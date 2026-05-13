from dataclasses import dataclass, field
from typing import List
from datetime import datetime


@dataclass
class CPUInfo:
    percent: float
    cores: int
    per_core: List[float]


@dataclass
class GPUInfo:
    name: str
    load_percent: float
    memory_total_mb: float
    memory_used_mb: float
    memory_percent: float
    temperature: float


@dataclass
class MemoryInfo:
    total_gb: float
    used_gb: float
    percent: float


@dataclass
class DiskInfo:
    total_gb: float
    used_gb: float
    percent: float
    mount_point: str


@dataclass
class NetworkInfo:
    bytes_sent: int
    bytes_recv: int
    speed_sent_mbps: float
    speed_recv_mbps: float


@dataclass
class ProcessInfo:
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float


@dataclass
class SystemSnapshot:
    timestamp: datetime = field(default_factory=datetime.now)
    cpu: CPUInfo = None
    gpu: GPUInfo = None
    memory: MemoryInfo = None
    disks: List[DiskInfo] = field(default_factory=list)
    network: NetworkInfo = None
    processes: List[ProcessInfo] = field(default_factory=list)