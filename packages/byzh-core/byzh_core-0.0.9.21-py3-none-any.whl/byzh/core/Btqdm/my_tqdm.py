import sys
import time
import threading
from typing import Iterable, Literal

from ..Butils import B_Color, B_Appearance, B_Background


class B_Tqdm:
    def __init__(
            self,
            range: int|Iterable = None,
            type: None|Literal['MB', 'KB'] = None,
            prefix: str = 'Processing',
            suffix: str = '',
            length: int = 20,
            fill: str = '█',
    ):
        """
        类似tqdm的进度条
        :param total: 总数
        :param prefix: 前缀
        :param suffix: 后缀
        :param length: 进度条长度(字符), 默认为20个字符长度
        :param fill: 填充字符
        """
        super().__init__()
        self.range = range
        if isinstance(range, (int, float, str)):
            self.range_len = int(range)
        elif isinstance(range, Iterable):
            self.range_len = len(range)
        else:
            self.range_len = float('inf')

        self.type = type
        self.prefix = prefix
        self.suffix = suffix
        self.length = length
        self.fill = fill
        self.start_time = 0
        self.current = 0

        self._lock = threading.Lock()

    def _format_time(self, seconds):
        """将秒数转换为mm:ss格式"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f'{minutes:02}:{seconds:02}'

    def update(self, step=1, prefix=None, suffix=None, color:B_Color=B_Color.BLUE, appearance:B_Appearance=None, background:B_Background=None):
        with self._lock:
            pre_show = color.value
            if appearance is not None:
                pre_show += appearance.value
            if background is not None:
                pre_show += background.value

            if self.current == 0:
                self.start_time = time.time()
            if prefix is not None:
                self.prefix = prefix
            if suffix is not None:
                self.suffix = suffix

            # 更新进度
            self.current += step

            # 计算已用时间
            elapsed_time = time.time() - self.start_time
            used_time = self._format_time(elapsed_time)
            # 预估剩余时间
            if self.range_len != float('inf'):
                estimated_time = elapsed_time / self.current * (self.range_len - self.current) if self.current > 0 else 0
                rest_time = self._format_time(estimated_time)
            else:
                rest_time = None
            # 计算每秒处理的项数
            speed = self.current / elapsed_time if elapsed_time > 0 else 0

            # 更新进度条
            self._update(pre_show, self.current, self.range_len, used_time, rest_time, speed)

            # 进度条结束后换行
            if self.current >= self.range_len:
                sys.stdout.write('\n')
                sys.stdout.flush()

    def _update(self, pre_show, current, total, used_time, rest_time, speed):
        filled_length = int(self.length * current // total)
        bar = self.fill * filled_length + '-' * (self.length - filled_length) * len(self.fill)

        match self.type:
            case 'MB':
                style = 'MB'
                current = current / 1024**2
                total = total / 1024**2
                speed = speed / 1024**2
            case 'KB':
                style = 'KB'
                current = current / 1024
                total = total / 1024
                speed = speed / 1024
            case _:
                style = 'it'
                current = current
                total = total
                speed = speed
        if total != float('inf'):
            sys.stdout.write(f'\r{pre_show}{self.prefix} |{bar}|'
                             f' {current:.3g}/{total:.3g} {style} -> {used_time}<{rest_time} | {speed:.1f} {style}/s |'
                             f' {self.suffix}{B_Color.RESET.value}')
        else:
            sys.stdout.write(f'\r{pre_show}{self.prefix} | {current:.3g} {style} -> {used_time} | {speed:.1f} {style}/s |'
                             f' {self.suffix}{B_Color.RESET.value}')
        sys.stdout.flush()

    def __iter__(self):
        for item in self.range:
            yield item
            self.update()
