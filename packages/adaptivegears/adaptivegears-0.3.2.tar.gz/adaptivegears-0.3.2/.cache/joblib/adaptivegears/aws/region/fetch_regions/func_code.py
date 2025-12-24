# first line: 58
@memory.cache
def fetch_regions() -> list[dict]:
    """Fetch all AWS regions from SSM global infrastructure."""
    ssm = boto3.client("ssm", region_name="us-east-1")

    regions = []
    paginator = ssm.get_paginator("get_parameters_by_path")

    for page in paginator.paginate(Path="/aws/service/global-infrastructure/regions"):
        for param in page["Parameters"]:
            code = param["Value"]

            r = ssm.get_parameter(
                Name=f"/aws/service/global-infrastructure/regions/{code}/longName"
            )
            name = r["Parameter"]["Value"]
            assert code in BILLING_CODES, f"Missing billing code for region: {code}"
            abbrv = BILLING_CODES[code].lower()

            regions.append({"code": code, "name": name, "abbrv": abbrv})

    return regions
