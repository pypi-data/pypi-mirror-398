# first line: 60
@memory.cache
def fetch_instance_type(instance_type: str, region: str) -> dict:
    """Fetch EC2 instance type info from AWS API (cached)."""
    ec2 = boto3.client("ec2", region_name=region)
    response = ec2.describe_instance_types(InstanceTypes=[instance_type])
    return response["InstanceTypes"][0]
