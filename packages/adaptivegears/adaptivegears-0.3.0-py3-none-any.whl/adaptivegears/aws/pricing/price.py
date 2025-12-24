from datetime import date
from decimal import Decimal
from enum import Enum

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel


def relativedelta_to_days(rd: relativedelta) -> int:
    """Convert relativedelta to days."""
    today = date.today()
    return (today + rd - today).days


class PaymentSchedule(Enum):
    """How often AWS charges for recurring costs.

    Values are relativedelta intervals representing the billing frequency.
    For one-time payments (upfront), use None instead of a PaymentSchedule.
    """

    MONTHLY = relativedelta(months=1)
    HOURLY = relativedelta(hours=1)


class Cost(BaseModel):
    """A single cost component with amount and payment terms.

    Supports both one-time and recurring costs:
    - One-time (upfront): payment_schedule=None, payment_period required
    - Recurring (hourly): payment_schedule=HOURLY, no period needed (on-demand)
    - Recurring (monthly): payment_schedule=MONTHLY, payment_period required (reserved)

    The amount field represents:
    - For one-time: total upfront payment
    - For recurring: hourly rate (even if billed monthly)

    Examples:
        # All upfront for 1 year
        Cost(amount=Decimal("1000"), payment_period=relativedelta(years=1))

        # On-demand hourly
        Cost(amount=Decimal("0.10"), payment_schedule=PaymentSchedule.HOURLY)

        # Reserved, billed monthly for 1 year
        Cost(amount=Decimal("0.08"), payment_schedule=PaymentSchedule.MONTHLY,
             payment_period=relativedelta(years=1))
    """

    amount: Decimal
    payment_schedule: PaymentSchedule | None = None  # None = one-time
    payment_period: relativedelta | None = None

    class Config:
        arbitrary_types_allowed = True

    @property
    def hourly_rate(self) -> Decimal:
        """Convert cost to hourly rate for comparison.

        One-time costs are amortized over payment_period.
        Recurring costs are already hourly rates.
        """
        if self.payment_schedule is None:
            hours = relativedelta_to_days(self.payment_period) * 24
            return self.amount / hours
        return self.amount


class Price(BaseModel):
    """Total price composed of multiple cost components.

    A price can have multiple costs, e.g. partial upfront reserved instance:
    - One-time upfront payment
    - Monthly recurring payment

    Prices can be added together to combine costs from different sources.
    """

    costs: list[Cost]

    def __add__(self, other: "Price") -> "Price":
        return Price(costs=self.costs + other.costs)

    @property
    def daily(self) -> Decimal:
        """Calculate total daily cost across all components."""
        return sum(cost.hourly_rate * 24 for cost in self.costs)
