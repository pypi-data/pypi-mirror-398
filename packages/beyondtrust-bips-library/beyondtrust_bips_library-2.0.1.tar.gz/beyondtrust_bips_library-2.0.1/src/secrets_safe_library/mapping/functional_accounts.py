"""
This file contains the fields mapping for each endpoint and version related to
functional accounts.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/passwordsafe-api
"""

from secrets_safe_library.constants.endpoints import (
    GET_FUNCTIONAL_ACCOUNTS,
    GET_FUNCTIONAL_ACCOUNTS_ID,
    POST_FUNCTIONAL_ACCOUNTS,
)
from secrets_safe_library.constants.versions import Version

GET_FUNCTIONAL_ACCOUNTS_DEFAULT = [
    "FunctionalAccountID",
    "PlatformID",
    "DomainName",
    "AccountName",
    "DisplayName",
    "Description",
    "ElevationCommand",
    "SystemReferenceCount",
    "TenantID",
    "ObjectID",
    "AzureInstance",
]

fields = {
    GET_FUNCTIONAL_ACCOUNTS: {
        Version.DEFAULT.value: GET_FUNCTIONAL_ACCOUNTS_DEFAULT,
    },
    GET_FUNCTIONAL_ACCOUNTS_ID: {
        Version.DEFAULT.value: GET_FUNCTIONAL_ACCOUNTS_DEFAULT,
    },
    POST_FUNCTIONAL_ACCOUNTS: {
        Version.DEFAULT.value: {
            "PlatformID": int,
            "DomainName": str,
            "AccountName": str,
            "DisplayName": str,
            "Password": str,
            "PrivateKey": str,
            "Passphrase": str,
            "Description": str,
            "ElevationCommand": str,
            "TenantID": str,
            "ObjectID": str,
            "Secret": str,
            "ServiceAccountEmail": str,
            "AzureInstance": str,
        }
    },
}
