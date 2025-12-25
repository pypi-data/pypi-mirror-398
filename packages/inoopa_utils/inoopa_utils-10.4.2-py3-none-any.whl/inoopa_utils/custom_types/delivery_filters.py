import json
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from inoopa_utils.custom_types import DecisionMakerDepartment
from inoopa_utils.custom_types.addresses import (
    Country,
    ProvinceBe,
    ProvinceFr,
    ProvinceNl,
    RegionBe,
    RegionFr,
    RegionNl,
)
from inoopa_utils.custom_types.legal_filters import EmployeeCategoryClass, EntityType, LegalFormBe, LegalFormNl, LegalFormCategory

MongoFilters = dict[str, dict[str, dict[str, int | str | list[str]]]]

AdditionalFields = Literal[
    "email",
    "phone",
    "website",
    "nace_codes",
    "social_medias",
    "decision_makers_name",
    "decision_makers_email",
    "board_members",
]


class LeadGenerationCompanyFilters(BaseModel):
    """
    Represents the filters used to generate the leads.

    This is a pydantic model, so it can be used in the apis as a parameter.
    """

    additional_fields: list[AdditionalFields] | None = [
        "email",
        "phone",
        "website",
        "nace_codes",
        "social_medias",
        "decision_makers_name",
        "decision_makers_email",
        "board_members",
    ]

    countries: list[Country] | None = None
    regions: list[RegionBe | RegionFr | RegionNl] | None = None
    provinces: list[ProvinceBe | ProvinceFr | ProvinceNl] | None = None
    zipcodes: list[str] | None = None
    declared_nace_codes: list[str] | None = None
    declared_nace_codes_inclusive: list[str] | None = None
    best_nace_codes: list[str] | None = None
    best_nace_codes_inclusive: list[str] | None = None

    minimum_number_of_establishments: int | None = None
    maximum_number_of_establishments: int | None = None
    employee_categories: list[EmployeeCategoryClass] | None = None
    created_before: datetime | None = None
    created_after: datetime | None = None

    max_results: int | None = None
    max_decision_makers_per_company: int | None = None
    decision_makers_department_allowed: list[DecisionMakerDepartment] | None = None
    decision_makers_department_priority: list[DecisionMakerDepartment] | None = None
    excluded_companies: list[str] | None = None

    legal_form_Categories: list[LegalFormCategory] | None = None
    legal_forms: list[LegalFormBe | LegalFormNl] | None = None
    entity_types: list[EntityType] | None = None

    only_include_active_companies: bool = True
    only_include_companies_with_phone_no_do_not_call_me: bool = False
    only_include_companies_with_email: bool = False
    only_include_companies_with_website: bool = False
    only_include_companies_with_nace_codes: bool = False

    def to_mongo_filters(self) -> MongoFilters:
        """
        Generate a MongoDB filter to search for companies based on the LeadGenerationCompanyFilters.

        can be used as a filter parameter in the MongoDB Collection.find() method.
        """
        filters = {}
        if self.countries:
            filters["country"] = {"$in": [c.value for c in self.countries]}
        if self.legal_forms:
            filters["legal_form"] = {"$in": [form.value for form in self.legal_forms]}
        if self.employee_categories:
            filters["employee_category_formatted"] = {"$in": [c.value for c in self.employee_categories]}
        if self.regions:
            regions = [r.value if r.value != RegionBe.not_found.value else None for r in self.regions]
            filters["address.region"] = {"$in": regions}
        if self.provinces:
            provinces = [p.value if p.value != ProvinceBe.not_found.value else None for p in self.provinces]
            filters["address.province"] = {"$in": provinces}
        if self.zipcodes:
            zipcodes = [z if z != "NOT FOUND" else None for z in self.zipcodes]
            filters["address.postal_code"] = {"$in": zipcodes}

        if self.minimum_number_of_establishments and self.maximum_number_of_establishments:
            filters["number_of_establishments"] = {
                "$gte": self.minimum_number_of_establishments,
                "$lte": self.maximum_number_of_establishments,
            }
        elif self.minimum_number_of_establishments:
            filters["number_of_establishments"] = {"$gte": self.minimum_number_of_establishments}
        elif self.maximum_number_of_establishments:
            filters["number_of_establishments"] = {"$lte": self.maximum_number_of_establishments}

        if self.declared_nace_codes:
            filters["$or"] = [
                {"nace_codes": {"$elemMatch": {"number": {"$in": self.declared_nace_codes}}}},
                {
                    "establishments": {
                        "$elemMatch": {"nace_codes": {"$elemMatch": {"number": {"$in": self.declared_nace_codes}}}}
                    }
                },
            ]
        if self.declared_nace_codes_inclusive:
            nace_section_codes = []
            nace_codes_regex = []
            for code in self.declared_nace_codes_inclusive:
                # if the regex is only one letter, it's a nace section code
                if len(code) == 1:
                    nace_section_codes.append(code)
                else:
                    # if the regex is more than one letter, it's a nace code regex
                    nace_codes_regex.append(f"^{code}.*")

            filters["$or"] = []
            if nace_codes_regex:
                filters["$or"].append(
                    {"nace_codes": {"$elemMatch": {"number": {"$regex": "|".join(nace_codes_regex)}}}}
                )
                filters["$or"].append(
                    {
                        "establishments": {
                            "$elemMatch": {
                                "nace_codes": {"$elemMatch": {"number": {"$regex": "|".join(nace_codes_regex)}}}
                            }
                        }
                    },
                )
            if nace_section_codes:
                filters["$or"].append({"nace_codes": {"$elemMatch": {"section_code": {"$in": nace_section_codes}}}})
                filters["$or"].append(
                    {
                        "establishments": {
                            "$elemMatch": {"nace_codes": {"$elemMatch": {"section_code": {"$in": nace_section_codes}}}}
                        }
                    },
                )

        if self.best_nace_codes:
            filters["best_nace_codes.first_best_nace_code.number"] = {"$in": self.best_nace_codes}
        if self.best_nace_codes_inclusive:
            nace_codes = []
            nace_section_codes = []
            for code_regex in self.best_nace_codes_inclusive:
                # if the regex is only one letter, it's a nace section code
                if len(code_regex) == 1:
                    nace_section_codes.append(code_regex)
                else:
                    # if the regex is more than one letter, it's a nace code regex
                    nace_codes.append(f"^{code_regex}.*")
            filters["$or"] = []
            if nace_codes:
                filters["$or"].append({"best_nace_codes.first_best_nace_code.number": {"$regex": "|".join(nace_codes)}})
            if nace_section_codes:
                filters["$or"].append(
                    {"best_nace_codes.first_best_nace_code.section_code": {"$in": nace_section_codes}}
                )

        if self.legal_form_Categories:
            filters["legal_form_type"] = {"$in": [c.value for c in self.legal_form_Categories]}
        if self.entity_types:
            filters["entity_type"] = {"$in": [e.value for e in self.entity_types]}
        if self.created_before and not self.created_after:
            filters["start_date"] = {"$lte": self.created_before}
        if self.created_after and not self.created_before:
            filters["start_date"] = {"$gte": self.created_after}
        if self.created_before and self.created_after:
            filters["start_date"] = {"$lte": self.created_before, "$gte": self.created_after}
        if self.excluded_companies:
            filters["_id"] = {"$nin": self.excluded_companies}
        if self.only_include_active_companies:
            filters["status"] = "Active"
            filters["legal_situation"] = "Normal situation"

        if self.only_include_companies_with_phone_no_do_not_call_me:
            filters["best_phone"] = {"$ne": None}
            filters["best_phone.phone"] = {"$nin": ["DO_NOT_CALL_ME", None]}

        if self.only_include_companies_with_email:
            filters["best_email"] = {"$ne": None}
        if self.only_include_companies_with_website:
            filters["best_website"] = {"$ne": None}
        if self.only_include_companies_with_nace_codes:
            filters["best_nace_codes"] = {"$ne": None}
        return filters

    def to_dict(self) -> dict:
        data_dict = self.model_dump()
        # Convert datetime objects to isoformat for json serialization
        if self.created_before:
            data_dict["created_before"] = _datetime_serializer(self.created_before)
        if self.created_after:
            data_dict["created_after"] = _datetime_serializer(self.created_after)
        return data_dict

    def to_hash(self, semantic_search_query: str | None = None) -> int:
        """Hash the filters to allow comparing."""
        hashable_dict = {
            "minimum_number_of_establishments": self.minimum_number_of_establishments,
            "maximum_number_of_establishments": self.maximum_number_of_establishments,
            "max_results": self.max_results,
            "created_before": self.created_before.__str__() if self.created_before else None,
            "created_after": self.created_after.__str__() if self.created_after else None,
            "max_decision_makers_per_company": self.max_decision_makers_per_company,

            # Sort all lists to get a similar hash for similar requests
            "zipcodes": sorted(self.zipcodes) if self.zipcodes else None,
            "declared_nace_codes": sorted(self.declared_nace_codes) if self.declared_nace_codes else None,
            "declared_nace_codes_inclusive": sorted(self.declared_nace_codes_inclusive)
            if self.declared_nace_codes_inclusive
            else None,
            "best_nace_codes": sorted(self.best_nace_codes) if self.best_nace_codes else None,
            "best_nace_codes_inclusive": sorted(self.best_nace_codes_inclusive)
            if self.best_nace_codes_inclusive
            else None,
            "excluded_companies": sorted(self.excluded_companies) if self.excluded_companies else None,
            "countries": sorted([v.value for v in self.countries]) if self.countries else None,
            "employee_categories": sorted([v.value for v in self.employee_categories])
            if self.employee_categories
            else None,
            "legal_form_Categories": sorted([v.value for v in self.legal_form_Categories])
            if self.legal_form_Categories
            else None,
            "entity_types": sorted([v.value for v in self.entity_types]) if self.entity_types else None,
            "legal_forms": sorted([v.value for v in self.legal_forms]) if self.legal_forms else None,
            "regions": sorted([v.value for v in self.regions]) if self.regions else None,
            "provinces": sorted([v.value for v in self.provinces]) if self.provinces else None,
            "decision_makers_department_allowed": sorted([v.value for v in self.decision_makers_department_allowed])
            if self.decision_makers_department_allowed
            else None,

            # ! This one requires following the user's order
            "decision_makers_department_priority": [v.value for v in self.decision_makers_department_priority]
            if self.decision_makers_department_priority
            else None,

            "only_include_active_companies": self.only_include_active_companies,
            "only_include_companies_with_phone_no_do_not_call_me": self.only_include_companies_with_phone_no_do_not_call_me,
            "only_include_companies_with_email": self.only_include_companies_with_email,
            "only_include_companies_with_website": self.only_include_companies_with_website,
            "only_include_companies_with_nace_codes": self.only_include_companies_with_nace_codes,
        }
        dict_str_dump = json.dumps(hashable_dict, sort_keys=True, default=str, ensure_ascii=False)
        if semantic_search_query:
            dict_str_dump += semantic_search_query.strip().lower()
        return hash(dict_str_dump)


