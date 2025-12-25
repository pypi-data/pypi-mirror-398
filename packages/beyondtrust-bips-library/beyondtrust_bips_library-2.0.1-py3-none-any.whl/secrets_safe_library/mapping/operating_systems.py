"""
This file contains the fields mapping for each endpoint and version related to
Operating Systems.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/beyondinsight-apis
"""

from secrets_safe_library.constants.endpoints import GET_OPERATING_SYSTEMS
from secrets_safe_library.constants.versions import Version

fields = {
    GET_OPERATING_SYSTEMS: {
        Version.DEFAULT.value: [
            "OperatingSystemID",
            "Name",
        ],
    },
}
