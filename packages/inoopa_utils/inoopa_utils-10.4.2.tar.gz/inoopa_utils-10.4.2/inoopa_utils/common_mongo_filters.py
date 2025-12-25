"""
This file contains common filters we use in our MongoDB question.
As MongoDB filters are dicts, you can unpack them like this:

    WITH_WEBSITE = {"best_website": {"$ne": None}}
    WITH_PHONE = {"best_phone": {"$ne": None}}

    results = collection.find({ **WITH_WEBSITE, **WITH_PHONE })
"""

from inoopa_utils.custom_types.addresses import Country, RegionBe
from inoopa_utils.custom_types.legal_filters import LegalFormCategory

# --- General ---
ACTIVE_COMPANIES = {"status": "Active", "legal_situation": "Normal situation"}

# --- Contact info ---
WITH_WEBSITE = {"best_website": {"$ne": None}}
WITH_PHONE = {"best_phone": {"$ne": None}}
WITH_PHONE_NO_DNCM = {"best_phone": {"$ne": None}, "best_phone.phone": {"$ne": "DO_NOT_CALL_ME"}}

# --- Activities sector (NACEs) ---
NO_LAWYER_NO_RELGIOUS_ORGS = {
    "$nor": [
        # Lawyers
        {"nace_codes.number": {"$regex": r"69101.*"}},
        {"establishments.nace_codes.number": {"$regex": r"69101.*"}},
        {"best_nace_codes.first_best_nace_code.number": {"$regex": r"69101.*"}},
        # Religious orgs
        {"nace_codes.number": {"$regex": r"9491.*"}},
        {"establishments.nace_codes.number": {"$regex": r"9491.*"}},
        {"best_nace_codes.first_best_nace_code.number": {"$regex": r"9491.*"}},
    ]
}
# Remove church factories (most of them doesn't have any declared NACE code)
NO_CHURCH_FACTORY = {
    "$expr": {
        "$not": {
            "$regexMatch": {
                "input": "$name",
                "regex": "communaute|gemeente|kerk|église|cathedrale|church factory|kirchenfabrik|eglise",
                "options": "i",
            }
        }
    }
}

# --- Geographic ----
COMPANIES_BE = {"country": Country.belgium.value}
COMPANIES_NL = {"country": Country.netherlands.value}
BE_FLANDER_REGION = {"address.region": RegionBe.flanders.value}
BE_WALLONIA_REGION = {"address.region": RegionBe.wallonia.value}

# --- Legal forms types ---
FOR_PROFIT_ONLY = {"legal_form_type": LegalFormCategory.for_profit}
NON_PROFIT_ONLY = {"legal_form_type": LegalFormCategory.non_profit}
PUBLIC_ONLY = {"legal_form_type": LegalFormCategory.public}
FOR_PROFIT_OR_PUBLIC = {"legal_form_type": {"$ne": LegalFormCategory.non_profit}}
