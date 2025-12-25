from enum import Enum

from inoopa_utils.custom_types.addresses import Country


class EmployeeCategoryClass(Enum):
    class_0_employees = "0 employees"
    class_1_to_4_employees = "1 to 4 employees"
    class_5_to_9_employees = "5 to 9 employees"
    class_10_to_19_employees = "10 to 19 employees"
    class_20_to_49_employees = "20 to 49 employees"
    class_50_to_99_employees = "50 to 99 employees"
    class_100_to_199_employees = "100 to 199 employees"
    class_200_to_499_employees = "200 to 499 employees"
    class_500_to_999_employees = "500 to 999 employees"
    class_1000_to_9999999_employees = "1000 to 9999999 employees"
    not_found = "NOT FOUND"

    @classmethod
    def get_all_values(cls):
        """Return all possible values for this enum as a list of enum."""
        return [v for v in cls.__dict__.values() if isinstance(v, cls)]

    @classmethod
    def get_all_values_str(cls) -> list[str]:
        """Return all possible values for this enum as a list of str."""
        return [v.value for v in cls.__dict__.values() if isinstance(v, cls)]


class EntityType(Enum):
    legal_person = "legal person"
    natural_person = "natural person"

    @classmethod
    def get_all_values(cls):
        """Return all possible values for this enum as a list of enum."""
        return [v for v in cls.__dict__.values() if isinstance(v, cls)]

    @classmethod
    def get_all_values_str(cls) -> list[str]:
        """Return all possible values for this enum as a list of str."""
        return [v.value for v in cls.__dict__.values() if isinstance(v, cls)]


class LegalFormCategory(Enum):
    for_profit = "for-profit"
    non_profit = "non-profit"
    public = "public"

    @classmethod
    def get_all_values(cls):
        """Return all possible values for this enum as a list of enum."""
        return [v for v in cls.__dict__.values() if isinstance(v, cls)]

    @classmethod
    def get_all_values_str(cls) -> list[str]:
        """Return all possible values for this enum as a list of str."""
        return [v.value for v in cls.__dict__.values() if isinstance(v, cls)]


