"""
This file contains the fields mapping for each endpoint and version related to
Propagation action types.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/password-safe-api
"""

from secrets_safe_library.constants.endpoints import GET_PROPAGATION_ACTION_TYPES
from secrets_safe_library.constants.versions import Version

fields = {
    GET_PROPAGATION_ACTION_TYPES: {
        Version.DEFAULT.value: [
            "PropagationActionTypeID",
            "Name",
        ]
    },
}
