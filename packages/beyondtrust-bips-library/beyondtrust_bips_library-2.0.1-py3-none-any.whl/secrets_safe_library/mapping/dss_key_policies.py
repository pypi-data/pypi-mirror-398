"""
This file contains the fields mapping for each endpoint and version related to
DSS key Policies.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/password-safe-api
"""

from secrets_safe_library.constants.endpoints import (
    GET_DSS_KEY_RULES,
    GET_DSS_KEY_RULES_ID,
)
from secrets_safe_library.constants.versions import Version

DEFAULT_FIELDS = [
    "DSSKeyRuleID",
    "Name",
    "Description",
    "KeyType",
    "KeySize",
    "EncryptionType",
    "PasswordRuleID",
]

fields = {
    GET_DSS_KEY_RULES: {
        Version.DEFAULT.value: DEFAULT_FIELDS,
    },
    GET_DSS_KEY_RULES_ID: {
        Version.DEFAULT.value: DEFAULT_FIELDS,
    },
}
