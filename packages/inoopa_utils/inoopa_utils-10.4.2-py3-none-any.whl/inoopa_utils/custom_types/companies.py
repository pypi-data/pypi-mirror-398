from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

import pendulum


@dataclass(slots=True)
class Finance:
    """
    Dataclass to store the finance report data from a company.

    This is used to store the finance report data from a company.
    """

    # The date at which the finance report was submitted
    last_report_year: int | None = None
    turnover: int | None = None
    total_equity: int | None = None
    net_result: int | None = None
    working_capital: int | None = None
    balance_sheet_total: int | None = None
    authorized_capital: int | None = None
    paid_up_capital: int | None = None
    issued_capital: int | None = None
    partnership_capital: int | None = None
    accountant_name: str | None = None


@dataclass(slots=True)
class Address:
    source: str
    last_update: datetime | None  # From source
    last_seen: datetime  # When we last saw it while scraping
    street: str | None = None
    number: str | None = None
    city: str | None = None
    province: str | None = None
    region: str | None = None
    postal_code: str | None = None
    additionnal_address_info: str | None = None
    string_address: str | None = None


@dataclass(slots=True)
class ParsedAddress:
    street: str | None = None
    number: str | None = None
    city: str | None = None
    postal_code: str | None = None


@dataclass(slots=True)
class NaceCode:
    """
    :param number: The Nace code number.
    :param description: The description of the Nace code.
    :param section_code: The section (one of the 21 high level category) code of the Nace code .
    :param section_label: The section label of the Nace code.
    :param source: `official:bce` or `inoopa:nace_correction`. The source of the Nace code.
        Starts with `official:` if it's from the country official data. Starts with `inoopa:` if it's from us.
    :param correction_ranking: The ranking of the correction NACE code correction algorithm (Typesense).
    :param correction_distance: The sementic distance of the correction NACE code correction algorithm (Typesense).
    :param is_main_activity: True if it's the main activity of the company. (from BCE data)
    :param nace_type: The type of the NACE code. Can be `VAT`, `NSSO` or `unknown` (or None).
    """

    number: str
    description: str
    section_code: str
    section_label: str
    source: str
    correction_ranking: int | None = None
    correction_distance: float | None = None
    is_main_activity: bool = False
    nace_type: Literal["VAT", "NSSO", "unknown"] | None = None


@dataclass(slots=True)
class NaceCodeExtended:
    """
    Class representing the NACE codes in the `nace_codes` Mongo collection, mainly used for internal testing.

    :param number: The NACE code number.
    :param description_fr: The French description of the NACE code.
    :param description_nl: The Dutch description of the NACE code.
    :param description_en: The English description of the NACE code.
    :param section_code: The section (one of the 21 high level category) code of the NACE code.
    :param section_label: The section label of the NACE code.
    :param version: The NACE version year (2003, 2008, or 2025).
    :param country: The country code ("BE" for Belgium, "NL" for Netherlands, "FR" for France).
    """

    number: str
    level: int
    description_fr: str | None
    description_nl: str | None
    description_en: str | None
    section_code: str
    section_label: str
    version: Literal[2003, 2008, 2025]
    country: Literal["BE", "NL", "FR"]


@dataclass(slots=True)
class Email:
    email: str
    source: str
    last_seen: datetime
    score: int | None = None


@dataclass(slots=True)
class Phone:
    phone: str
    source: str
    last_seen: datetime
    score: int | None = None
    # Phone provider (ex: Vodafone, Orange, Voo,...)
    operator: str | None = None
    # Last time the operator DB was updated for this phone
    operator_last_update: datetime | None = None
    is_mobile: bool | None = None


@dataclass(slots=True)
class Website:
    """
    :param source: The source of the website. Ex: BCE, websites_finers,..., etc.
    :param website: The website url. with http scheme, endpoints,... Ex: https://www.inoop.com/contact
    :param domain: The domain of the website. Ex: inoop.com
    :param base_url: The base url of the website. Ex: https://www.inoop.com
    :param last_seen: The last time the website was seen.
    :param score: The score of the website. This is used to rank the websites.
    """

    source: str
    website: str
    domain: str
    base_url: str
    last_seen: datetime
    score: int | None = None


@dataclass(slots=True)
class BoardMember:
    is_company: bool
    function: str
    name: str
    start_date: datetime | None = None
    linked_company_number: str | None = None


@dataclass(slots=True)
class SocialNetwork:
    last_seen: datetime
    name: str
    url: str
    source: str | None = None
    score: int | None = None


@dataclass(slots=True)
class BestNaceCodes:
    first_best_nace_code: NaceCode | None = None
    second_best_nace_code: NaceCode | None = None
    third_best_nace_code: NaceCode | None = None


