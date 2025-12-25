from dataclasses import dataclass
from datetime import datetime

from inoopa_utils.custom_types.addresses import Country

# Map employee_categories codes with their labels
EMPLOYEE_CATEGORIES_CODES_MAP: dict[int | None, str] = {
    0: "emp_0",
    1: "emp_1_to_4",
    2: "emp_5_to_9",
    3: "emp_10_to_19",
    4: "emp_20_to_49",
    5: "emp_50_to_99",
    6: "emp_100_to_199",
    7: "emp_200_to_499",
    8: "emp_500_to_999",
    9: "emp_1000_plus",
    None: "unknown",
}


@dataclass(slots=True)
class PerEmployeeCategory:
    """Hold the counting of a metric."""

    total: int | None = None
    distinct: int | None = None
    emp_0: int = 0
    emp_1_to_4: int = 0
    emp_5_to_9: int = 0
    emp_10_to_19: int = 0
    emp_20_to_49: int = 0
    emp_50_to_99: int = 0
    emp_100_to_199: int = 0
    emp_200_to_499: int = 0
    emp_500_to_999: int = 0
    emp_1000_plus: int = 0
    unknown: int = 0


@dataclass(slots=True)
class CompanyStats:
    """
    Hold the metrics of our company collection at a given point in time.
    Each metric is divided by employee category.
    """

    date: datetime
    country: Country
    active_companies: PerEmployeeCategory
    websites: PerEmployeeCategory
    emails: PerEmployeeCategory
    phones: PerEmployeeCategory
    attributed_phones: PerEmployeeCategory


@dataclass(slots=True)
class DecisionMakersStats:
    """
    Hold the stats of the decision_makers collection at a given point in time.
    Each metric is divided by employee category.
    Each metric has a _dm version that counts unique decision makers.
    Each metric has a _companies version that counts unique companies with at least 1 matching DM.
    """

    date: datetime
    country: Country
    with_name_dms: PerEmployeeCategory
    with_job_title_dms: PerEmployeeCategory
    with_department_dms: PerEmployeeCategory
    with_responsibility_level_dms: PerEmployeeCategory
    with_linkedin_url_dms: PerEmployeeCategory
    with_email_dms: PerEmployeeCategory
    with_name_companies: PerEmployeeCategory
    with_job_title_companies: PerEmployeeCategory
    with_department_companies: PerEmployeeCategory
    with_responsibility_level_companies: PerEmployeeCategory
    with_linkedin_url_companies: PerEmployeeCategory
    with_email_companies: PerEmployeeCategory
    board_members: PerEmployeeCategory
    board_members_companies: PerEmployeeCategory


@dataclass(slots=True)
class DecisionMakersDepartmentStats:
    """
    Hold the stats of the decision_makers collection per department at a given point in time.
    Each metric is divided by employee category.
    Each metric has a _dm version that counts unique decision makers.
    """

    date: datetime
    country: Country
    from_it_dms: PerEmployeeCategory
    from_it_dms_with_emails: PerEmployeeCategory
    from_sales_dms: PerEmployeeCategory
    from_sales_dms_with_emails: PerEmployeeCategory
    from_legal_dms: PerEmployeeCategory
    from_legal_dms_with_emails: PerEmployeeCategory
    from_finance_dms: PerEmployeeCategory
    from_finance_dms_with_emails: PerEmployeeCategory
    from_board_dms: PerEmployeeCategory
    from_board_dms_with_emails: PerEmployeeCategory
    from_logistic_dms: PerEmployeeCategory
    from_logistic_dms_with_emails: PerEmployeeCategory
    from_hr_dms: PerEmployeeCategory
    from_hr_dms_with_emails: PerEmployeeCategory
    from_support_dms: PerEmployeeCategory
    from_support_dms_with_emails: PerEmployeeCategory
    from_esg_dms: PerEmployeeCategory
    from_esg_dms_with_emails: PerEmployeeCategory
    from_administration_dms: PerEmployeeCategory
    from_administration_dms_with_emails: PerEmployeeCategory
    from_project_management_dms: PerEmployeeCategory
    from_project_management_dms_with_emails: PerEmployeeCategory
    from_notworking_dms: PerEmployeeCategory
    from_notworking_dms_with_emails: PerEmployeeCategory
    from_other_dms: PerEmployeeCategory
    from_other_dms_with_emails: PerEmployeeCategory


