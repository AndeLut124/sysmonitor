import psutil
import time
from datetime import datetime
from .models import (
    SystemSnapshot, CPUInfo, GPUInfo, MemoryInfo, DiskInfo,
    NetworkInfo, ProcessInfo
)
from .ring_buffer import RingBuffer


class MetricCollector:
    """Собирает метрики системы. Не зависит от API и веба."""

    def __init__(self, history_size: int = 60):
        self._history = RingBuffer[SystemSnapshot](max_size=history_size)
        self._prev_net = psutil.net_io_counters()
        self._prev_time = time.time()
        self._gpu_available = False

        # Проверяем наличие GPU
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            self._gpu_available = len(gpus) > 0
        except (ImportError, Exception):
            self._gpu_available = False

    def _get_gpu_info(self) -> GPUInfo | None:
        """Собирает метрики GPU через GPUtil."""
        if not self._gpu_available:
            return None

        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if not gpus:
                return None

            gpu = gpus[0]  # Берём первую видеокарту

            return GPUInfo(
                name=gpu.name,
                load_percent=round(gpu.load * 100, 1),
                memory_total_mb=round(gpu.memoryTotal, 1),
                memory_used_mb=round(gpu.memoryUsed, 1),
                memory_percent=round(gpu.memoryUtil * 100, 1),
                temperature=round(gpu.temperature, 1)
            )
        except Exception:
            return None

    def collect(self) -> SystemSnapshot:
        """Снять один снимок системы."""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_cores = psutil.cpu_count()
        cpu_per_core = psutil.cpu_percent(interval=0, percpu=True)

        # GPU
        gpu = self._get_gpu_info()

        # Memory
        mem = psutil.virtual_memory()
        memory = MemoryInfo(
            total_gb=round(mem.total / (1024**3), 1),
            used_gb=round(mem.used / (1024**3), 1),
            percent=mem.percent
        )

        # Disks
        disks = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append(DiskInfo(
                    total_gb=round(usage.total / (1024**3), 1),
                    used_gb=round(usage.used / (1024**3), 1),
                    percent=usage.percent,
                    mount_point=part.mountpoint
                ))
            except PermissionError:
                continue

        # Network
        current_net = psutil.net_io_counters()
        current_time = time.time()
        delta_time = current_time - self._prev_time

        if delta_time > 0:
            speed_sent = (current_net.bytes_sent - self._prev_net.bytes_sent) / delta_time
            speed_recv = (current_net.bytes_recv - self._prev_net.bytes_recv) / delta_time
        else:
            speed_sent = speed_recv = 0

        network = NetworkInfo(
            bytes_sent=current_net.bytes_sent,
            bytes_recv=current_net.bytes_recv,
            speed_sent_mbps=round(speed_sent * 8 / 1_000_000, 2),
            speed_recv_mbps=round(speed_recv * 8 / 1_000_000, 2)
        )

        self._prev_net = current_net
        self._prev_time = current_time

        # Processes
        processes = []
        for proc in sorted(
            psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]),
            key=lambda p: p.info["cpu_percent"] or 0,
            reverse=True
        )[:15]:
            try:
                name = (proc.info["name"] or "Unknown").lower()
                cpu_pct = proc.info["cpu_percent"] or 0
                mem_pct = proc.info["memory_percent"] or 0

                if "idle" in name:
                    continue

                processes.append(ProcessInfo(
                    pid=proc.info["pid"],
                    name=proc.info["name"] or "Unknown",
                    cpu_percent=round(cpu_pct, 1),
                    memory_percent=round(mem_pct, 1)
                ))

                if len(processes) >= 10:
                    break

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        snapshot = SystemSnapshot(
            timestamp=datetime.now(),
            cpu=CPUInfo(percent=cpu_percent, cores=cpu_cores, per_core=cpu_per_core),
            gpu=gpu,
            memory=memory,
            disks=disks,
            network=network,
            processes=processes
        )

        self._history.push(snapshot)
        return snapshot

    def get_history(self) -> list[SystemSnapshot]:
        return self._history.get_all()

    def get_latest(self) -> SystemSnapshot | None:
        return self._history.get_last()