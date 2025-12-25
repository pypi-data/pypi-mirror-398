"""
This file contains the fields mapping for each endpoint and version related to
EPM Policies.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/beyondinsight-apis
"""

from secrets_safe_library.constants.endpoints import (
    POST_EPM_POLICIES_ID_EPMAPPLICATIONS_ADD,
)
from secrets_safe_library.constants.versions import Version

fields = {
    POST_EPM_POLICIES_ID_EPMAPPLICATIONS_ADD: {
        Version.DEFAULT.value: {
            "GroupName": str,
            "Name": str,
            "Path": str,
            "Publisher": str,
            "ChildrenInheritToken": bool,
        }
    },
}
