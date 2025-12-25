"""
This file contains the fields mapping for each endpoint and version related to Address
Groups.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/beyondinsight-api
"""

from secrets_safe_library.constants.endpoints import (
    GET_ADDRESS_GROUPS,
    GET_ADDRESS_GROUPS_ID,
)
from secrets_safe_library.constants.versions import Version

fields = {
    GET_ADDRESS_GROUPS: {
        Version.DEFAULT.value: ["AddressGroupID", "Name", "OrganizationID"],
    },
    GET_ADDRESS_GROUPS_ID: {
        Version.DEFAULT.value: [
            "AddressGroupID",
            "Name",
        ],
    },
}
