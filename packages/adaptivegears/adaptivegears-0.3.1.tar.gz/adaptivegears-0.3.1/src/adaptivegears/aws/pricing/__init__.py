import json
from typing import Annotated, Any, Literal

import boto3
from pydantic import BaseModel, BeforeValidator, Field, model_validator

from adaptivegears.aws.compute import RDSInstance
from adaptivegears.aws.pricing.offers import Offer, parse_offers


# --- Parsers ---


def parse_int(v: str) -> int:
    """Parse '2' -> 2"""
    return int(v)


# --- Annotated types ---

NormalizationFactor = Annotated[int, BeforeValidator(parse_int)]


# --- Engine mapping ---

ENGINE_MAP = {
    "PostgreSQL": "postgres",
    "MySQL": "mysql",
    "MariaDB": "mariadb",
    "Oracle": "oracle",
    "SQL Server": "sqlserver",
    "Aurora PostgreSQL": "aurora-postgresql",
    "Aurora MySQL": "aurora-mysql",
}


# --- Product Models ---


class RDSInstanceProduct(BaseModel):
    """RDS database instance product with compute specs and pricing."""

    product_family: Literal["Database Instance"]
    sku: str
    deployment_option: str
    normalization_factor: NormalizationFactor = Field(alias="normalizationSizeFactor")
    instance: RDSInstance
    offers: list[Offer]

    @model_validator(mode="before")
    @classmethod
    def flatten_product(cls, data: Any) -> Any:
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"

        product = data.pop("product")
        attrs = product["attributes"]

        data["product_family"] = product["productFamily"]
        data["sku"] = product["sku"]
        data["normalizationSizeFactor"] = attrs["normalizationSizeFactor"]
        data["deployment_option"] = attrs["deploymentOption"]

        instance_type = attrs["instanceType"]
        database_engine = attrs["databaseEngine"]
        deployment_option = attrs["deploymentOption"]
        region_code = attrs["regionCode"]

        engine = ENGINE_MAP.get(database_engine, database_engine.lower())
        multi_az = deployment_option == "Multi-AZ"

        data["instance"] = RDSInstance.get(
            instance_class=instance_type,
            engine=engine,
            multi_az=multi_az,
            region=region_code,
        )

        # Parse offers
        terms = data.pop("terms")
        assert not isinstance(terms, list), "terms already parsed"
        data["offers"] = parse_offers(terms)

        return data


class RDSStorageProduct(BaseModel):
    """RDS database storage product (gp2, gp3, io1, io2).

    Price is per GB (hourly rate converted from GB-Mo).
    Multiply price.daily by storage_gb to get total daily cost.
    """

    product_family: Literal["Database Storage"]
    sku: str
    deployment_option: str
    volume_type: str
    offers: list[Offer]

    @model_validator(mode="before")
    @classmethod
    def flatten_product(cls, data: Any) -> Any:
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"

        product = data.pop("product")
        attrs = product["attributes"]

        data["product_family"] = product["productFamily"]
        data["sku"] = product["sku"]
        data["deployment_option"] = attrs["deploymentOption"]
        data["volume_type"] = attrs["volumeType"]

        terms = data.pop("terms")
        data["offers"] = parse_offers(terms)

        return data


IOPS_GROUP_MAP = {
    "RDS Provisioned IOPS": "io1",
    "RDS Provisioned GP3 IOPS": "gp3",
    "RDS Provisioned IO2 IOPS": "io2",
}


class RDSIOPSProduct(BaseModel):
    """RDS provisioned IOPS product (io1, gp3, io2).

    Price is per IOPS (hourly rate converted from IOPS-Mo).
    Multiply price.daily by iops to get total daily cost.
    """

    product_family: Literal["Provisioned IOPS"]
    sku: str
    deployment_option: str
    volume_type: str
    offers: list[Offer]

    @model_validator(mode="before")
    @classmethod
    def flatten_product(cls, data: Any) -> Any:
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"

        product = data.pop("product")
        attrs = product["attributes"]

        data["product_family"] = product["productFamily"]
        data["sku"] = product["sku"]
        data["deployment_option"] = attrs["deploymentOption"]

        # volumeType only exists for io2, derive from groupDescription
        group_desc = attrs["groupDescription"]
        assert group_desc in IOPS_GROUP_MAP, f"Unknown IOPS group: {group_desc}"
        data["volume_type"] = IOPS_GROUP_MAP[group_desc]

        terms = data.pop("terms")
        data["offers"] = parse_offers(terms)

        return data


class RDSThroughputProduct(BaseModel):
    """RDS provisioned throughput product (gp3).

    Price is per MiBps (hourly rate converted from MBPS-Mo).
    Multiply price.daily by throughput_mibps to get total daily cost.
    """

    product_family: Literal["Provisioned Throughput"]
    sku: str
    deployment_option: str
    offers: list[Offer]

    @model_validator(mode="before")
    @classmethod
    def flatten_product(cls, data: Any) -> Any:
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"

        product = data.pop("product")
        attrs = product["attributes"]

        data["product_family"] = product["productFamily"]
        data["sku"] = product["sku"]
        data["deployment_option"] = attrs["deploymentOption"]

        terms = data.pop("terms")
        data["offers"] = parse_offers(terms)

        return data


# --- Discriminated Union ---

RDSProduct = Annotated[
    RDSInstanceProduct | RDSStorageProduct | RDSIOPSProduct | RDSThroughputProduct,
    Field(discriminator="product_family"),
]

PRODUCT_CLASS_MAP = {
    "Database Instance": RDSInstanceProduct,
    "Database Storage": RDSStorageProduct,
    "Provisioned IOPS": RDSIOPSProduct,
    "Provisioned Throughput": RDSThroughputProduct,
}


# --- Pricing Client ---


class Pricing:
    def __init__(self, region_name="us-east-1"):
        self.client = boto3.client("pricing", region_name=region_name)

    def get_rds_products(self, filters) -> list[RDSProduct]:
        """Fetch RDS products matching filters with pagination."""
        paginator = self.client.get_paginator("get_products")
        products = []

        for page in paginator.paginate(ServiceCode="AmazonRDS", Filters=filters):
            for item in page["PriceList"]:
                raw = json.loads(item)
                product_family = raw["product"]["productFamily"]
                product_class = PRODUCT_CLASS_MAP.get(product_family)
                if product_class:
                    products.append(product_class.model_validate(raw))

        return products