@dataclass(slots=True)
class Establishment:
    establishment_number: str
    last_seen: datetime
    # If no emails are provided, it should be an empty list. This is crutial for the mongoDB queries.
    # If you would do `emails: list = []` it would be the same list for all instances of the class!
    # which is why we use `default_factory`. (Same for phones, websites, social_networks, nace_codes)
    emails: list[Email] = field(default_factory=list)
    phones: list[Phone] = field(default_factory=list)
    websites: list[Website] = field(default_factory=list)
    nace_codes: list[NaceCode] = field(default_factory=list)
    social_networks: list[SocialNetwork] = field(default_factory=list)
    status: str | None = None
    start_date: datetime | None = None
    country: Literal["BE"] = "BE"
    name: str | None = None
    name_fr: str | None = None
    name_nl: str | None = None
    name_de: str | None = None
    name_last_update: str | None = None
    address: Address | None = None
    best_email: Email | None = None
    best_phone: Phone | None = None
    best_nace_codes: BestNaceCodes | None = None
    best_website: Website | None = None
    end_date: str | None = None
    is_nace_codes_corrected: bool = False


@dataclass(slots=True)
class Company:
    # A combination of country ISO code and country_company_id in format: BE_1234567890
    _id: str
    company_number: str | None = None  # Depends on the country, KVK number in NL, VAT in BE,...
    # If no emails are provided, it should be an empty list. This is crutial for the mongoDB queries.
    # If you would do `emails: list = []` it would be the same list for all instances of the class !
    # which is why we use `default_factory`. (Same for phones, websites, social_networks, nace_codes)
    emails: list[Email] = field(default_factory=list)
    phones: list[Phone] = field(default_factory=list)
    websites: list[Website] = field(default_factory=list)
    nace_codes: list[NaceCode] = field(default_factory=list)
    social_networks: list[SocialNetwork] = field(default_factory=list)
    country: Literal["BE", "FR", "NL"] = "BE"
    # Finance report data, we only have that for NL at the moment
    finance: Finance | None = None
    legal_situation: str | None = None
    status: str | None = None
    start_date: datetime | None = None
    entity_type: str | None = None  # (legal person, natural person, public,...)
    legal_form: str | None = None  # complete name of the legal form
    legal_form_code: str | None = None  # code of the legal form
    legal_form_type: str | None = None
    legal_form_last_update: str | None = None
    address: Address | None = None
    best_email: Email | None = None
    best_phone: Phone | None = None
    best_website: Website | None = None
    best_nace_codes: BestNaceCodes | None = None
    last_website_finding_date: datetime | None = None
    last_bce_update: datetime | None = None
    name: str | None = None
    name_fr: str | None = None
    name_nl: str | None = None
    name_de: str | None = None
    name_last_update: str | None = None
    number_of_establishments: int | None = None
    establishments: list[Establishment] | None = None
    end_date: datetime | None = None
    legal_situation_last_update: str | None = None
    board_members: list[BoardMember] | None = None
    is_nace_codes_corrected: bool | None = False
    employee_category_code: int | None = None
    employee_category_formatted: str | None = None
    description_id: int | None = None  # ID from the Typesense table (descriptions)
    last_processed_website: str | None = None  # Used for the websites_parser to detect websites changes
    declared_language: str | None = None


