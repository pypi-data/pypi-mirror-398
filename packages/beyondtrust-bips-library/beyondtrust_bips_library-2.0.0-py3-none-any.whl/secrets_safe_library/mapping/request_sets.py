"""
This file contains the fields mapping for each endpoint and version related to
Requests.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/password-safe-api
"""

from secrets_safe_library.constants.endpoints import GET_REQUEST_SETS, POST_REQUEST_SETS
from secrets_safe_library.constants.versions import Version

fields = {
    GET_REQUEST_SETS: {
        Version.DEFAULT.value: [
            "RequestSetID",
            "Requests",
        ],
    },
    POST_REQUEST_SETS: {
        Version.DEFAULT.value: {
            "AccessTypes": list,
            "SystemID": int,
            "AccountID": int,
            "ApplicationID": int,
            "DurationMinutes": int,
            "Reason": str,
            "TicketSystemID": int,
            "TicketNumber": str,
        },
    },
}