class EnrichmentCompanyFilters(BaseModel):
    vats_to_enrich: list[str]

    only_include_active_companies: bool = True
    only_include_companies_with_phone_no_do_not_call_me: bool = False
    only_include_companies_with_email: bool = False
    only_include_companies_with_website: bool = False
    only_include_companies_with_nace_codes: bool = False

    additional_fields: list[AdditionalFields] = [
        "email",
        "phone",
        "website",
        "nace_codes",
        "social_medias",
        "decision_makers_name",
        "decision_makers_email",
        "board_members",
    ]

    def to_mongo_filters(self) -> MongoFilters:
        filters: dict = {"_id": {"$in": self.vats_to_enrich}}
        if self.only_include_active_companies:
            filters["status"] = "Active"
            filters["legal_situation"] = "Normal situation"
        if self.only_include_companies_with_phone_no_do_not_call_me:
            filters["best_phone"] = {"$ne": None}
        if self.only_include_companies_with_email:
            filters["best_email"] = {"$ne": None}
        if self.only_include_companies_with_website:
            filters["best_website"] = {"$ne": None}
        if self.only_include_companies_with_nace_codes:
            filters["best_nace_codes"] = {"$ne": None}
        return filters

    def to_dict(self) -> dict:
        return self.model_dump()

    def to_hash(self) -> int:
        """Hash the filters to allow comparing."""
        dict_str_dump = json.dumps(self.model_dump(), sort_keys=True, default=str, ensure_ascii=False)
        return hash(dict_str_dump)

def _datetime_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")
