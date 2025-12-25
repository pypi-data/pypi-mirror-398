from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class PhoneOperator:
    """
    Store the phone operator data.
    This is used to cache the data we scrape from crdc.be which gives us the operator of a phone number.

    This is stored into the `phone_operators_cache` collection.

    :attribute _id: The phone number to store the operator for.
    :attribute operator: The operator of the phone number. Ex: Orange. None if the phone was not valid (not found in crdc)
    :attribute operator_last_update: The last time the operator was updated.
    :attribute last_update: The last time the phone operator was updated.
    """

    _id: str
    operator: str | None
    operator_last_update: datetime | None
    last_update: datetime = field(default_factory=lambda: datetime.now())