@dataclass(slots=True)
class NaceMetricForEmployeeCategory:
    """
    Hold the distribution of companies per sector (lvl 1 NACE) or per code (any lvl)

    Both will get a dict like: {nace_level: number_of_companies}
    ex: {"12": 333} -> "12" is the nace code, "333" is the number of companies having this code as first best NACE
    """

    per_sector: dict[str, int]  # Level 1
    per_code: dict[str, int]  # Any level


@dataclass(slots=True)
class NaceStats:
    """
    Hold the metrics of country's NACE.
    Each metric is divided by employee category.
    """

    date: datetime
    country: Country
    total: NaceMetricForEmployeeCategory
    emp_0: NaceMetricForEmployeeCategory
    emp_1_to_4: NaceMetricForEmployeeCategory
    emp_5_to_9: NaceMetricForEmployeeCategory
    emp_10_to_19: NaceMetricForEmployeeCategory
    emp_20_to_49: NaceMetricForEmployeeCategory
    emp_50_to_99: NaceMetricForEmployeeCategory
    emp_100_to_199: NaceMetricForEmployeeCategory
    emp_200_to_499: NaceMetricForEmployeeCategory
    emp_500_to_999: NaceMetricForEmployeeCategory
    emp_1000_plus: NaceMetricForEmployeeCategory


def dict_to_nace_stats(nace_stats: dict) -> NaceStats:
    """Convert a dict from the DB to a NaceStats dataclass."""
    return NaceStats(
        date=nace_stats["date"],
        country=Country(nace_stats["country"]),
        total=NaceMetricForEmployeeCategory(**nace_stats["total"]),
        emp_0=NaceMetricForEmployeeCategory(**nace_stats["emp_0"]),
        emp_1_to_4=NaceMetricForEmployeeCategory(**nace_stats["emp_1_to_4"]),
        emp_5_to_9=NaceMetricForEmployeeCategory(**nace_stats["emp_5_to_9"]),
        emp_10_to_19=NaceMetricForEmployeeCategory(**nace_stats["emp_10_to_19"]),
        emp_20_to_49=NaceMetricForEmployeeCategory(**nace_stats["emp_20_to_49"]),
        emp_50_to_99=NaceMetricForEmployeeCategory(**nace_stats["emp_50_to_99"]),
        emp_100_to_199=NaceMetricForEmployeeCategory(**nace_stats["emp_100_to_199"]),
        emp_200_to_499=NaceMetricForEmployeeCategory(**nace_stats["emp_200_to_499"]),
        emp_500_to_999=NaceMetricForEmployeeCategory(**nace_stats["emp_500_to_999"]),
        emp_1000_plus=NaceMetricForEmployeeCategory(**nace_stats["emp_1000_plus"]),
    )


def dict_to_company_stats(company_stats: dict) -> CompanyStats:
    """Convert a dict from the DB to a CompanyStats dataclass."""
    company_stats_fmt = CompanyStats(
        date=company_stats["date"],
        country=Country(company_stats["country"]),
        active_companies=PerEmployeeCategory(**company_stats["active_companies"]),
        websites=PerEmployeeCategory(**company_stats["websites"]),
        phones=PerEmployeeCategory(**company_stats["phones"]),
        emails=PerEmployeeCategory(**company_stats["emails"]),
        attributed_phones=PerEmployeeCategory(**company_stats["attributed_phones"]),
    )
    return company_stats_fmt


def dict_to_decision_makers_stats(decision_makers_stats: dict) -> DecisionMakersStats:
    """Convert a dict from the DB to a DecisionMakersStats dataclass."""
    decision_makers_stats_fmt = DecisionMakersStats(
        date=decision_makers_stats["date"],
        country=Country(decision_makers_stats["country"]),
        with_name_dms=PerEmployeeCategory(**decision_makers_stats["with_name_dms"]),
        with_job_title_dms=PerEmployeeCategory(**decision_makers_stats["with_job_title_dms"]),
        with_department_dms=PerEmployeeCategory(**decision_makers_stats["with_department_dms"]),
        with_responsibility_level_dms=PerEmployeeCategory(**decision_makers_stats["with_responsibility_level_dms"]),
        with_linkedin_url_dms=PerEmployeeCategory(**decision_makers_stats["with_linkedin_url_dms"]),
        with_email_dms=PerEmployeeCategory(**decision_makers_stats["with_email_dms"]),
        with_name_companies=PerEmployeeCategory(**decision_makers_stats["with_name_companies"]),
        with_job_title_companies=PerEmployeeCategory(**decision_makers_stats["with_job_title_companies"]),
        with_department_companies=PerEmployeeCategory(**decision_makers_stats["with_department_companies"]),
        with_responsibility_level_companies=PerEmployeeCategory(
            **decision_makers_stats["with_responsibility_level_companies"]
        ),
        with_linkedin_url_companies=PerEmployeeCategory(**decision_makers_stats["with_linkedin_url_companies"]),
        with_email_companies=PerEmployeeCategory(**decision_makers_stats["with_email_companies"]),
        board_members=PerEmployeeCategory(**decision_makers_stats["board_members"]),
        board_members_companies=PerEmployeeCategory(**decision_makers_stats["board_members_companies"]),
    )
    return decision_makers_stats_fmt


