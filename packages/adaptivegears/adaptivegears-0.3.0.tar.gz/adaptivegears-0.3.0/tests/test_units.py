import pytest

from adaptivegears.aws.units import (
    Burstable,
    ByteRateScale,
    ByteRateUnit,
    ByteScale,
    ByteUnit,
    CPUScale,
    CPUUnit,
    IOPSUnit,
)


class TestByteUnit:
    def test_to_default_bytes(self):
        unit = ByteUnit(value=1, scale=ByteScale.GB)
        assert unit.to() == 1_000_000_000

    def test_decimal_conversion_gb_to_mb(self):
        unit = ByteUnit(value=1, scale=ByteScale.GB)
        assert unit.to(ByteScale.MB) == 1000

    def test_decimal_conversion_mb_to_gb(self):
        unit = ByteUnit(value=1000, scale=ByteScale.MB)
        assert unit.to(ByteScale.GB) == 1

    def test_binary_conversion_gib_to_mib(self):
        unit = ByteUnit(value=1, scale=ByteScale.GiB)
        assert unit.to(ByteScale.MiB) == 1024

    def test_binary_conversion_mib_to_gib(self):
        unit = ByteUnit(value=16384, scale=ByteScale.MiB)
        assert unit.to(ByteScale.GiB) == 16

    def test_bits_to_bytes(self):
        unit = ByteUnit(value=8, scale=ByteScale.bit)
        assert unit.to(ByteScale.B) == 1

    def test_gbit_to_mb(self):
        unit = ByteUnit(value=1, scale=ByteScale.Gbit)
        assert unit.to(ByteScale.MB) == 125

    def test_cross_decimal_binary(self):
        # 1 GiB in MB (binary to decimal)
        unit = ByteUnit(value=1, scale=ByteScale.GiB)
        result = unit.to(ByteScale.MB)
        assert result == pytest.approx(1073.741824)


class TestByteRateUnit:
    def test_to_default_bps(self):
        unit = ByteRateUnit(value=1, scale=ByteRateScale.GBps)
        assert unit.to() == 1_000_000_000

    def test_gbps_to_mbps(self):
        unit = ByteRateUnit(value=10, scale=ByteRateScale.Gbps)
        assert unit.to(ByteRateScale.MBps) == 1250

    def test_mbps_to_gbps(self):
        unit = ByteRateUnit(value=1250, scale=ByteRateScale.MBps)
        assert unit.to(ByteRateScale.Gbps) == 10

    def test_gbps_bits_to_gbps_bytes(self):
        unit = ByteRateUnit(value=8, scale=ByteRateScale.Gbps)
        assert unit.to(ByteRateScale.GBps) == 1


class TestCPUUnit:
    def test_to_default_core(self):
        unit = CPUUnit(value=2000, scale=CPUScale.millicore)
        assert unit.to() == 2

    def test_core_to_millicore(self):
        unit = CPUUnit(value=2, scale=CPUScale.core)
        assert unit.to(CPUScale.millicore) == 2000

    def test_millicore_to_core(self):
        unit = CPUUnit(value=500, scale=CPUScale.millicore)
        assert unit.to(CPUScale.core) == 0.5


class TestIOPSUnit:
    def test_value(self):
        unit = IOPSUnit(value=3000)
        assert unit.value == 3000


class TestBurstable:
    def test_burstable_byte_rate(self):
        burst = Burstable(
            baseline=ByteRateUnit(value=5, scale=ByteRateScale.Gbps),
            max=ByteRateUnit(value=10, scale=ByteRateScale.Gbps),
        )
        assert burst.baseline.to(ByteRateScale.MBps) == 625
        assert burst.max.to(ByteRateScale.MBps) == 1250

    def test_burstable_iops(self):
        burst = Burstable(
            baseline=IOPSUnit(value=3000),
            max=IOPSUnit(value=16000),
        )
        assert burst.baseline.value == 3000
        assert burst.max.value == 16000
