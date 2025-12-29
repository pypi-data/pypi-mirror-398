import csv
import sys
import time
from contextlib import contextmanager
from datetime import datetime

import psutil

from .utils import generate_unique_filename


class ProcessMonitor:
    """持续监控指定进程CPU和内存消耗，并将数据保存到csv文件"""

    def __init__(self, pid: int, interval: float = 1.0):
        """
        初始化监控器

        Args:
            pid: 要监控的进程ID
            interval: 监控间隔(秒)
        """
        self.pid = pid
        self.interval = interval
        self.filename = generate_unique_filename()
        self._is_running = False

        # 尝试附加到进程
        try:
            self.process = psutil.Process(pid)
            print(f"Successfully attached to process: {pid} ({self.process.name()})")
        except psutil.NoSuchProcess:
            raise ValueError(f"Process {pid} does not exist!")
        except psutil.AccessDenied:
            raise ValueError(f"Access denied to process {pid}!")

    @contextmanager
    def _prepare_csv(self):
        """准备CSV文件，如果不存在则创建并写入表头

        Yields:
            csv.writer: CSV写入器对象
        """
        f = open(self.filename, "w", newline="", buffering=1, encoding="utf-8")
        writer = csv.writer(f)
        try:
            writer.writerow(
                [
                    "Timestamp",
                    "CPU_Percent",
                    "Memory_Percent",
                    "Memory_RSS_MB",
                    "Memory_VMS_MB",
                ]
            )
            yield writer
        finally:
            f.close()

    def _monitoring(self):
        """监控循环，持续收集进程资源使用情况并写入CSV文件"""
        print(f"Monitoring process {self.pid} with interval {self.interval}s.")
        print(f"Metrics will be saved to: {self.filename}")
        with self._prepare_csv() as writer:
            while self._is_running:
                try:
                    # 获取时间戳
                    timestamp = datetime.now().isoformat()

                    metrics = self.process.as_dict(
                        ["pid", "cpu_percent", "memory_percent", "memory_info"]
                    )
                    # 获取CPU使用率（非阻塞）
                    cpu_percent = metrics["cpu_percent"] / psutil.cpu_count()

                    # 获取内存信息
                    mem_percent = metrics["memory_percent"]
                    mem_info = metrics["memory_info"]
                    mem_rss_mb = mem_info.rss / (1024 * 1024)  # 物理内存
                    mem_vms_mb = mem_info.vms / (1024 * 1024)  # 虚拟内存

                    # 写入CSV
                    writer.writerow(
                        [
                            timestamp,
                            f"{cpu_percent:.2f}",
                            f"{mem_percent:.2f}",
                            f"{mem_rss_mb:.2f}",
                            f"{mem_vms_mb:.2f}",
                        ]
                    )
                    time.sleep(self.interval)
                except psutil.NoSuchProcess:
                    print(
                        f"\nProcess {self.pid} has terminated, stopping monitoring.",
                        file=sys.stderr,
                    )
                    self.stop()  # 进程已退出，自动停止监控
                    break
                except KeyboardInterrupt:
                    print("\nUser interrupted monitoring!")
                    self.stop()
                    break
                except Exception as e:
                    print(f"\nError occurred during monitoring: {e}", file=sys.stderr)
                    self.stop()
                    break

    def start(self):
        """启动监控"""
        if self._is_running:
            print("Monitoring is already running.")
            return

        self._is_running = True
        self._monitoring()

    def stop(self):
        """停止监控"""
        if not self._is_running:
            print("Monitoring is not running.")
            return

        self._is_running = False
        print("Monitoring stopped.")
