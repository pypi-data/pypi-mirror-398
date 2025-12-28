import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from typing import List, Tuple, Optional
from enum import Enum
import time
import os

class Method(Enum):
    DIFFERENCE = "difference"
    SSIM = "ssim"
    HISTOGRAM = "histogram"
    MOTION_VECTOR = "motion_vector"  # 新增运动矢量方法

class AdvancedKeyframeExtractor:
    def __init__(self):
        self.reset()

    def reset(self):
        """重置提取器状态"""
        self.prev_frame = None
        self.prev_hist = None
        self.prev_gray = None  # 用于运动矢量计算
        self.keyframes = []
        self.frame_indices = []

    def downsample_frame(self,
                         frame: np.ndarray,
                         scale_factor: float = 0.5,
                         target_size: Optional[Tuple[int, int]] = None) -> np.ndarray:
        """对单帧进行降采样"""
        if target_size:
            return cv2.resize(frame, target_size, interpolation=cv2.INTER_AREA)

        width = int(frame.shape[1] * scale_factor)
        height = int(frame.shape[0] * scale_factor)
        return cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

    def compute_difference(self, current: np.ndarray, previous: np.ndarray) -> float:
        """计算帧差分"""
        diff = cv2.absdiff(current, previous)
        return np.mean(diff)

    def compute_ssim(self, current: np.ndarray, previous: np.ndarray) -> float:
        """计算SSIM"""
        return ssim(previous, current)

    def compute_histogram_similarity(self, current: np.ndarray, previous: np.ndarray) -> float:
        """计算直方图相似度"""
        # 计算HSV直方图
        current_hsv = cv2.cvtColor(current, cv2.COLOR_BGR2HSV)
        current_hist = cv2.calcHist([current_hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])
        cv2.normalize(current_hist, current_hist, 0, 1, cv2.NORM_MINMAX)

        if previous is None:
            return 0.0

        previous_hsv = cv2.cvtColor(previous, cv2.COLOR_BGR2HSV)
        previous_hist = cv2.calcHist([previous_hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])
        cv2.normalize(previous_hist, previous_hist, 0, 1, cv2.NORM_MINMAX)

        return cv2.compareHist(previous_hist, current_hist, cv2.HISTCMP_CORREL)

    def compute_motion_vectors(self, current_gray: np.ndarray, previous_gray: np.ndarray) -> Tuple[float, float]:
        """
        计算运动矢量

        Returns:
            mean_magnitude: 平均运动大小
            motion_ratio: 运动区域比例
        """
        # 计算光流
        flow = cv2.calcOpticalFlowFarneback(
            previous_gray,
            current_gray,
            None,
            pyr_scale=0.5,  # 金字塔缩放比例
            levels=3,       # 金字塔层数
            winsize=15,     # 窗口大小
            iterations=3,   # 迭代次数
            poly_n=5,      # 多项式展开阶数
            poly_sigma=1.2, # 高斯标准差
            flags=0
        )

        # 计算运动矢量大小
        magnitude, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])

        # 计算平均运动大小
        mean_magnitude = np.mean(magnitude)

        # 计算显著运动区域比例
        motion_threshold = np.mean(magnitude) + np.std(magnitude)
        motion_ratio = np.sum(magnitude > motion_threshold) / magnitude.size

        return mean_magnitude, motion_ratio

    def is_keyframe(self,
                    current_frame: np.ndarray,
                    method: Method,
                    threshold: float) -> bool:
        """
        判断是否为关键帧

        Args:
            current_frame: 当前帧
            method: 使用的方法
            threshold: 阈值

        Returns:
            是否为关键帧
        """
        if self.prev_frame is None:
            return True

        if method == Method.DIFFERENCE:
            diff = self.compute_difference(current_frame, self.prev_frame)
            return diff > threshold

        elif method == Method.SSIM:
            similarity = self.compute_ssim(current_frame, self.prev_frame)
            return similarity < threshold

        elif method == Method.HISTOGRAM:
            similarity = self.compute_histogram_similarity(current_frame, self.prev_frame)
            return similarity < threshold

        elif method == Method.MOTION_VECTOR:
            if self.prev_gray is None:
                return True

            # 转换为灰度图
            if len(current_frame.shape) == 3:
                current_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
            else:
                current_gray = current_frame

            # 计算运动矢量特征
            mean_magnitude, motion_ratio = self.compute_motion_vectors(current_gray, self.prev_gray)

            # 更新previous_gray
            self.prev_gray = current_gray.copy()

            # 基于运动大小和运动区域比例综合判断
            magnitude_threshold = threshold  # 例如 2.0
            ratio_threshold = threshold / 10  # 例如 0.2

            return (mean_magnitude > magnitude_threshold) or (motion_ratio > ratio_threshold)

        return False

    def extract_keyframes(self,
                          video_path: str,
                          method: Method = Method.DIFFERENCE,
                          threshold: float = 30.0,
                          sampling_rate: int = 5,
                          scale_factor: float = 0.5,
                          target_size: Optional[Tuple[int, int]] = None,
                          max_frames: Optional[int] = None,
                          start_time: Optional[float] = None,
                          end_time: Optional[float] = None
                          ) -> Tuple[List[np.ndarray], List[int]]:
        """
        提取关键帧

        Args:
            video_path: 视频文件路径
            method: 使用的方法
            threshold: 阈值:
                - difference: 30.0 (像素差异)
                - ssim: 0.7 (结构相似度)
                - histogram: 0.8 (直方图相关性)
                - motion_vector: 2.0 (运动矢量阈值)
            sampling_rate: 采样率 (每N帧处理一帧)
            scale_factor: 降采样比例
            target_size: 目标大小
            max_frames: 最大处理帧数
            start_time: 开始时间(秒)
            end_time: 结束时间(秒)

        Returns:
            keyframes: 关键帧列表
            frame_indices: 关键帧对应的原始帧序号
        """
        self.reset()
        cap = cv2.VideoCapture(video_path)

        # 获取视频信息
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        duration = total_frames / fps

        print("\n开始处理视频:")
        print(f"方法: {method.value}")
        print(f"总帧数: {total_frames}")
        print(f"FPS: {fps}")
        print(f"时长: {duration:.2f}秒")

        # 处理时间范围
        if start_time is not None:
            start_frame = int(start_time * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        else:
            start_frame = 0

        if end_time is not None:
            end_frame = int(end_time * fps)
        else:
            end_frame = total_frames

        if max_frames:
            end_frame = min(end_frame, start_frame + max_frames)

        frame_count = start_frame
        processed_count = 0
        start_time = time.time()

        while frame_count < end_frame:
            ret, frame = cap.read()
            if not ret:
                break

            # 跳帧采样
            if (frame_count - start_frame) % sampling_rate != 0:
                frame_count += 1
                continue

            # 降采样
            small_frame = self.downsample_frame(frame, scale_factor, target_size)

            # 判断是否为关键帧
            if method == Method.DIFFERENCE:
                gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
                is_key = self.is_keyframe(gray, method, threshold)
                if is_key:
                    self.prev_frame = gray
            elif method == Method.MOTION_VECTOR:
                gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
                is_key = self.is_keyframe(gray, method, threshold)
                # prev_gray的更新已经在is_keyframe中处理
            else:
                is_key = self.is_keyframe(small_frame, method, threshold)
                if is_key:
                    self.prev_frame = small_frame

            if is_key:
                self.keyframes.append(frame)  # 保存原始分辨率帧
                self.frame_indices.append(frame_count)

            processed_count += 1
            frame_count += 1

            # 打印进度
            if processed_count % 100 == 0:
                elapsed_time = time.time() - start_time
                fps = processed_count / elapsed_time
                progress = ((frame_count - start_frame) / (end_frame - start_frame)) * 100
                print(f"处理进度: {progress:.1f}% ({frame_count}/{end_frame}) "
                      f"处理速度: {fps:.1f} fps")

        cap.release()

        print("\n处理完成:")
        print(f"总耗时: {time.time() - start_time:.2f}秒")
        print(f"提取关键帧数: {len(self.keyframes)}")
        print(f"平均提取比例: {len(self.keyframes)/processed_count*100:.1f}%")

        return self.keyframes, self.frame_indices

    def save_keyframes(self,
                       output_dir: str,
                       prefix: str = "keyframe",
                       ext: str = ".jpg",
                       jpg_quality: int = 95):
        """保存关键帧到指定目录"""
        os.makedirs(output_dir, exist_ok=True)

        for i, frame in enumerate(self.keyframes):
            frame_idx = self.frame_indices[i]
            filename = f"{prefix}_{frame_idx:06d}{ext}"
            filepath = os.path.join(output_dir, filename)

            if ext.lower() == '.jpg':
                cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, jpg_quality])
            else:
                cv2.imwrite(filepath, frame)

        print(f"保存了 {len(self.keyframes)} 张关键帧到 {output_dir}")

    def process_video(self,
                      video_path: str,
                      output_dir: str,
                      methods: List[Method],
                      **kwargs):
        """
        使用多种方法处理同一个视频

        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            methods: 要使用的方法列表
            **kwargs: 其他参数传递给extract_keyframes
        """
        for method in methods:
            print(f"\n使用 {method.value} 方法处理...")

            # 为每种方法创建子目录
            method_dir = os.path.join(output_dir, method.value)

            # 设置合适的阈值
            if method == Method.DIFFERENCE:
                threshold = kwargs.get('threshold', 30.0)
            elif method == Method.SSIM:
                threshold = kwargs.get('threshold', 0.7)
            elif method == Method.MOTION_VECTOR:
                threshold = kwargs.get('threshold', 2.0)
            else:  # HISTOGRAM
                threshold = kwargs.get('threshold', 0.8)

            # 提取关键帧
            self.extract_keyframes(
                video_path=video_path,
                method=method,
                threshold=threshold,
                **kwargs
            )

            # 保存关键帧
            self.save_keyframes(
                output_dir=method_dir,
                prefix=f"{method.value}_frame"
            )


if __name__ == "__main__":
    extractor = AdvancedKeyframeExtractor()
    video_path = "./test.mp4"

    # 示例1: 使用单一方法
    keyframes, indices = extractor.extract_keyframes(
        video_path=video_path,
        method=Method.DIFFERENCE,
        threshold=30.0,
        sampling_rate=5,
        scale_factor=0.5
    )
    extractor.save_keyframes("output/difference_keyframes")

    # 示例2: 使用所有方法处理视频
    extractor.process_video(
        video_path=video_path,
        output_dir="output/comparison",
        methods=[Method.DIFFERENCE, Method.SSIM, Method.HISTOGRAM],
        sampling_rate=3,
        scale_factor=0.5,
        max_frames=5000  # 只处理前5000帧
    )

    # 示例3: 处理视频片段
    keyframes, indices = extractor.extract_keyframes(
        video_path=video_path,
        method=Method.SSIM,
        threshold=0.7,
        sampling_rate=2,
        target_size=(320, 240),
        start_time=60,  # 从第60秒开始
        end_time=120  # 处理到第120秒
    )