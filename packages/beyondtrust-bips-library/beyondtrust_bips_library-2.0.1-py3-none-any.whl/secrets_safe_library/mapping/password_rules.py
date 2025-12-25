"""
This file contains the fields mapping for each endpoint and version related to Safes.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/passwordsafe-api
"""

from secrets_safe_library.constants.endpoints import (
    GET_PASSWORD_RULES,
    GET_PASSWORD_RULES_ENABLED_PRODUCTS,
    GET_PASSWORD_RULES_ID,
)
from secrets_safe_library.constants.versions import Version

GET_PASSWORD_RULES_FIELDS = [
    "PasswordRuleID",
    "Name",
    "Description",
    "MinimumLength",
    "MaximumLength",
    "FirstCharacterRequirement",
    "LowercaseRequirement",
    "UppercaseRequirement",
    "NumericRequirement",
    "SymbolRequirement",
    "ValidLowercaseCharacters",
    "ValidUppercaseCharacters",
    "ValidSymbols",
    "EnabledProducts",
]

fields = {
    GET_PASSWORD_RULES: {
        Version.DEFAULT.value: GET_PASSWORD_RULES_FIELDS,
    },
    GET_PASSWORD_RULES_ID: {
        Version.DEFAULT.value: GET_PASSWORD_RULES_FIELDS,
    },
    GET_PASSWORD_RULES_ENABLED_PRODUCTS: {
        Version.DEFAULT.value: GET_PASSWORD_RULES_FIELDS,
    },
}
