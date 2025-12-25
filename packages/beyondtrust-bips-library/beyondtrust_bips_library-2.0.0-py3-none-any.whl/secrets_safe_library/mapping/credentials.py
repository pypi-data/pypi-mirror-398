"""
This file contains the fields mapping for each endpoint and version related to
CREDENTIALS.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/passwordsafe-api
"""

from secrets_safe_library.constants.endpoints import (
    GET_CREDENTIALS_ALIASID,
    GET_CREDENTIALS_REQUESTID,
)
from secrets_safe_library.constants.versions import Version

fields = {
    GET_CREDENTIALS_REQUESTID: {
        Version.DEFAULT.value: [
            "Credentials",
        ],
    },
    GET_CREDENTIALS_ALIASID: {
        Version.DEFAULT.value: [
            "AliasID",
            "AliasName",
            "SystemID",
            "SystemName",
            "AccountID",
            "AccountName",
            "DomainName",
            "Password",
            "PrivateKey",
            "Passphrase",
        ],
    },
}
