from dataclasses import dataclass


@dataclass(slots=True)
class NaceCodeTypesense:
    country: str
    level: int
    code: str
    section_label: str
    section_code: str
    label_en: str
    label_en_extended: str
    label_en_embedding: list[float] | None = None
    label_en_extended_embedding: list[float] | None = None
    label_fr: str | None = None
    label_fr_extended: str | None = None
    label_fr_extended_embedding: list[float] | None = None
    label_fr_embedding: list[float] | None = None
    label_nl: str | None = None
    label_nl_extended: str | None = None
    label_nl_extended_embedding: list[float] | None = None
    label_nl_embedding: list[float] | None = None


@dataclass
class EntityName:
    name: str | None = None
    name_fr: str | None = None
    name_nl: str | None = None
    name_de: str | None = None
    website: str | None = None


@dataclass(init=False)
class CompanyNameTypesense(EntityName):
    _id: str
    establishments: list[EntityName] | None = None

    # We have to manually define the __init__ method here because of the way dataclasses work with inheritance
    def __init__(self, _id: str, establishments: list[EntityName] | None = None, **kwargs):
        super().__init__(**kwargs)
        self._id = _id
        self.establishments = establishments
