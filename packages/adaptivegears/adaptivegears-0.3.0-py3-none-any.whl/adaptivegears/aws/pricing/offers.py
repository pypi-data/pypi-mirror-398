from decimal import Decimal
from enum import StrEnum

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel

from adaptivegears.aws.pricing.price import Cost, PaymentSchedule, Price


class ReservationPurchaseOption(StrEnum):
    ALL_UPFRONT = "all_upfront"
    PARTIAL_UPFRONT = "partial_upfront"
    NO_UPFRONT = "no_upfront"


RESERVATION_PERIOD_MAP = {
    "1yr": relativedelta(years=1),
    "3yr": relativedelta(years=3),
}

RESERVATION_PURCHASE_OPTION_MAP = {
    "All Upfront": ReservationPurchaseOption.ALL_UPFRONT,
    "Partial Upfront": ReservationPurchaseOption.PARTIAL_UPFRONT,
    "No Upfront": ReservationPurchaseOption.NO_UPFRONT,
}


class Reservation(BaseModel):
    period: relativedelta
    purchase_option: ReservationPurchaseOption

    class Config:
        arbitrary_types_allowed = True


class Offer(BaseModel):
    code: str  # e.g., "SYSS9K5CM54GB44V.JRTCKXETXF"
    reservation: Reservation | None = None  # None = on-demand
    price: Price

    @classmethod
    def from_raw(cls, code: str, raw: dict, reserved: bool) -> "Offer":
        """Parse raw offer data into an Offer."""
        # Build reservation (None for on-demand)
        if not reserved:
            reservation = None
        else:
            raw_terms = raw["termAttributes"]
            raw_length = raw_terms["LeaseContractLength"]
            raw_option = raw_terms["PurchaseOption"]
            reservation = Reservation(
                period=RESERVATION_PERIOD_MAP[raw_length],
                purchase_option=RESERVATION_PURCHASE_OPTION_MAP[raw_option],
            )

        raw_prices = raw["priceDimensions"]
        # Extract pricing from dimensions
        costs = []
        for raw_price in raw_prices.values():
            unit = raw_price["unit"]
            amount = Decimal(raw_price["pricePerUnit"]["USD"]).normalize()
            if not amount:
                continue
            if unit == "Quantity":
                costs.append(Cost(amount=amount, payment_period=reservation.period))
            elif unit == "Hrs":
                if reservation:
                    costs.append(Cost(amount=amount, payment_schedule=PaymentSchedule.MONTHLY, payment_period=reservation.period))
                else:
                    costs.append(Cost(amount=amount, payment_schedule=PaymentSchedule.HOURLY))

        return cls(
            code=code,
            reservation=reservation,
            price=Price(costs=costs),
        )


def parse_offers(data: dict) -> list[Offer]:
    """Parse nested terms structure into flat list of Offer objects."""
    offers = []

    for reserved, type_key in [(False, "OnDemand"), (True, "Reserved")]:
        raw_offers = data.get(type_key) or {}
        for code, raw in raw_offers.items():
            offers.append(Offer.from_raw(code, raw, reserved))

    return offers