def dict_to_decision_makers_departments_stats(decision_makers_stats: dict) -> DecisionMakersDepartmentStats:
    """Convert a dict from the DB to a DecisionMakersDepartmentStats dataclass."""
    decision_makers_stats_fmt = DecisionMakersDepartmentStats(
        date=decision_makers_stats["date"],
        country=Country(decision_makers_stats["country"]),
        from_it_dms=PerEmployeeCategory(**decision_makers_stats["from_it_dms"]),
        from_it_dms_with_emails=PerEmployeeCategory(**decision_makers_stats["from_it_dms_with_emails"]),
        from_sales_dms=PerEmployeeCategory(**decision_makers_stats["from_sales_dms"]),
        from_sales_dms_with_emails=PerEmployeeCategory(**decision_makers_stats["from_sales_dms_with_emails"]),
        from_legal_dms=PerEmployeeCategory(**decision_makers_stats["from_legal_dms"]),
        from_legal_dms_with_emails=PerEmployeeCategory(**decision_makers_stats["from_legal_dms_with_emails"]),
        from_finance_dms=PerEmployeeCategory(**decision_makers_stats["from_finance_dms"]),
        from_finance_dms_with_emails=PerEmployeeCategory(**decision_makers_stats["from_finance_dms_with_emails"]),
        from_board_dms=PerEmployeeCategory(**decision_makers_stats["from_board_dms"]),
        from_board_dms_with_emails=PerEmployeeCategory(**decision_makers_stats["from_board_dms_with_emails"]),
        from_logistic_dms=PerEmployeeCategory(**decision_makers_stats["from_logistic_dms"]),
        from_logistic_dms_with_emails=PerEmployeeCategory(**decision_makers_stats["from_logistic_dms_with_emails"]),
        from_hr_dms=PerEmployeeCategory(**decision_makers_stats["from_hr_dms"]),
        from_hr_dms_with_emails=PerEmployeeCategory(**decision_makers_stats["from_hr_dms_with_emails"]),
        from_support_dms=PerEmployeeCategory(**decision_makers_stats["from_support_dms"]),
        from_support_dms_with_emails=PerEmployeeCategory(**decision_makers_stats["from_support_dms_with_emails"]),
        from_esg_dms=PerEmployeeCategory(**decision_makers_stats["from_esg_dms"]),
        from_esg_dms_with_emails=PerEmployeeCategory(**decision_makers_stats["from_esg_dms_with_emails"]),
        from_notworking_dms=PerEmployeeCategory(**decision_makers_stats["from_notworking_dms"]),
        from_notworking_dms_with_emails=PerEmployeeCategory(**decision_makers_stats["from_notworking_dms_with_emails"]),
        from_other_dms=PerEmployeeCategory(**decision_makers_stats["from_other_dms"]),
        from_other_dms_with_emails=PerEmployeeCategory(**decision_makers_stats["from_other_dms_with_emails"]),
        from_administration_dms=PerEmployeeCategory(**decision_makers_stats["from_administration_dms"]),
        from_administration_dms_with_emails=PerEmployeeCategory(
            **decision_makers_stats["from_administration_dms_with_emails"]
        ),
        from_project_management_dms=PerEmployeeCategory(**decision_makers_stats["from_project_management_dms"]),
        from_project_management_dms_with_emails=PerEmployeeCategory(
            **decision_makers_stats["from_project_management_dms_with_emails"]
        ),
    )
    return decision_makers_stats_fmt
