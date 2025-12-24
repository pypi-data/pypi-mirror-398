from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Burstable(BaseModel, Generic[T]):
    """Baseline and max values for burstable resources"""

    baseline: T
    max: T


class ByteScale(StrEnum):
    """Data size scales"""

    # Decimal
    B = "B"
    KB = "KB"
    MB = "MB"
    GB = "GB"
    TB = "TB"
    # Binary
    KiB = "KiB"
    MiB = "MiB"
    GiB = "GiB"
    TiB = "TiB"
    # Bits
    bit = "bit"
    Kbit = "Kbit"
    Mbit = "Mbit"
    Gbit = "Gbit"


class ByteRateScale(StrEnum):
    """Data rate scales"""

    Bps = "Bps"
    KBps = "KBps"
    MBps = "MBps"
    GBps = "GBps"
    bps = "bps"
    Kbps = "Kbps"
    Mbps = "Mbps"
    Gbps = "Gbps"


class CPUScale(StrEnum):
    """CPU scales"""

    core = "core"
    millicore = "millicore"


BYTE_FACTORS: dict[ByteScale, float] = {
    # Decimal
    ByteScale.B: 1,
    ByteScale.KB: 1_000,
    ByteScale.MB: 1_000_000,
    ByteScale.GB: 1_000_000_000,
    ByteScale.TB: 1_000_000_000_000,
    # Binary
    ByteScale.KiB: 2**10,
    ByteScale.MiB: 2**20,
    ByteScale.GiB: 2**30,
    ByteScale.TiB: 2**40,
    # Bits
    ByteScale.bit: 0.125,
    ByteScale.Kbit: 125,
    ByteScale.Mbit: 125_000,
    ByteScale.Gbit: 125_000_000,
}

BYTE_RATE_FACTORS: dict[ByteRateScale, float] = {
    ByteRateScale.Bps: 1,
    ByteRateScale.KBps: 1_000,
    ByteRateScale.MBps: 1_000_000,
    ByteRateScale.GBps: 1_000_000_000,
    ByteRateScale.bps: 0.125,
    ByteRateScale.Kbps: 125,
    ByteRateScale.Mbps: 125_000,
    ByteRateScale.Gbps: 125_000_000,
}

CPU_FACTORS: dict[CPUScale, float] = {
    CPUScale.core: 1,
    CPUScale.millicore: 0.001,
}


class ByteUnit(BaseModel):
    """Data size unit"""

    value: float
    scale: ByteScale

    def to(self, target: ByteScale = ByteScale.B) -> float:
        bytes_ = self.value * BYTE_FACTORS[self.scale]
        return bytes_ / BYTE_FACTORS[target]


class ByteRateUnit(BaseModel):
    """Data rate unit"""

    value: float
    scale: ByteRateScale

    def to(self, target: ByteRateScale = ByteRateScale.Bps) -> float:
        bytes_per_sec = self.value * BYTE_RATE_FACTORS[self.scale]
        return bytes_per_sec / BYTE_RATE_FACTORS[target]


class CPUUnit(BaseModel):
    """CPU unit"""

    value: float
    scale: CPUScale

    def to(self, target: CPUScale = CPUScale.core) -> float:
        cores = self.value * CPU_FACTORS[self.scale]
        return cores / CPU_FACTORS[target]


class IOPSUnit(BaseModel):
    """IOPS unit (operations per second)"""

    value: int
