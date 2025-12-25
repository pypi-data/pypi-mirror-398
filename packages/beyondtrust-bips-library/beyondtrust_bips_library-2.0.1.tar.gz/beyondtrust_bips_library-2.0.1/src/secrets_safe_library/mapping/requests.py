"""
This file contains the fields mapping for each endpoint and version related to
Requests.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/password-safe-api
"""

from secrets_safe_library.constants.endpoints import (
    GET_REQUESTS,
    POST_REQUESTS,
    POST_REQUESTS_ALIASES,
)
from secrets_safe_library.constants.versions import Version

fields = {
    GET_REQUESTS: {
        Version.DEFAULT.value: [
            "RequestID",
            "SystemID",
            "SystemName",
            "AccountID",
            "AccountName",
            "DomainName",
            "AliasID",
            "ApplicationID",
            "RequestReleaseDate",
            "ApprovedDate",
            "ExpiresDate",
            "Status",
            "AccessType",
            "Reason",
        ],
    },
    POST_REQUESTS: {
        Version.DEFAULT.value: {
            "AccessType": str,
            "SystemID": int,
            "AccountID": int,
            "ApplicationID": int,
            "DurationMinutes": int,
            "Reason": str,
            "AccessPolicyScheduleID": int,
            "ConflictOption": str,
            "TicketSystemID": int,
            "TicketNumber": str,
            "RotateOnCheckin": bool,
        },
    },
    POST_REQUESTS_ALIASES: {
        Version.DEFAULT.value: {
            "AccessType": str,
            "DurationMinutes": int,
            "Reason": str,
            "AccessPolicyScheduleID": int,
            "ConflictOption": str,
            "TicketSystemID": int,
            "TicketNumber": str,
            "RotateOnCheckin": bool,
        },
    },
}
