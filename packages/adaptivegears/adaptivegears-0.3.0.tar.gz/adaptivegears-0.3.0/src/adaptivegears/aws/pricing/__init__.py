from typing import Annotated, Any

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


# --- Models ---


class RDSProduct(BaseModel):
    sku: str
    normalization_factor: NormalizationFactor = Field(alias="normalizationSizeFactor")
    product: RDSInstance
    offers: list[Offer]

    @model_validator(mode="before")
    @classmethod
    def flatten_product(cls, data: Any) -> Any:
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"

        product = data.pop("product")
        attrs = product["attributes"]

        data["sku"] = product["sku"]
        data["normalizationSizeFactor"] = attrs["normalizationSizeFactor"]

        instance_type = attrs["instanceType"]
        database_engine = attrs["databaseEngine"]
        deployment_option = attrs["deploymentOption"]
        region_code = attrs["regionCode"]

        engine = ENGINE_MAP.get(database_engine, database_engine.lower())
        multi_az = deployment_option == "Multi-AZ"

        data["product"] = RDSInstance.get(
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


class Pricing:
    def __init__(self, region_name="us-east-1"):
        self.client = boto3.client("pricing", region_name=region_name)

    def get_rds_products(self, filters) -> list[RDSProduct]:
        """Fetch RDS products matching filters with pagination."""
        paginator = self.client.get_paginator("get_products")
        products = []

        for page in paginator.paginate(ServiceCode="AmazonRDS", Filters=filters):
            print(f"Fetched {len(page['PriceList'])} products in current page.")
            for item in page["PriceList"]:
                products.append(RDSProduct.model_validate_json(item))
            print(f"Fetched {len(products)} products so far...")

        return products
