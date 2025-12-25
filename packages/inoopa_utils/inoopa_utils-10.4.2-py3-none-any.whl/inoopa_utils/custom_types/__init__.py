"""
Allow import direcly from inoopa_utils.custom_types without specifying file (ie: from inoopa_utils.custom_types import Company)
See: https://docs.astral.sh/ruff/rules/unused-import/
"""

# --- Address ---
from .addresses import Country as Country
from .addresses import ProvinceBe as ProvinceBe
from .addresses import ProvinceFr as ProvinceFr
from .addresses import ProvinceNl as ProvinceNl
from .addresses import RegionBe as RegionBe
from .addresses import RegionFr as RegionFr
from .addresses import RegionNl as RegionNl

# --- Company ---
from .companies import Address as Address
from .companies import BestNaceCodes as BestNaceCodes
from .companies import BoardMember as BoardMember
from .companies import Company as Company
from .companies import Email as Email
from .companies import Establishment as Establishment
from .companies import Finance as Finance
from .companies import NaceCode as NaceCode
from .companies import NaceCodeExtended as NaceCodeExtended
from .companies import Phone as Phone
from .companies import Website as Website
from .companies import convert_dict_to_company as convert_dict_to_company

# --- DB stats ---
from .db_stats import EMPLOYEE_CATEGORIES_CODES_MAP as EMPLOYEE_CATEGORIES_CODES_MAP
from .db_stats import CompanyStats as CompanyStats
from .db_stats import DecisionMakersStats as DecisionMakersStats
from .db_stats import NaceMetricForEmployeeCategory as NaceMetricForEmployeeCategory
from .db_stats import NaceStats as NaceStats
from .db_stats import PerEmployeeCategory as PerEmployeeCategory
from .db_stats import dict_to_company_stats as dict_to_company_stats
from .db_stats import dict_to_decision_makers_stats as dict_to_decision_makers_stats
from .db_stats import dict_to_nace_stats as dict_to_nace_stats

# --- Decision Makers ---
from .decision_makers import DecisionMaker as DecisionMaker
from .decision_makers import DecisionMakerDepartment as DecisionMakerDepartment
from .decision_makers import responsibilities_level_mapper as responsibilities_level_mapper
from .delivery_filters import AdditionalFields as AdditionalFields
from .delivery_filters import EnrichmentCompanyFilters as EnrichmentCompanyFilters
from .delivery_filters import LeadGenerationCompanyFilters as LeadGenerationCompanyFilters

# --- Delivery filters ---
from .delivery_filters import MongoFilters as MongoFilters

# --- Legal filters ---
from .legal_filters import EmployeeCategoryClass as EmployeeCategoryClass
from .legal_filters import EntityType as EntityType
from .legal_filters import LegalFormBe as LegalFormBe
from .legal_filters import LegalFormCategory as LegalFormCategory
from .legal_filters import LegalFormNl as LegalFormNl
from .legal_filters import get_all_legal_forms as get_all_legal_forms
from .legal_filters import get_all_legal_forms_str as get_all_legal_forms_str

# --- Website structure ---
from .website_structure import WebsiteStructure as WebsiteStructure