class LegalFormBe(Enum):
    agricultural_company = "Agricultural company"
    autonomous_municipal_company = "Autonomous municipal company"
    autonomous_provincial_company = "Autonomous provincial company"
    brussels_capital_region_authority = "Brussels-Capital region authority"
    cpas_ocmw_association = "CPAS / OCMW Association"
    cities_and_municipalities = "Cities and municipalities"
    co_ownership_association = "Co-ownership association"
    common_law_company = "Common law company"
    company_or_association_without_legal_personality = "Company or association without legal personality"
    congolese_company = "Congolese company"
    cooperative_society = "Cooperative society"
    cooperative_society_old_regime = "Cooperative society (old regime)"
    cooperative_society_governed_by_public_law = "Cooperative society governed by public law"
    cooperative_society_governed_by_public_law_old_regime = "Cooperative society governed by public law (old regime)"
    cooperative_society_with_limited_liability = "Cooperative society with limited liability"
    cooperative_society_with_limited_liability_profit_share = (
        "Cooperative society with limited liability (profit share)"
    )
    cooperative_society_with_limited_liability_and_a_social_objective = (
        "Cooperative society with limited liability and a social objective"
    )
    cooperative_society_with_limited_liability_governed_by_public_law = (
        "Cooperative society with limited liability governed by public law"
    )
    cooperative_society_with_unlimited_liability = "Cooperative society with unlimited liability"
    cooperative_society_with_unlimited_liability_profit_share = (
        "Cooperative society with unlimited liability (profit share)"
    )
    cooperative_society_with_unlimited_liability_and_a_social_objective = (
        "Cooperative society with unlimited liability and a social objective"
    )
    economic_interest_grouping_with_a_social_objective = "Economic interest grouping with a social objective"
    economic_interest_grouping_with_registered_seat_in_belgium = (
        "Economic interest grouping with registered seat in Belgium"
    )
    europ_econ_assoc_wo_regseat_but_with_est_unit_in_belgium = (
        "Europ. Econ. assoc wo reg.seat but with est. unit in Belgium"
    )
    european_company_societas_europaea = "European company (Societas Europaea)"
    european_cooperative_society = "European cooperative society"
    european_economic_assoc_with_registered_seat_in_belgium = "European economic assoc with registered seat in Belgium"
    european_political_foundation = "European political foundation"
    european_political_party = "European political party"
    federal_public_planning_service = "Federal public planning service"
    federal_public_service = "Federal public service"
    flemish_region_and_flemish_community_authority = "Flemish region and Flemish community authority"
    foreign_ent_with_property_in_belgium_without_legal_pers = (
        "Foreign ent. with property in Belgium (without legal pers.)"
    )
    foreign_entity = "Foreign entity"
    foreign_entity_with_property_in_belgium_with_legal_personality = (
        "Foreign entity with property in Belgium (with legal personality)"
    )
    foreign_entity_without_belgian_establishment_unit_with_vat_representation = (
        "Foreign entity without Belgian establishment unit with VAT representation"
    )
    foreign_listed_company_without_belgian_establishment_unit = (
        "Foreign listed company without Belgian establishment unit"
    )
    foreign_or_international_public_organisations = "Foreign or international public organisations"
    french_community_authority = "French community authority"
    general_partnership = "General partnership"
    general_partnership_with_a_social_objective = "General partnership with a social objective"
    german_speaking_community_authority = "German-speaking community authority"
    health_fund_mutual_health_insurance_national_union_of_health_funds = (
        "Health fund / Mutual health insurance / National union of health funds"
    )
    hulpverleningszone = "Hulpverleningszone"
    intercommunal = "Intercommunal"
    international_non_profit_association = "International non-profit association"
    international_non_profit_association_governed_by_public_law = (
        "International non-profit association governed by public law"
    )
    international_scientific_organisation_under_belgian_law = "International scientific organisation under Belgian law"
    limited_partnership = "Limited partnership"
    limited_partnership_governed_by_public_law = "Limited partnership governed by public Law"
    local_police = "Local police"
    ministry_for_middle_class = "Ministry for Middle Class"
    ministry_of_economic_affairs = "Ministry of Economic Affairs"
    ministry_of_foreign_affairs = "Ministry of Foreign Affairs"
    ministry_of_home_affairs = "Ministry of Home Affairs"
    ministry_of_justice = "Ministry of Justice"
    ministry_of_the_brussels_capital_region = "Ministry of the Brussels-Capital Region"
    ministry_of_the_flemish_community = "Ministry of the Flemish Community"
    ministry_of_the_french_community = "Ministry of the French Community"
    ministry_of_the_walloon_region = "Ministry of the Walloon Region"
    miscellaneous = "Miscellaneous"
    miscellaneous_without_legal_personality = "Miscellaneous without legal personality"
    non_profit_institution = "Non-profit institution"
    non_profit_organisation = "Non-profit organisation"
    ordinary_limited_partnership = "Ordinary limited partnership"
    ordinary_limited_partnership_with_a_social_objective = "Ordinary limited partnership with a social objective"
    organis_regist_with_the_public_admin_pensions_finance = "Organis. regist. with the public admin. Pensions (Finance)"
    organisations_registered_with_the_onp = "Organisations registered with the O.N.P"
    other_federal_services = "Other federal services"
    other_institution_with_a_social_objective_public = "Other institution with a social objective (public)"
    other_legal_form = "Other legal form"
    other_private_organisation_with_legal_personality = "Other private organisation with legal personality"
    partnership_limited_by_shares = "Partnership limited by shares"
    partnership_limited_by_shares_with_a_social_objective = "Partnership limited by shares with a social objective"
    pawnshop = "Pawnshop"
    pension_scheme_organisation = "Pension scheme organisation"
    polders_and_water_boards = "Polders and water boards"
    private_foreign_association_with_establishment_in_belgium = (
        "Private foreign association with establishment in Belgium"
    )
    private_foundation = "Private foundation"
    private_limited_company = "Private limited company"
    private_limited_company_governed_by_public_law = "Private limited company governed by public law"
    private_limited_liability_company = "Private limited liability company"
    private_limited_liability_company_with_a_social_objective = (
        "Private limited liability company with a social objective"
    )
    private_mutual_insurance_fund = "Private mutual insurance fund"
    professional_corporations_orders = "Professional corporations - Orders"
    professional_union = "Professional union"
    project_association = "Project association"
    provincial_authority = "Provincial authority"
    pubic_social_action_centre = "Pubic social action centre"
    public_institution = "Public institution"
    public_limited_company = "Public limited company"
    public_limited_company_with_a_social_objective = "Public limited company with a social objective"
    public_non_profit_association = "Public non-profit association"
    public_utility_foundation = "Public utility foundation"
    public_utility_institution = "Public utility institution"
    representative_association_flemish_region = "Representative association (Flemish region)"
    service_provider_association_flemish_region = "Service provider association (Flemish region)"
    state_province_region_community = "State, Province, Region, Community"
    temporary_association = "Temporary association"
    the_services_of_the_prime_minister = "The services of the Prime Minister"
    trade_union = "Trade union"
    unkown_legal_form_nsso = "Unkown legal form (NSSO)"
    vat_group = "VAT-group"
    walloon_region_authorit = "Walloon region authorit"
    walloon_region_authority = "Walloon region authority"

    @classmethod
    def get_all_values(cls):
        """Return all possible values for this enum as a list of enum."""
        return [v for v in cls.__dict__.values() if isinstance(v, cls)]

    @classmethod
    def get_all_values_str(cls) -> list[str]:
        """Return all possible values for this enum as a list of str."""
        return [v.value for v in cls.__dict__.values() if isinstance(v, cls)]


