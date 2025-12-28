import cv2
import numpy as np
from PIL import Image
import base64
import io
from dataclasses import dataclass
from typing import List, Union, Optional, Literal

ReturnFormat = Literal['pil', 'numpy', 'base64']

@dataclass
class FrameExtractionResult:
    width: int
    height: int
    total_frames: int
    original_fps: float
    extracted_frames: List[Union[Image.Image, np.ndarray, str]]  # str for base64
    start_time: float
    end_time: float
    extraction_fps: Optional[float] = None
    format: ReturnFormat = 'pil'


class VideoFrameExtractor:
    def __init__(self, video_path: str):
        """初始化视频帧提取器

        Args:
            video_path (str): 视频文件路径
        """
        self.video_path = video_path
        self._video = None
        self._init_video_capture()

    def _init_video_capture(self):
        """初始化视频捕获对象"""
        self._video = cv2.VideoCapture(self.video_path)
        if not self._video.isOpened():
            raise ValueError(f"无法打开视频文件: {self.video_path}")
        
        self.video_fps = self._video.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self._video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self._video.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self._video.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def extract_frames(
        self,
        start_time: float,
        end_time: float = -1,
        fps: Optional[float] = None,
        n_frames: Optional[int] = None,
        return_format: ReturnFormat = 'pil',
        max_width: Optional[int] = None,
        max_height: Optional[int] = None
    ) -> FrameExtractionResult:
        """提取视频帧

        Args:
            start_time (float): 开始时间（秒）
            end_time (float): 结束时间（秒），-1表示到视频结束
            fps (float, optional): 目标帧率
            n_frames (int, optional): 需要提取的帧数
            return_format (str): 返回格式，支持 'pil'、'numpy' 或 'base64'
            max_width (int, optional): 最大宽度，保持宽高比缩放
            max_height (int, optional): 最大高度，保持宽高比缩放

        Returns:
            FrameExtractionResult: 包含提取结果的数据类
        """
        # 计算开始和结束帧
        start_frame = int(start_time * self.video_fps)
        if end_time == -1:
            end_frame = self.total_frames
            end_time = self.total_frames / self.video_fps
        else:
            end_frame = int(end_time * self.video_fps)

        # 计算需要提取的帧数
        if fps:
            n_frames = int((end_time - start_time) * fps)
        else:
            fps = self.video_fps
            if n_frames is None:
                raise ValueError("fps和n_frames不能同时为None")
        
        if n_frames <= 0:
            raise ValueError("n_frames必须大于0")

        # 计算采样步长
        step = (end_frame - start_frame) / n_frames

        # 计算目标尺寸
        target_width = self.width
        target_height = self.height
        if max_width or max_height:
            scale_w = max_width / self.width if max_width else float('inf')
            scale_h = max_height / self.height if max_height else float('inf')
            scale = min(scale_w, scale_h, 1.0)  # 确保不会放大
            target_width = int(self.width * scale)
            target_height = int(self.height * scale)

        # 提取帧
        extracted_frames = []
        for i in np.arange(start_frame, end_frame, step):
            self._video.set(cv2.CAP_PROP_POS_FRAMES, int(i))
            ret, frame = self._video.read()
            if ret:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # 如果需要调整大小
                if target_width != self.width or target_height != self.height:
                    rgb_frame = cv2.resize(rgb_frame, (target_width, target_height), 
                                         interpolation=cv2.INTER_AREA)

                if return_format == 'pil':
                    frame_data = Image.fromarray(rgb_frame)
                elif return_format == 'numpy':
                    frame_data = rgb_frame
                elif return_format == 'base64':  # base64
                    pil_image = Image.fromarray(rgb_frame)
                    buffer = io.BytesIO()
                    pil_image.save(buffer, format='PNG')
                    frame_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                else:
                    raise TypeError(f"不支持的返回格式: {return_format}")
                extracted_frames.append(frame_data)
            else:
                break

        return FrameExtractionResult(
            width=target_width,
            height=target_height,
            total_frames=self.total_frames,
            original_fps=self.video_fps,
            extracted_frames=extracted_frames,
            start_time=start_time,
            end_time=end_time,
            extraction_fps=fps,
            format=return_format
        )

    def frames_to_video(
        self,
        frames_result: FrameExtractionResult,
        output_path: str,
        fps: Optional[float] = None,
        codec: str = 'mp4v'
    ) -> None:
        """将提取的帧重新组装为视频

        Args:
            frames_result (FrameExtractionResult): 帧提取结果
            output_path (str): 输出视频的路径
            fps (float, optional): 输出视频的帧率，默认使用提取时的帧率
            codec (str, optional): 视频编码器，默认为'mp4v'
        """
        if not frames_result.extracted_frames:
            raise ValueError("没有可用的帧进行视频合成")

        # 使用提取时的帧率或指定的帧率
        output_fps = fps if fps is not None else (
            frames_result.extraction_fps if frames_result.extraction_fps
            else frames_result.original_fps
        )

        # 创建VideoWriter对象
        fourcc = cv2.VideoWriter_fourcc(*codec)
        out = cv2.VideoWriter(
            output_path,
            fourcc,
            output_fps,
            (frames_result.width, frames_result.height)
        )

        try:
            for frame in frames_result.extracted_frames:
                # 根据不同的格式转换为OpenCV可用的格式
                if frames_result.format == 'pil':
                    cv_frame = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
                elif frames_result.format == 'numpy':
                    cv_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                elif frames_result.format == 'base64':
                    # 解码base64字符串
                    img_data = base64.b64decode(frame)
                    nparr = np.frombuffer(img_data, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    cv_frame = img
                else:
                    raise ValueError(f"不支持的帧格式: {frames_result.format}")

                out.write(cv_frame)
        finally:
            out.release()

    def __del__(self):
        """析构函数，确保视频资源被释放"""
        if self._video is not None:
            self._video.release()


if __name__ == "__main__":
    extractor = VideoFrameExtractor('input.mp4')

    # 限制最大宽度为 1280，高度会按比例缩放
    frames = extractor.extract_frames(
        start_time=0,
        end_time=10,
        fps=30,
        max_width=1280
    )

    # 同时限制最大宽度和高度，会按照最小缩放比例进行缩放
    frames = extractor.extract_frames(
        start_time=0,
        end_time=10,
        fps=30,
        max_width=1280,
        max_height=720
    )