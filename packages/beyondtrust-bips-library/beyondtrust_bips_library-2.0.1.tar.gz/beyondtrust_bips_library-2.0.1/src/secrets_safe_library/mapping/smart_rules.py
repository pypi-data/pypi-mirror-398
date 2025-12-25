"""
This file contains the fields mapping for each endpoint and version related to Smart
Rules.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/beyondinsight-apis
- https://docs.beyondtrust.com/bips/docs/passwordsafe-apis
- https://docs.beyondtrust.com/bips/docs/secrets-safe-apis
"""

from secrets_safe_library.constants.endpoints import (
    GET_SMART_RULES,
    GET_SMART_RULES_ID,
    POST_SMART_RULES_FILTER_ASSET_ATTRIBUTE,
)
from secrets_safe_library.constants.versions import Version

GET_SMART_RULES_DEFAULT = [
    "SmartRuleID",
    "OrganizationIDs",
    "Title",
    "Description",
    "Category",
    "Status",
    "LastProcessedDate",
    "IsReadOnly",
    "RuleType",
]

fields = {
    GET_SMART_RULES: {Version.DEFAULT.value: GET_SMART_RULES_DEFAULT},
    GET_SMART_RULES_ID: {
        Version.DEFAULT.value: GET_SMART_RULES_DEFAULT,
    },
    POST_SMART_RULES_FILTER_ASSET_ATTRIBUTE: {
        Version.DEFAULT.value: {
            "AttributeIDs": list,
            "Title": str,
            "Category": str,
            "Description": str,
            "ProcessImmediately": bool,
        }
    },
}
