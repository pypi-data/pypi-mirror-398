"""
This file contains the fields mapping for each endpoint and version related to ISA
Requests.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/passwordsafe-api
"""

from secrets_safe_library.constants.endpoints import POST_ISA_REQUESTS
from secrets_safe_library.constants.versions import Version

fields = {
    POST_ISA_REQUESTS: {
        Version.DEFAULT.value: {
            "SystemID": int,
            "AccountID": int,
            "DurationMinutes": int,
            "Reason": str,
        },
    }
}
