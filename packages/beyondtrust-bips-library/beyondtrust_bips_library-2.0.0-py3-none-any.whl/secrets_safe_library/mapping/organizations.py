"""
This file contains the fields mapping for each endpoint and version related to
organizations.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/beyondinsight-api
"""

from secrets_safe_library.constants.endpoints import GET_ORGANIZATIONS
from secrets_safe_library.constants.versions import Version

fields = {
    GET_ORGANIZATIONS: {
        Version.DEFAULT.value: [
            "OrganizationID",
            "Name",
            "IsActive",
        ],
    },
}
