import boto3
from joblib import Memory
from pydantic import BaseModel

from adaptivegears.aws.region import Region, find_region
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

memory = Memory(".cache", verbose=0)


class Resources(BaseModel):
    """Compute resources specification"""

    cpu: CPUUnit
    memory: ByteUnit
    network: Burstable[ByteRateUnit]
    storage_iops: Burstable[IOPSUnit]
    storage_throughput: Burstable[ByteRateUnit]


class RDSInstance(BaseModel):
    """RDS instance specification"""

    engine: str
    engine_version: str | None
    multi_az: bool
    region: Region
    instance: "EC2Instance"

    @classmethod
    def get(
        cls,
        instance_class: str,
        engine: str,
        engine_version: str | None = None,
        multi_az: bool = False,
        region: str = "us-east-1",
    ) -> "RDSInstance":
        region_model = find_region(region)
        assert region_model, f"Unknown region: {region}"
        instance = EC2Instance.get(instance_class, region=region)
        return cls(
            engine=engine,
            engine_version=engine_version,
            multi_az=multi_az,
            region=region_model,
            instance=instance,
        )


@memory.cache
def fetch_instance_type(instance_type: str, region: str) -> dict:
    """Fetch EC2 instance type info from AWS API (cached)."""
    ec2 = boto3.client("ec2", region_name=region)
    response = ec2.describe_instance_types(InstanceTypes=[instance_type])
    return response["InstanceTypes"][0]

# https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-network-bandwidth.html
class EC2Instance(BaseModel):
    """EC2 instance specification"""

    instance_type: str
    instance_family: str
    architecture: str
    region: str
    resources: Resources

    @classmethod
    def get(cls, instance_type: str, region: str = "us-east-1") -> "EC2Instance":
        """Fetch instance type specs from AWS."""
        # Handle service prefixes (db., cache.) and suffixes (.search)
        ec2_type = (
            instance_type
            .removeprefix("db.")
            .removeprefix("cache.")
            .removesuffix(".search")
        )
        assert ec2_type.count(".") == 1, f"Invalid instance type: {instance_type}"

        data = fetch_instance_type(ec2_type, region)
        instance_family = ec2_type.split(".")[0]
        architecture = data["ProcessorInfo"]["SupportedArchitectures"][0]

        vcpu = data["VCpuInfo"]["DefaultVCpus"]
        memory_mib = data["MemoryInfo"]["SizeInMiB"]

        network_card = data["NetworkInfo"]["NetworkCards"][0]
        network_baseline = network_card["BaselineBandwidthInGbps"]
        network_max = network_card["PeakBandwidthInGbps"]

        ebs = data["EbsInfo"]["EbsOptimizedInfo"]
        iops_baseline = ebs["BaselineIops"]
        iops_max = ebs["MaximumIops"]
        throughput_baseline = ebs["BaselineThroughputInMBps"]
        throughput_max = ebs["MaximumThroughputInMBps"]

        resources = Resources(
            cpu=CPUUnit(value=vcpu, scale=CPUScale.core),
            memory=ByteUnit(value=memory_mib, scale=ByteScale.MiB),
            network=Burstable(
                baseline=ByteRateUnit(value=network_baseline, scale=ByteRateScale.Gbps),
                max=ByteRateUnit(value=network_max, scale=ByteRateScale.Gbps),
            ),
            storage_iops=Burstable(
                baseline=IOPSUnit(value=iops_baseline),
                max=IOPSUnit(value=iops_max),
            ),
            storage_throughput=Burstable(
                baseline=ByteRateUnit(value=throughput_baseline, scale=ByteRateScale.MBps),
                max=ByteRateUnit(value=throughput_max, scale=ByteRateScale.MBps),
            ),
        )

        return cls(
            instance_type=instance_type,
            instance_family=instance_family,
            architecture=architecture,
            region=region,
            resources=resources,
        )
