from datetime import datetime
from dataclasses import dataclass, field
from bson import ObjectId



# ? Note:
# We have to have this dataclass in dataclass to be able to map the company collection
# with the delivery_memory collection. Otherwise, it's a mess to query the collections together.
# I know it seems overkill, but it's the only way I could get it to work simply in the delivery_manger.


@dataclass(slots=True)
class BestEmail:
    email: str | None = None

@dataclass(slots=True)
class BestPhone:
    phone: str | None = None

@dataclass(slots=True)
class BestWebsite:
    website: str | None = None


@dataclass(slots=True)
class DeliveryMemory:
    """The data schema for the delivery_memory collection."""
    delivery_id: str
    company_id: str
    delivery_date: datetime
    _id: ObjectId = field(default_factory=ObjectId)
    # Optionals
    best_phone: BestPhone = field(default_factory=BestPhone)
    best_email: BestEmail = field(default_factory=BestEmail)
    best_website: BestWebsite = field(default_factory=BestWebsite)
    decision_maker_ids: list | None = None