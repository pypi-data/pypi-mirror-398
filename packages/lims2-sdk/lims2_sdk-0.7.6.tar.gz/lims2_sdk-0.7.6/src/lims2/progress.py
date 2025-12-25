"""进度显示工具

提供简洁的进度条显示和整体执行进度管理
"""

import sys
import time
from typing import Any, Callable, Optional, TextIO

from .utils import format_file_size


class ProgressBar:
    """统一的进度条显示"""

    def __init__(
        self, name: str = "上传", bar_width: int = 40, file: Optional[TextIO] = None
    ):
        self.name = name
        self.bar_width = bar_width
        self.file = file or sys.stderr
        self.start_time = time.time()
        self.last_update = 0

    def update(self, consumed: int, total: int):
        """更新进度条"""
        now = time.time()
        # 限制更新频率，避免闪烁
        if now - self.last_update < 0.1 and consumed < total:
            return

        percentage = min(100, (consumed / total) * 100) if total > 0 else 0
        filled = int(self.bar_width * consumed / total) if total > 0 else 0
        bar = "█" * filled + "░" * (self.bar_width - filled)

        # 计算速度
        elapsed = now - self.start_time
        speed_text = ""
        if elapsed > 0 and consumed > 0:
            speed = consumed / elapsed
            speed_text = f" {format_file_size(int(speed))}/s"

        print(
            f"\r{self.name}: [{bar}] {percentage:.1f}% "
            f"{format_file_size(consumed)}/{format_file_size(total)}"
            f"{speed_text}",
            end="",
            file=self.file,
        )
        self.last_update = now

        if consumed >= total:
            print(file=self.file)  # 完成时换行


class OverallProgress:
    """整体执行进度管理，避免0到100的跳跃"""

    def __init__(self, name: str = "执行进度", file: Optional[TextIO] = None):
        self.name = name
        self.file = file or sys.stderr
        self.phases = []  # 阶段列表: [(name, weight), ...]
        self.current_phase = 0
        self.phase_progress = 0
        self.progress_bar = None

    def add_phase(self, name: str, weight: int = 1):
        """添加执行阶段"""
        self.phases.append((name, weight))

    def start_phase(self, phase_index: int):
        """开始某个阶段"""
        if 0 <= phase_index < len(self.phases):
            self.current_phase = phase_index
            self.phase_progress = 0
            if self.progress_bar is None:
                sum(weight for _, weight in self.phases)
                self.progress_bar = ProgressBar(self.name, file=self.file)

    def update_phase_progress(self, progress: float):
        """更新当前阶段的进度 (0-1)"""
        self.phase_progress = min(1.0, max(0.0, progress))
        self._update_overall()

    def _update_overall(self):
        """更新整体进度"""
        if not self.phases or self.progress_bar is None:
            return

        total_progress = 0
        total_weight = sum(weight for _, weight in self.phases)

        for i, (_, weight) in enumerate(self.phases):
            if i < self.current_phase:
                total_progress += weight
            elif i == self.current_phase:
                total_progress += weight * self.phase_progress

        # 转换为百分比
        overall_consumed = int(total_progress * 100)
        overall_total = total_weight * 100

        self.progress_bar.update(overall_consumed, overall_total)

    def complete_phase(self):
        """完成当前阶段"""
        self.phase_progress = 1.0
        self._update_overall()

    def finish(self):
        """完成所有任务"""
        if self.progress_bar:
            total_weight = sum(weight for _, weight in self.phases)
            self.progress_bar.update(total_weight * 100, total_weight * 100)


def create_progress_callback(filename: Optional[str] = None, **kwargs) -> Callable:
    """创建进度回调函数（简化版，只有bar样式）"""
    progress_bar = None
    display_name = filename or "上传"

    def callback(consumed: int, total: int):
        nonlocal progress_bar
        if progress_bar is None:
            progress_bar = ProgressBar(display_name, **kwargs)
        progress_bar.update(consumed, total)

    return callback


def create_multi_file_progress_callback(
    files: list[dict[str, Any]], **kwargs
) -> Callable:
    """创建多文件上传的整体进度回调"""
    if not files:
        return lambda idx: lambda c, t: None

    # 创建整体进度管理器
    overall = OverallProgress("上传进度", **kwargs)

    # 添加文件处理阶段
    for i, file_info in enumerate(files):
        file_name = file_info.get("name", f"文件{i + 1}")
        # 根据文件大小计算权重，最小权重为1
        file_size = file_info.get("size", 1024)  # 默认1KB
        weight = max(1, file_size // (100 * 1024))  # 每100KB为1个权重单位
        overall.add_phase(file_name, weight)

    def get_file_callback(file_index: int) -> Callable[[int, int], None]:
        if 0 <= file_index < len(files):
            overall.start_phase(file_index)

        def callback(consumed: int, total: int):
            # 更新当前阶段进度
            phase_progress = consumed / total if total > 0 else 0
            overall.update_phase_progress(phase_progress)

            # 如果文件完成
            if consumed >= total:
                overall.complete_phase()

                # 如果是最后一个文件
                if file_index == len(files) - 1:
                    overall.finish()

        return callback

    return get_file_callback
