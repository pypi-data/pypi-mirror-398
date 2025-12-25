"""
This file contains the fields mapping for each endpoint and version related to
Access Levels.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/beyondinsight-api
"""

from secrets_safe_library.constants.endpoints import (
    GET_ACCESS_LEVELS,
    POST_ACCESS_LEVELS_USERGROUPID_SMARTRULEID,
)
from secrets_safe_library.constants.versions import Version

fields = {
    GET_ACCESS_LEVELS: {
        Version.DEFAULT.value: [
            "AccessLevelID",
            "Name",
        ]
    },
    POST_ACCESS_LEVELS_USERGROUPID_SMARTRULEID: {
        Version.DEFAULT.value: {
            "AccessLevelID": int,
        }
    },
}