def convert_dict_to_company(company_dict: dict) -> Company:
    """Convert a dict to a Company object."""
    company_dict = _parse_datetime_fields(company_dict)
    # Handle nested establishments
    establishments = []
    if company_dict.get("establishments"):
        for establishment in company_dict["establishments"]:
            establishment = _parse_datetime_fields(establishment)
            if establishment.get("address"):
                address = Address(**establishment["address"])
            else:
                address = Address(source="BCE", last_update=None, last_seen=datetime.now())
            establishments.append(
                Establishment(
                    establishment_number=establishment["establishment_number"],
                    last_seen=establishment["last_seen"],
                    status=establishment.get("status"),
                    start_date=establishment.get("start_date"),
                    country=establishment.get("country", "BE"),
                    name=establishment.get("name"),
                    name_fr=establishment.get("name_fr"),
                    name_nl=establishment.get("name_nl"),
                    name_de=establishment.get("name_de"),
                    name_last_update=establishment.get("name_last_update"),
                    social_networks=[SocialNetwork(**sn) for sn in establishment.get("social_networks", []) or []],
                    address=Address(**establishment["address"]) if establishment.get("address") else address,
                    best_email=Email(**establishment["best_email"]) if establishment.get("best_email") else None,
                    emails=[Email(**email) for email in establishment.get("emails", []) or []],
                    best_phone=Phone(**establishment["best_phone"]) if establishment.get("best_phone") else None,
                    phones=[Phone(**phone) for phone in establishment.get("phones", []) or []],
                    best_website=Website(**establishment["best_website"])
                    if establishment.get("best_website")
                    else None,
                    websites=[Website(**website) for website in establishment.get("websites", []) or []],
                    end_date=establishment.get("end_date"),
                    nace_codes=[NaceCode(**nc) for nc in establishment.get("nace_codes", []) or []],
                    is_nace_codes_corrected=establishment.get("is_nace_codes_corrected", False),
                )
            )
    if company_dict.get("address"):
        address = Address(**company_dict["address"])
    else:
        address = Address(source="BCE", last_update=None, last_seen=datetime.now())
    return Company(
        _id=company_dict["_id"],
        company_number=company_dict["company_number"],
        description_id=company_dict["description_id"],
        country=company_dict.get("country", "BE"),
        status=company_dict.get("status"),
        start_date=company_dict.get("start_date"),
        finance=Finance(**company_dict["finance"]) if company_dict.get("finance") else None,
        entity_type=company_dict.get("entity_type"),
        legal_form=company_dict.get("legal_form"),
        legal_form_last_update=company_dict.get("legal_form_last_update"),
        legal_situation=company_dict.get("legal_situation"),
        legal_situation_last_update=company_dict.get("legal_situation_last_update"),
        address=address,
        best_email=Email(**company_dict["best_email"]) if company_dict.get("best_email") else None,
        emails=[Email(**email) for email in company_dict.get("emails", []) or []],
        best_phone=Phone(**company_dict["best_phone"]) if company_dict.get("best_phone") else None,
        phones=[Phone(**phone) for phone in company_dict.get("phones", []) or []],
        best_website=Website(**company_dict["best_website"]) if company_dict.get("best_website") else None,
        websites=[Website(**website) for website in company_dict.get("websites", []) or []],
        last_website_finding_date=company_dict.get("best_website"),
        name=company_dict.get("name"),
        name_fr=company_dict.get("name_fr"),
        name_nl=company_dict.get("name_nl"),
        name_de=company_dict.get("name_de"),
        name_last_update=company_dict.get("name_last_update"),
        number_of_establishments=company_dict.get("number_of_establishments"),
        establishments=establishments,
        nace_codes=[NaceCode(**nc) for nc in company_dict.get("nace_codes", []) or []],
        best_nace_codes=BestNaceCodes(
            first_best_nace_code=NaceCode(**company_dict["best_nace_codes"]["first_best_nace_code"])
            if company_dict["best_nace_codes"].get("first_best_nace_code")
            else None,
            second_best_nace_code=NaceCode(**company_dict["best_nace_codes"]["second_best_nace_code"])
            if company_dict["best_nace_codes"].get("second_best_nace_code")
            else None,
            third_best_nace_code=NaceCode(**company_dict["best_nace_codes"]["third_best_nace_code"])
            if company_dict["best_nace_codes"].get("third_best_nace_code")
            else None,
        )
        if company_dict.get("best_nace_codes")
        else None,
        is_nace_codes_corrected=company_dict.get("is_nace_codes_corrected", False),
        employee_category_code=company_dict.get("employee_category_code"),
        employee_category_formatted=company_dict.get("employee_category_formatted"),
        board_members=[BoardMember(**bm) for bm in company_dict.get("board_members", []) or []],
        end_date=company_dict.get("end_date"),
        social_networks=[SocialNetwork(**sn) for sn in company_dict.get("social_networks", []) or []],
        declared_language=company_dict.get("declared_language", None),
    )


def _parse_datetime_fields(entity: dict) -> dict:
    """
    Parse datetime fields to ensure they are in the right format.

    Sometime we have to loose the timedate format for json serialization purpose. This fixes it.
    """
    field_nested_items_with_last_seen = ["websites", "emails", "phones", "social_networks"]
    for date_field in field_nested_items_with_last_seen:
        entity_item_list = entity.get(date_field)
        if not entity_item_list:
            continue
        for i, item in enumerate(entity_item_list):
            if isinstance(item["last_seen"], str):
                entity[date_field][i]["last_seen"] = pendulum.parse(item["last_seen"], strict=False)  # type: ignore
            if isinstance(item.get("last_update"), str):
                entity[date_field][i]["last_update"] = pendulum.parse(item["last_update"], strict=False)  # type: ignore

    fields_datetime = ["start_date", "last_website_finding_date", "end_date", "name_last_update", "last_seen"]
    for date_field in fields_datetime:
        if isinstance(entity.get(date_field), str):
            entity[date_field] = pendulum.parse(entity[date_field], strict=False)  # type: ignore
    return entity