class LegalFormNl(Enum):
    """"""

    @classmethod
    def get_all_values(cls):
        """Return all possible values for this enum as a list of enum."""
        return [v for v in cls.__dict__.values() if isinstance(v, cls)]

    @classmethod
    def get_all_values_str(cls) -> list[str]:
        """Return all possible values for this enum as a list of str."""
        return [v.value for v in cls.__dict__.values() if isinstance(v, cls)]

    Sole_Proprietorship = "Sole Proprietorship"
    Civil_law_partnership = "Civil-law partnership"
    Partnership_firm = "Partnership firm"
    Limited_partnership = "Limited partnership"
    Private_limited_company = "Private limited company"
    Limited_company = "Limited company"
    Cooperative_association = "Cooperative association"
    Association = "Association"
    Foundation = "Foundation"
    Mutual_insurance_association = "Mutual insurance association"
    Foreign_legal_form_branch_of_a_foreign_company = "Foreign legal form (branch of a foreign company)"
    Shipping_company = "Shipping company"
    European_economical_cooperative_organisation = "European economical cooperative organisation"
    Church = "Church"
    Legal_entity_in_formation = "Legal entity in formation"
    Public_partnership = "Public partnership"
    Eropean_limited_company = "Eropean limited company"
    Owners_association = "Owners' association"
    Legal_entity_under_public_law = "Legal entity under public law"
    Legal_entity_under_private_law = "Legal entity under private law"
    Body_governed_by_public_law = "Body governed by public law"
    European_limited_company = "European limited company"


class LegalFormFr(Enum):
    def __new__(cls, value):
        raise NotImplementedError("FR legal forms not implemented yet")

    @classmethod
    def get_all_values(cls):
        """Return all possible values for this enum as a list of enum."""
        return [v for v in cls.__dict__.values() if isinstance(v, cls)]

    @classmethod
    def get_all_values_str(cls) -> list[str]:
        """Return all possible values for this enum as a list of str."""
        return [v.value for v in cls.__dict__.values() if isinstance(v, cls)]


def get_all_legal_forms(countries: list[Country] | list[str]) -> list[LegalFormBe | LegalFormFr | LegalFormNl]:
    """Get all legal forms for a list of countries. Countries can be a list of Country enums or a list of str."""
    all_legal_forms = []
    if not countries:
        return all_legal_forms

    if isinstance(countries[0], str):
        countries = [Country(country) for country in countries]

    for country in countries:
        if country == Country.belgium:
            all_legal_forms.extend(LegalFormBe.get_all_values())
        elif country == Country.france:
            all_legal_forms.extend(LegalFormFr.get_all_values())
        elif country == Country.netherlands:
            all_legal_forms.extend(LegalFormNl.get_all_values())
        else:
            raise ValueError(f"Unknown country: `{country}`")

    return all_legal_forms


def get_all_legal_forms_str(countries: list[Country] | list[str]) -> list[str]:
    """Get all legal forms for a list of countries. Countries can be a list of Country enums or a list of str."""
    all_legal_forms = []
    if not countries:
        return all_legal_forms

    if isinstance(countries[0], str):
        countries = [Country(country) for country in countries]

    for country in countries:
        if country == Country.belgium:
            all_legal_forms.extend(LegalFormBe.get_all_values_str())
        elif country == Country.france:
            all_legal_forms.extend(LegalFormFr.get_all_values_str())
        elif country == Country.netherlands:
            all_legal_forms.extend(LegalFormNl.get_all_values_str())
        else:
            raise ValueError(f"Unknown country: `{country}`")

    return all_legal_forms
