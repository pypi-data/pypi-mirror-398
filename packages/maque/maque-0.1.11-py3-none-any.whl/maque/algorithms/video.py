from __future__ import annotations
"""video_frame_deduplicator.py  –  lightweight, **multiprocess‑capable** duplicate‑frame detector

*   Works for **video files** *and* in‑memory **image lists**.
*   Pure‑Python / NumPy / OpenCV; Pillow optional (for PIL.Image input).
*   Optional **multi‑processing** (set *workers>1*) accelerates perceptual‑hash
    computation on multi‑core CPUs.

CLI examples
------------
»   Extract unique frames (single‑process):
    ```bash
    python video_frame_deduplicator.py input.mp4
    ```
»   Same but with 8 worker processes:
    ```bash
    python video_frame_deduplicator.py input.mp4 phash 8
    ```
"""

import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple, Union

import cv2
import numpy as np

try:
    from PIL import Image  # type: ignore

    _HAS_PIL = True
except ImportError:  # Pillow is optional
    _HAS_PIL = False

################################################################################
#  NumPy fallbacks for pHash / dHash / aHash  +  Hamming distance helper
################################################################################

def _phash_numpy(img: np.ndarray, hash_size: int = 8) -> int:
    gray = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (32, 32), interpolation=cv2.INTER_AREA)
    dct = cv2.dct(np.float32(gray))
    low = dct[:hash_size, :hash_size]
    # med = np.median(low)
    med = np.mean(low)
    bits = (low > med).flatten()
    return int("".join("1" if b else "0" for b in bits), 2)


def _ahash_numpy(img: np.ndarray, hash_size: int = 8) -> int:
    gray = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (hash_size, hash_size), interpolation=cv2.INTER_AREA)
    med = gray.mean()
    bits = (gray > med).flatten()
    return int("".join("1" if b else "0" for b in bits), 2)


def _dhash_numpy(img: np.ndarray, hash_size: int = 8) -> int:
    gray = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (hash_size + 1, hash_size), interpolation=cv2.INTER_AREA)
    diff = gray[:, 1:] > gray[:, :-1]
    return int("".join("1" if b else "0" for b in diff.flatten()), 2)


def _hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


################################################################################
#  Multiprocessing worker (must be top‑level so it can be pickled)
################################################################################

def _sig_worker(args):
    """Compute signature in a subprocess. Arguments are packed to avoid global state."""
    idx, img_bgr, method, resize = args

    # resize (kept identical to main‑process logic)
    if resize:
        h, w = img_bgr.shape[:2]
        scale = resize / w
        img_bgr = cv2.resize(img_bgr, (resize, int(h * scale)), interpolation=cv2.INTER_AREA)

    if method == "phash":
        sig = _phash_numpy(img_bgr)
    elif method == "dhash":
        sig = _dhash_numpy(img_bgr)
    elif method == "ahash":
        sig = _ahash_numpy(img_bgr)
    else:
        raise RuntimeError("_sig_worker only supports hash methods (phash/dhash/ahash)")
    # return idx to restore original order
    return idx, sig


