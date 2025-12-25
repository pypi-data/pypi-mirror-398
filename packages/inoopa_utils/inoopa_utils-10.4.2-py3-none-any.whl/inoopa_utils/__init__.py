"""
Allow import direcly from inoopa_utils without specifying the file (ie: from inoopa_utils import DbManagerMongo)
See: https://docs.astral.sh/ruff/rules/unused-import/
"""

# --- DB filter Mongo ---
from .common_mongo_filters import ACTIVE_COMPANIES as ACTIVE_COMPANIES
from .common_mongo_filters import BE_FLANDER_REGION as BE_FLANDER_REGION
from .common_mongo_filters import BE_WALLONIA_REGION as BE_WALLONIA_REGION
from .common_mongo_filters import COMPANIES_BE as COMPANIES_BE
from .common_mongo_filters import COMPANIES_NL as COMPANIES_NL
from .common_mongo_filters import FOR_PROFIT_ONLY as FOR_PROFIT_ONLY
from .common_mongo_filters import FOR_PROFIT_OR_PUBLIC as FOR_PROFIT_OR_PUBLIC
from .common_mongo_filters import NO_CHURCH_FACTORY as NO_CHURCH_FACTORY
from .common_mongo_filters import NO_LAWYER_NO_RELGIOUS_ORGS as NO_LAWYER_NO_RELGIOUS_ORGS
from .common_mongo_filters import NON_PROFIT_ONLY as NON_PROFIT_ONLY
from .common_mongo_filters import PUBLIC_ONLY as PUBLIC_ONLY
from .common_mongo_filters import WITH_PHONE as WITH_PHONE
from .common_mongo_filters import WITH_PHONE_NO_DNCM as WITH_PHONE_NO_DNCM
from .common_mongo_filters import WITH_WEBSITE as WITH_WEBSITE

# --- Helpers ---
from .helpers import extract_domain as extract_domain
from .helpers import get_all_latest_user_agents as get_all_latest_user_agents
from .helpers import get_latest_user_agent as get_latest_user_agent
from .helpers import get_random_user_agent as get_random_user_agent

# --- Logging ---
from .inoopa_logging import create_logger as create_logger

# --- DB ---
from .mongodb_helpers import DbManagerMongo as DbManagerMongo
from .typesense_helpers import TypesenseManager as TypesenseManager
