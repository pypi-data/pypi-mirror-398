"""
This file contains the fields mapping for each endpoint and version related to Quick
Rules.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/passwordsafe-apis
"""

from secrets_safe_library.constants.endpoints import GET_QUICK_RULES, GET_QUICK_RULES_ID
from secrets_safe_library.constants.versions import Version

fields = {
    GET_QUICK_RULES: {
        Version.DEFAULT.value: [
            "SmartRuleID",
            "OrganizationID",
            "Title",
            "Description",
            "Category",
            "Status",
            "LastProcessedDate",
            "IsReadOnly",
            "RuleType",
        ],
    },
    GET_QUICK_RULES_ID: {
        Version.DEFAULT.value: [
            "SmartRuleID",
            "OrganizationID",
            "Title",
            "Description",
            "Category",
            "Status",
            "LastProcessedDate",
            "IsReadOnly",
            "RuleType",
        ],
    },
}
