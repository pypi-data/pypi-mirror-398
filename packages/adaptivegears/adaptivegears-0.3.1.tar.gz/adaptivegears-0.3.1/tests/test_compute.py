import pytest

from adaptivegears.aws.compute import EC2Instance, RDSInstance, Resources
from adaptivegears.aws.units import ByteRateScale, ByteScale, CPUScale


class TestEC2InstanceValidation:
    def test_invalid_instance_type_no_dot(self):
        with pytest.raises(AssertionError, match="Invalid instance type"):
            EC2Instance.get("r6glarge")

    def test_invalid_instance_type_multiple_dots(self):
        with pytest.raises(AssertionError, match="Invalid instance type"):
            EC2Instance.get("r6g.large.extra")


@pytest.mark.vcr()
class TestEC2Instance:
    def test_get_r6g_large(self):
        instance = EC2Instance.get("r6g.large", region="us-east-1")

        assert instance.instance_type == "r6g.large"
        assert instance.instance_family == "r6g"
        assert instance.architecture == "arm64"
        assert instance.region == "us-east-1"
        assert isinstance(instance.resources, Resources)

    def test_get_r6g_large_cpu(self):
        instance = EC2Instance.get("r6g.large", region="us-east-1")

        assert instance.resources.cpu.value == 2
        assert instance.resources.cpu.scale == CPUScale.core

    def test_get_r6g_large_memory(self):
        instance = EC2Instance.get("r6g.large", region="us-east-1")

        assert instance.resources.memory.value == 16384
        assert instance.resources.memory.scale == ByteScale.MiB
        assert instance.resources.memory.to(ByteScale.GiB) == 16

    def test_get_r6g_large_network(self):
        instance = EC2Instance.get("r6g.large", region="us-east-1")

        assert instance.resources.network.baseline.value == 0.75
        assert instance.resources.network.baseline.scale == ByteRateScale.Gbps
        assert instance.resources.network.max.value == 10.0

    def test_get_r6g_large_storage_iops(self):
        instance = EC2Instance.get("r6g.large", region="us-east-1")

        assert instance.resources.storage_iops.baseline.value == 3600
        assert instance.resources.storage_iops.max.value == 20000

    def test_get_r6g_large_storage_throughput(self):
        instance = EC2Instance.get("r6g.large", region="us-east-1")

        assert instance.resources.storage_throughput.baseline.value == 78.75
        assert instance.resources.storage_throughput.baseline.scale == ByteRateScale.MBps
        assert instance.resources.storage_throughput.max.value == 593.75

    def test_get_rds_db_prefix(self):
        instance = EC2Instance.get("db.r6g.large", region="us-east-1")

        assert instance.instance_type == "db.r6g.large"
        assert instance.instance_family == "r6g"
        assert instance.resources.cpu.value == 2

    def test_get_elasticache_cache_prefix(self):
        instance = EC2Instance.get("cache.r6g.large", region="us-east-1")

        assert instance.instance_type == "cache.r6g.large"
        assert instance.instance_family == "r6g"
        assert instance.resources.cpu.value == 2

    def test_get_opensearch_search_suffix(self):
        instance = EC2Instance.get("r6g.large.search", region="us-east-1")

        assert instance.instance_type == "r6g.large.search"
        assert instance.instance_family == "r6g"
        assert instance.resources.cpu.value == 2


@pytest.mark.vcr()
class TestRDSInstance:
    def test_get(self):
        rds = RDSInstance.get(
            "db.r6g.large",
            engine="postgres",
            engine_version="16.4",
            region="us-east-1",
        )

        assert rds.engine == "postgres"
        assert rds.engine_version == "16.4"
        assert rds.multi_az is False
        assert rds.region.code == "us-east-1"
        assert rds.region.abbrv == "use1"
        assert rds.instance.instance_type == "db.r6g.large"
        assert rds.instance.resources.cpu.value == 2

    def test_get_without_engine_version(self):
        rds = RDSInstance.get(
            "db.r6g.large",
            engine="postgres",
            region="us-east-1",
        )

        assert rds.engine == "postgres"
        assert rds.engine_version is None
        assert rds.instance.instance_type == "db.r6g.large"
