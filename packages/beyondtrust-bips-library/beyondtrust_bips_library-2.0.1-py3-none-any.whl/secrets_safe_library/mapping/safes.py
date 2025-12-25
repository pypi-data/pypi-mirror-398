"""
This file contains the fields mapping for each endpoint and version related to Safes.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/passwordsafe-api
- https://docs.beyondtrust.com/bips/docs/secrets-safe-api
"""

from secrets_safe_library.constants.endpoints import (
    GET_SECRETS_SAFE_SAFES,
    GET_SECRETS_SAFE_SAFES_ID,
)
from secrets_safe_library.constants.versions import Version

fields = {
    GET_SECRETS_SAFE_SAFES: {
        Version.DEFAULT.value: [
            "Id",
            "Name",
            "Description",
        ],
    },
    GET_SECRETS_SAFE_SAFES_ID: {
        Version.DEFAULT.value: [
            "Id",
            "Name",
            "Description",
        ],
    },
}
