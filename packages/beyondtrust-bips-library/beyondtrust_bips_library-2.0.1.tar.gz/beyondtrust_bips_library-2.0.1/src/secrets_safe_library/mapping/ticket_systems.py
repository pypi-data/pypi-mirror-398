"""
This file contains the fields mapping for each endpoint and version related to
Ticket Systems.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/password-safe-apis
"""

from secrets_safe_library.constants.endpoints import GET_TICKET_SYSTEMS
from secrets_safe_library.constants.versions import Version

fields = {
    GET_TICKET_SYSTEMS: {
        Version.DEFAULT.value: [
            "TicketSystemID",
            "IsActive",
            "TicketSystemName",
            "Description",
            "IsDefaultSystem",
        ],
    },
}
