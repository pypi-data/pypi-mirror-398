"""
This file contains the fields mapping for each endpoint and version related to
Applications.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/passwordsafe-apis
"""

from secrets_safe_library.constants.endpoints import (
    GET_APPLICATIONS,
    GET_APPLICATIONS_ID,
)
from secrets_safe_library.constants.versions import Version

DEFAULT_FIELDS = [
    "ApplicationID",
    "Name",
    "DisplayName",
    "Version",
    "Command",
    "Parameters",
    "Publisher",
    "ApplicationType",
    "FunctionalAccountID",
    "ManagedSystemID",
    "IsActive",
    "SmartRuleID",
]

fields = {
    GET_APPLICATIONS: {
        Version.DEFAULT.value: DEFAULT_FIELDS,
    },
    GET_APPLICATIONS_ID: {Version.DEFAULT.value: DEFAULT_FIELDS},
}
