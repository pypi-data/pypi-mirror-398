import time
import uuid
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Callable

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np


def timer(func: Callable) -> Callable:
    """
    装饰器：计算函数执行时间和平均执行时间

    Args:
        func: 需要计时的函数

    Returns:
        包装后的函数

    Example:
        ```python
            @timer
            def my_function():
                pass
        ```
    """
    total_time = 0
    n = 0

    @wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal n, total_time
        start = time.perf_counter()
        retval = func(*args, **kwargs)
        end = time.perf_counter()

        n += 1
        total_time += end - start
        print(f"Call {func.__name__} {n} times consume: {total_time:.5f}s")
        print(f"Average time consumed per call: {total_time / n:.5f}s")
        return retval

    return wrapper


def generate_unique_filename(prefix: str = "", extension: str = ".csv") -> str:
    """
    生成基于当前时间和UUID的唯一文件名

    Args:
        prefix: 文件名前缀
        extension: 文件扩展名 (如 .txt, .csv)

    Returns:
        唯一的文件名字符串
    """
    # 1. 获取当前时间，格式化为：年月日_时分秒
    time_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 2. 生成UUID的简短形式(取前8位），防止极端情况下的时间冲突
    unique_str = uuid.uuid4().hex[:8]

    # 3. 组合文件名
    filename = f"{prefix}{time_str}_{unique_str}{extension}"
    return filename


def visualize_metric(
    csv_file: str | Path, show_plot: bool = True, save_plot: bool = True
):
    """
    读取csv文件并可视化资源消耗情况

    Args:
        csv_file: csv文件路径
        show_plot: 是否显示图表
        save_plot: 是否将图表保存为图片（默认保存至csv文件所在目录）
    """
    # 1. 读取数据
    fp = Path(csv_file)
    if fp.suffix != ".csv":
        raise ValueError(f"{fp.name} is not a csv file!")
    struct_arr = np.genfromtxt(
        fp,
        dtype=[
            ("Timestamp", "datetime64[μs]"),
            ("CPU_Percent", "f"),
            ("Memory_Percent", "f"),
            ("Memory_RSS_MB", "f"),
            ("Memory_VMS_MB", "f"),
        ],
        delimiter=",",
        names=True,
        encoding="utf-8",
    )

    # 2. 提取绘图用的数据列
    timestamps = struct_arr["Timestamp"]
    cpu_percent = struct_arr["CPU_Percent"]
    memory_percent = struct_arr["Memory_Percent"]
    memory_rss_mb = struct_arr["Memory_RSS_MB"]
    memory_vms_mb = struct_arr["Memory_VMS_MB"]

    # 3. 创建图表
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    fig.suptitle(f"Resource Consumption Over Time (from {fp.name})", fontsize=16)

    # 4. 绘制CPU、内存使用率图
    ax1.plot(timestamps, cpu_percent, label="CPU %", color="tab:blue")
    ax1.plot(timestamps, memory_percent, label="Memory %", color="tab:green")

    # 计算 Y 轴动态范围
    max_usage = np.maximum(cpu_percent.max(), memory_percent.max()).item()
    ax1.set_ylabel("CPU & Memory Usage (%)")
    ax1.set_ylim(0, max(100, max_usage * 1.1))
    ax1.legend(loc="upper right")
    ax1.grid(True)

    # 5. 绘制内存使用图
    ax2.plot(timestamps, memory_rss_mb, label="RSS (Physical)", color="tab:red")
    ax2.plot(timestamps, memory_vms_mb, label="VMS (Virtual)", color="tab:orange")
    ax2.set_ylabel("Memory Usage (MB)")
    ax2.set_xlabel("Time")
    ax2.legend(loc="upper right")
    ax2.grid(True)

    # 6. 格式化X轴时间显示
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    fig.autofmt_xdate()  # 自动旋转日期标签

    plt.tight_layout(rect=(0, 0, 1, 0.96))  # 调整布局为标题留出空间

    # 7. 保存图表
    if save_plot:
        plt.savefig(fp.with_suffix(".png"), dpi=300, bbox_inches="tight")
        print(f"Save plot to {fp.with_suffix('.png')}")
    # 8. 显示图表
    if show_plot:
        plt.show()
