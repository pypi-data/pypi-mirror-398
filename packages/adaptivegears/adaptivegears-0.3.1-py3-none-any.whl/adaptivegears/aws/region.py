import boto3
from joblib import Memory
from pydantic import BaseModel

memory = Memory(".cache", verbose=0)

# https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-region-billing-codes.html
BILLING_CODES = {
    "us-east-1": "USE1",
    "us-east-2": "USE2",
    "us-west-1": "USW1",
    "us-west-2": "USW2",
    "ca-central-1": "CAN1",
    "ca-west-1": "CAN2",
    "mx-central-1": "MXC1",
    "af-south-1": "AFS1",
    "ap-east-1": "APE1",
    "ap-east-2": "APE2",
    "ap-northeast-1": "APN1",
    "ap-northeast-2": "APN2",
    "ap-northeast-3": "APN3",
    "ap-south-1": "APS3",
    "ap-south-2": "APS5",
    "ap-southeast-1": "APS1",
    "ap-southeast-2": "APS2",
    "ap-southeast-3": "APS4",
    "ap-southeast-4": "APS6",
    "ap-southeast-5": "APS7",
    "ap-southeast-6": "APS8",
    "ap-southeast-7": "APS9",
    "eu-central-1": "EUC1",
    "eu-central-2": "EUC2",
    "eu-north-1": "EUN1",
    "eu-south-1": "EUS1",
    "eu-south-2": "EUS2",
    "eu-west-1": "EU",
    "eu-west-2": "EUW2",
    "eu-west-3": "EUW3",
    "il-central-1": "ILC1",
    "me-central-1": "MEC1",
    "me-south-1": "MES1",
    "sa-east-1": "SAE1",
    # GovCloud
    "us-gov-west-1": "UGW1",
    "us-gov-east-1": "UGE1",
    # China
    "cn-north-1": "CNN1",
    "cn-northwest-1": "CNW1",
    # European Sovereign Cloud (new partition, billing code TBD)
    "eusc-de-east-1": "EUSCDE1",
}


class Region(BaseModel):
    code: str
    name: str
    abbrv: str

    @property
    def pricing_filter(self) -> dict:
        return {"Type": "TERM_MATCH", "Field": "regionCode", "Value": self.code}


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


def get_regions() -> list[Region]:
    """Get cached regions as Pydantic models."""
    regions = [Region(**r) for r in fetch_regions()]
    assert regions, "No regions fetched from AWS"
    return regions


def find_region(query: str) -> Region | None:
    """Find region by code, name, or abbreviation (case-insensitive)."""
    query = query.lower()
    for r in get_regions():
        if r.code.lower() == query:
            return r
        if r.name.lower() == query:
            return r
        if r.abbrv == query:
            return r
    return None
