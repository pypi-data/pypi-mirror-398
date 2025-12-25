"""
This file contains the fields mapping for each endpoint and version related to
Propagation actions.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/password-safe-api
"""

from secrets_safe_library.constants.endpoints import (
    GET_MANAGED_ACCOUNTS_PROPAGATION_ACTIONS,
    GET_PROPAGATION_ACTIONS,
    GET_PROPAGATION_ACTIONS_ID,
    POST_MANAGED_ACCOUNT_PROPAGATION_ACTIONS,
)
from secrets_safe_library.constants.versions import Version

DEFAULT_FIELDS = [
    "PropagationActionID",
    "PropagationActionTypeID",
    "Name",
    "Description",
]

fields = {
    GET_PROPAGATION_ACTIONS: {
        Version.DEFAULT.value: DEFAULT_FIELDS,
    },
    GET_PROPAGATION_ACTIONS_ID: {
        Version.DEFAULT.value: DEFAULT_FIELDS,
    },
    GET_MANAGED_ACCOUNTS_PROPAGATION_ACTIONS: {
        Version.DEFAULT.value: DEFAULT_FIELDS
        + [
            "SmartRuleID",
        ]
    },
    POST_MANAGED_ACCOUNT_PROPAGATION_ACTIONS: {
        Version.DEFAULT.value: {
            "SmartRuleID": int,
        }
    },
}
