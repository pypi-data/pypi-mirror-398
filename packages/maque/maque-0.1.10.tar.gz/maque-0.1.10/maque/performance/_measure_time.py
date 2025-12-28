import time
from rich.text import Text
from rich import print


class MeasureTime:
    def __init__(self, msg=None, prec=3, logger=None, logger_level="info", gpu=False):
        if gpu:
            import torch
            self.cuda_sync = torch.cuda.synchronize
        else:
            self.cuda_sync = None
        self._cost_time = 0.
        self._start_time = time.perf_counter()
        self._logger = logger
        self._logger_level = logger_level
        self._msg = msg
        self._prec: int = prec
        self._gpu = gpu

    def start(self, gpu=False):
        if gpu:
            self.cuda_sync()
        self._start_time = time.perf_counter()
        return self

    def show_interval(self, msg=None, gpu=False):
        if gpu:
            self.cuda_sync()
        self._cost_time = time.perf_counter() - self._start_time
        self._msg = msg
        cost = self.format_cost()
        self._show(cost)
        self._start_time = time.perf_counter()
        return self._cost_time

    def format_cost(self):
        return f"{self._cost_time:.{int(self._prec)}E}"

    def _show(self, cost_time: str):
        msg = f"{self._msg}\t" if self._msg else ''
        if self._logger:
            show_string = f"{msg}cost time: {cost_time}s"
            self._logger.log(self._logger_level, show_string)
        else:
            rgb_cost_time = Text(cost_time, style='green')
            rgb_msg = Text(f"{msg}", style="cyan")
            str_tuple = (rgb_msg, 'cost time: ', rgb_cost_time)
            print(*str_tuple, sep='')

    def __enter__(self):
        """进入上下文管理器，开始计时"""
        if self._gpu and self.cuda_sync:
            self.cuda_sync()
        self._start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器，显示执行时间"""
        if self._gpu and self.cuda_sync:
            self.cuda_sync()
        self._cost_time = time.perf_counter() - self._start_time
        cost = self.format_cost()
        self._show(cost)
        return False  # 不抑制异常

    @property
    def elapsed_time(self):
        """获取已消耗时间"""
        return self._cost_time
