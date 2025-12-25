"""
This file contains the fields mapping for each endpoint and version related to Aliases.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/password-safe-apis
"""

from secrets_safe_library.constants.endpoints import (
    GET_ALIASES,
    GET_ALIASES_ID,
    GET_ALIASES_NAME,
)
from secrets_safe_library.constants.versions import Version

DEFAULT_FIELDS = [
    "AliasID",
    "AliasName",
    "AliasState",
    "SystemId",
    "SystemName",
    "AccountId",
    "AccountName",
    "DomainName",
    "InstanceName",
    "DefaultReleaseDuration",
    "MaximumReleaseDuration",
    "LastChangeDate",
    "NextChangeDate",
    "IsChanging",
    "ChangeState",
    "MappedAccounts",
]

fields = {
    GET_ALIASES: {
        Version.DEFAULT.value: DEFAULT_FIELDS,
    },
    GET_ALIASES_ID: {
        Version.DEFAULT.value: DEFAULT_FIELDS,
    },
    GET_ALIASES_NAME: {
        Version.DEFAULT.value: DEFAULT_FIELDS,
    },
}