################################################################################
#  Main class
################################################################################
class VideoFrameDeduplicator:
    """Duplicate detector with optional multi‑processing.

    Parameters
    ----------
    method     : {"phash", "dhash", "ahash", "hist", "mse", "ssim"}
    threshold  : float | None.  If None, uses method‑specific default.
    step       : int ≥1.  Sample every *step* frames/images.
    resize     : int.  Pre‑resize width (keep aspect). 0 disables.
    workers    : int ≥1.  1 → single‑process (default).  >1 → mp.
                  *Currently mp acceleration applies to hash methods only.*
    fps        : float | None.  Frames per second. 0 disables.
    """

    _DEFAULTS = {
        "phash": 5,
        "dhash": 5,
        "ahash": 5,
        "hist": 0.95,  # correlation ≥ 0.95 → duplicate
        "mse": 4.0,    # mse ≤ 4 → duplicate
        "ssim": 0.98,  # ssim ≥ 0.98 → duplicate
    }

    ###########################################################################
    #  Init & helpers
    ###########################################################################

    def __init__(
        self,
        method: str = "phash",
        threshold: Optional[float] = None,
        step: int = 1,
        resize: int = 256,
        workers: int = 1,
        fps: Optional[float] = None,
    ) -> None:
        self.method = method.lower()
        if self.method not in self._DEFAULTS:
            raise ValueError(f"Unsupported method '{self.method}'.")

        # Validate step and fps: only one can be set (unless step is default 1)
        if step != 1 and fps is not None:
            raise ValueError("Cannot specify both 'step' (other than 1) and 'fps'.")

        self.thr = threshold if threshold is not None else self._DEFAULTS[self.method]
        self.step = max(1, step)
        self.resize = resize
        self.workers = max(1, workers)
        self.fps = fps

        # Prefer OpenCV's img_hash where available (single‑process only!)
        self._use_cv_hash = False
        if self.method in ("phash", "dhash", "ahash") and self.workers == 1:
            try:
                alg_map = {
                    "phash": cv2.img_hash.PHash_create,
                    "dhash": cv2.img_hash.BlockMeanHash_create,  # mode=1 (dHash‑like)
                    "ahash": cv2.img_hash.AverageHash_create,
                }
                self._hash_alg = alg_map[self.method]()
                self._use_cv_hash = True
            except Exception:
                pass  # contrib not available → fall back to NumPy routines

        self._prev_sig = None  # reset by each public API

    # ------------------------------ utils -----------------------------------
    def _to_bgr(self, img: Union[np.ndarray, "Image.Image"]) -> np.ndarray:
        if _HAS_PIL and isinstance(img, Image.Image):
            img = np.asarray(img.convert("RGB"))[:, :, ::-1]  # PIL RGB → BGR
        elif not isinstance(img, np.ndarray):
            raise TypeError("Input must be np.ndarray or PIL.Image")
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        return img

    # --------------------------- signature & distance ------------------------
    def _signature(self, frame: np.ndarray):
        if self.method in ("phash", "dhash", "ahash"):
            if self._use_cv_hash:
                return self._hash_alg.compute(frame)
            # workers==1 but contrib missing ➜ NumPy fallback
            if self.method == "phash":
                return _phash_numpy(frame)
            if self.method == "dhash":
                return _dhash_numpy(frame)
            return _ahash_numpy(frame)
        elif self.method == "hist":
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
            return cv2.normalize(hist, hist).flatten()
        elif self.method in ("mse", "ssim"):
            return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            raise RuntimeError

    def _distance(self, sig1, sig2) -> float:
        if self.method in ("phash", "dhash", "ahash"):
            if self._use_cv_hash:
                return cv2.norm(sig1, sig2, cv2.NORM_HAMMING)
            return _hamming(sig1, sig2)
        elif self.method == "hist":
            return cv2.compareHist(sig1.astype(np.float32), sig2.astype(np.float32), cv2.HISTCMP_CORREL)
        elif self.method == "mse":
            diff = sig1.astype(np.int16) - sig2.astype(np.int16)
            return float(np.mean(diff * diff))
        elif self.method == "ssim":
            C1, C2 = 6.5025, 58.5225
            mu1 = cv2.GaussianBlur(sig1, (11, 11), 1.5)
            mu2 = cv2.GaussianBlur(sig2, (11, 11), 1.5)
            mu1_sq, mu2_sq, mu1_mu2 = mu1 ** 2, mu2 ** 2, mu1 * mu2
            sigma1_sq = cv2.GaussianBlur(sig1 ** 2, (11, 11), 1.5) - mu1_sq
            sigma2_sq = cv2.GaussianBlur(sig2 ** 2, (11, 11), 1.5) - mu2_sq
            sigma12 = cv2.GaussianBlur(sig1 * sig2, (11, 11), 1.5) - mu1_mu2
            ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / (
                (mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2)
            )
            return float(ssim_map.mean())
        else:
            raise RuntimeError

    def _is_duplicate(self, dist: float) -> bool:
        # hist & ssim: higher similarity → duplicate
        if self.method in ("hist", "ssim"):
            return dist >= self.thr
        return dist <= self.thr  # hashes and mse: lower distance → duplicate

    # --------------------------- keep‑decision ------------------------------
    def _keep(self, sig) -> bool:
        if self._prev_sig is None:
            self._prev_sig = sig
            return True
        dist = self._distance(sig, self._prev_sig)
        if not self._is_duplicate(dist):
            self._prev_sig = sig
            return True
        return False

    ###########################################################################
    #  Public API: video ------------------------------------------------------
    ###########################################################################
    def unique_frames(self, src: Union[str, Path, int]) -> Iterable[Tuple[int, np.ndarray]]:
        """Yield unique video frames (index, BGR ndarray).  Uses mp if workers>1 & hash methods."""
        cap = cv2.VideoCapture(str(src))
        if not cap.isOpened():
            raise FileNotFoundError(f"Cannot open video {src}")
        
        # Determine effective step based on fps or step
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        effective_step = self.step
        if self.fps is not None:
            if video_fps and video_fps > 0:
                effective_step = max(1, round(video_fps / self.fps))
            else:
                # Warn if FPS is unavailable and fps parameter is set
                import sys
                print(f"Warning: Could not determine FPS for video '{src}'. Ignoring 'fps' parameter.", file=sys.stderr)
                effective_step = 1 # Default to processing every frame if FPS unknown
        elif self.step == 1:
             # Default case: if neither fps nor step>1 is specified, process every frame
             effective_step = 1

        self._prev_sig = None
        idx = -1

        if self.workers == 1 or self.method not in ("phash", "dhash", "ahash"):
            # ---------------- single‑process path ----------------
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                idx += 1
                if idx % effective_step: # Use effective_step
                    continue

                # resize beforehand (single‑process path)
                if self.resize:
                    h, w = frame.shape[:2]
                    scale = self.resize / w
                    frame_proc = cv2.resize(frame, (self.resize, int(h * scale)), interpolation=cv2.INTER_AREA)
                else:
                    frame_proc = frame

                sig = self._signature(frame_proc)
                if self._keep(sig):
                    yield idx, frame
        else:
            # ---------------- multi‑process path -----------------
            # collect candidate frames first (step filtering) to minimise IPC
            frames: List[Tuple[int, np.ndarray]] = []
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                idx += 1
                if idx % effective_step == 0: # Use effective_step
                    frames.append((idx, frame))
            cap.release()

            # compute signatures in parallel using fallbacks (cv2.img_hash not picklable)
            with ProcessPoolExecutor(max_workers=self.workers) as pool:
                sigs = list(
                    pool.map(
                        _sig_worker,
                        [
                            (i, f, self.method, self.resize)
                            for i, f in frames
                        ],
                    )
                )

            # merge idx→sig dict for ordered pass
            sig_dict = {i: s for i, s in sigs}
            for i, frame in frames:
                if self._keep(sig_dict[i]):
                    yield i, frame
            return  # explicit

    ###########################################################################
    #  Public API: images -----------------------------------------------------
    ###########################################################################
    def iter_unique_images(
        self, images: Sequence[Union[np.ndarray, "Image.Image"]]
    ) -> Iterable[Tuple[int, np.ndarray]]:
        """Generator.  mp acceleration when workers>1 & hash methods."""
        # Check if fps is set, which is invalid for image sequences
        if self.fps is not None:
            raise ValueError("'fps' parameter is not applicable to image sequences.")
        
        self._prev_sig = None

        # ------------ single‑process or non‑hash path -------------
        if self.workers == 1 or self.method not in ("phash", "dhash", "ahash"):
            for idx, img in enumerate(images):
                if idx % self.step:
                    continue
                bgr = self._to_bgr(img)

                # resize
                if self.resize:
                    h, w = bgr.shape[:2]
                    scale = self.resize / w
                    bgr_proc = cv2.resize(bgr, (self.resize, int(h * scale)), interpolation=cv2.INTER_AREA)
                else:
                    bgr_proc = bgr

                sig = self._signature(bgr_proc)
                if self._keep(sig):
                    yield idx, bgr
            return

        # ------------ multi‑process hash path -------------
        # Pre‑convert images to BGR ndarrays in main process (more stable than PIL inside pool)
        candidates: List[Tuple[int, np.ndarray]] = []
        for idx, img in enumerate(images):
            if idx % self.step == 0:
                candidates.append((idx, self._to_bgr(img)))

        with ProcessPoolExecutor(max_workers=self.workers) as pool:
            sigs = list(
                pool.map(
                    _sig_worker,
                    [
                        (idx, img, self.method, self.resize) for idx, img in candidates
                    ],
                )
            )
        sig_dict = {i: s for i, s in sigs}

        for idx, bgr in candidates:
            if self._keep(sig_dict[idx]):
                yield idx, bgr

    def unique_images(
        self,
        images: Sequence[Union[np.ndarray, "Image.Image"]],
        return_indices: bool = False,
    ) -> List[Union[np.ndarray, Tuple[int, np.ndarray]]]:
        uniques: List[Union[np.ndarray, Tuple[int, np.ndarray]]] = []
        for idx, img in self.iter_unique_images(images):
            uniques.append((idx, img) if return_indices else img)
        return uniques

    ###########################################################################
    #  Public API: Process and Save ------------------------------------------
    ###########################################################################
    def process_and_save_unique_frames(self, src: Union[str, Path, int], out_dir: Union[str, Path]) -> int:
        """Process video/images, find unique frames, and save them to out_dir.

        Args:
            src (str | Path | int): Path to video file, device index, or sequence of images.
            out_dir (str | Path): Directory to save unique frames.

        Returns:
            int: Number of unique frames saved.
        """
        # Create base output directory
        output_path = Path(out_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Extract filename from source (if src is a path)
        if isinstance(src, (str, Path)) and not isinstance(src, int):
            src_path = Path(src)
            if src_path.exists() and src_path.is_file():
                # Use filename without extension as subdirectory
                filename_no_ext = src_path.stem
                # Create subdirectory with input filename
                output_path = output_path / filename_no_ext
                output_path.mkdir(parents=True, exist_ok=True)

        print(f"Processing '{src}' with method='{self.method}', threshold={self.thr}, "
              f"step={self.step if self.fps is None else 'N/A'}, fps={self.fps if self.fps is not None else 'N/A'}, "
              f"resize={self.resize}, workers={self.workers}...")
        print(f"Saving unique frames to '{output_path}'...")

        count = 0
        try:
            # Check if src is an image sequence or video path/index
            if isinstance(src, (list, tuple)):
                 # Assuming src is a sequence of images (np.ndarray or PIL.Image)
                 # Note: This part currently assumes unique_frames handles image sequences correctly
                 # If only video sources are intended for this method, add a check here.
                 iterator = self.iter_unique_images(src)
            else:
                 # Assuming src is a video file path or device index
                 iterator = self.unique_frames(src)

            for idx, frame in iterator:
                frame_filename = output_path / f"{idx:06d}.jpg"
                cv2.imwrite(str(frame_filename), frame)
                count += 1
        except FileNotFoundError as e:
            print(f"Error: Input source '{src}' not found or could not be opened. {e}")
            # Re-raise or handle as needed
            raise
        except Exception as e:
            print(f"An error occurred during processing or saving: {e}")
            # Re-raise or handle as needed
            raise

        print(f"Successfully saved {count} unique frames to ./{output_path}/")
        return count

    def frames_to_video(self, frames_dir: Union[str, Path], output_video: Union[str, Path] = None, fps: float = 15.0, codec: str = 'mp4v', use_av: bool = False) -> str:
        """
        将一个目录中的帧图像合成为视频。
        
        Args:
            frames_dir (str | Path): 包含帧图像的目录路径。
            output_video (str | Path, optional): 输出视频的路径。如果为None，则默认为frames_dir旁边的同名mp4文件。
            fps (float, optional): 输出视频的帧率。默认为15.0。
            codec (str, optional): 视频编解码器。默认为'mp4v'，可选'avc1'等。
            use_av (bool, optional): 是否使用PyAV库加速（如果可用）。默认为False。
            
        Returns:
            str: 输出视频的路径。
        """
        frames_dir = Path(frames_dir)
        if not frames_dir.exists() or not frames_dir.is_dir():
            raise ValueError(f"帧目录'{frames_dir}'不存在或不是一个目录。")
        
        # 确定输出视频路径
        if output_video is None:
            output_video = str(frames_dir.parent / f"{frames_dir.name}.mp4")
        else:
            output_video = str(output_video)
        
        # 获取帧图像文件列表并排序
        frame_files = sorted([f for f in frames_dir.glob("*.jpg") or frames_dir.glob("*.png") or frames_dir.glob("*.jpeg")])
        if not frame_files:
            raise ValueError(f"在目录'{frames_dir}'中未找到图像文件。")
        
        # 读取第一帧以获取宽度和高度
        first_frame = cv2.imread(str(frame_files[0]))
        if first_frame is None:
            raise ValueError(f"无法读取图像文件'{frame_files[0]}'。")
        
        height, width = first_frame.shape[:2]
        
        # 尝试使用PyAV加速（如果请求并可用）
        if use_av:
            try:
                import av
                import numpy as np
                print(f"使用PyAV库合成视频...")
                
                # 将OpenCV编解码器转换为PyAV编解码器
                av_codec = codec
                if codec == 'mp4v':
                    av_codec = 'libx264'  # 对于mp4v，使用libx264
                elif codec == 'avc1':
                    av_codec = 'libx264'  # avc1同样使用libx264
                
                try:
                    container = av.open(output_video, mode='w')
                    stream = container.add_stream(av_codec, rate=fps)
                    stream.width = width
                    stream.height = height
                    stream.pix_fmt = 'yuv420p'
                    
                    for frame_file in frame_files:
                        img = cv2.imread(str(frame_file))
                        # OpenCV使用BGR，转换为RGB
                        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        frame = av.VideoFrame.from_ndarray(img_rgb, format='rgb24')
                        packet = stream.encode(frame)
                        container.mux(packet)
                    
                    # 刷新缓冲区
                    packet = stream.encode(None)
                    container.mux(packet)
                    container.close()
                    
                    print(f"视频合成完成，输出到: {output_video}")
                    return output_video
                except Exception as e:
                    print(f"PyAV编解码器错误: {e}")
                    print("尝试使用默认编解码器...")
                    
                    # 如果特定编解码器失败，尝试使用默认编解码器
                    container = av.open(output_video, mode='w')
                    stream = container.add_stream('libx264', rate=fps)
                    stream.width = width
                    stream.height = height
                    stream.pix_fmt = 'yuv420p'
                    
                    for frame_file in frame_files:
                        img = cv2.imread(str(frame_file))
                        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        frame = av.VideoFrame.from_ndarray(img_rgb, format='rgb24')
                        packet = stream.encode(frame)
                        container.mux(packet)
                    
                    packet = stream.encode(None)
                    container.mux(packet)
                    container.close()
                    
                    print(f"视频合成完成，输出到: {output_video}")
                    return output_video
                    
            except (ImportError, Exception) as e:
                print(f"PyAV库不可用或发生错误: {e}")
                print("回退到OpenCV进行视频合成...")
        
        # 使用OpenCV合成视频（默认）
        print(f"使用OpenCV合成视频...")
        fourcc = cv2.VideoWriter_fourcc(*codec)
        out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
        
        if not out.isOpened():
            print(f"警告: 无法使用编解码器'{codec}'创建视频，尝试使用默认编解码器...")
            # 尝试使用默认编解码器
            default_codec = 'mp4v'
            fourcc = cv2.VideoWriter_fourcc(*default_codec)
            out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
            
            if not out.isOpened():
                raise RuntimeError(f"无法创建视频写入器，请检查编解码器是否支持。")
        
        for frame_file in frame_files:
            img = cv2.imread(str(frame_file))
            if img is not None:
                out.write(img)
            else:
                print(f"警告: 无法读取图像文件'{frame_file}'，跳过。")
        
        out.release()
        print(f"视频合成完成，输出到: {output_video}")
        return output_video


################################################################################
#  Simple CLI helper
################################################################################
if __name__ == "__main__":
    import sys
    from maque.performance._measure_time import MeasureTime

    if len(sys.argv) < 2:
        print("请使用 maque CLI 来使用此功能。例如：")
        print("python -m maque video_frame_dedup <video_file> [--fps 1] [--method phash] [--workers 4]")
        print("python -m maque frames_to_video <frames_dir> [--fps 30] [--use-av]")
        print("python -m maque dedup_and_create_video <video_file> [--fps 1] [--video-fps 30]")
        sys.exit(0)

    print("请使用 maque CLI 来使用此功能：")
    print("1. 提取帧: python -m maque video_frame_dedup <video_file>")
    print("2. 合成视频: python -m maque frames_to_video <frames_dir>")
    print("3. 一体化流程: python -m maque dedup_and_create_video <video_file>")
    sys.exit(0)
