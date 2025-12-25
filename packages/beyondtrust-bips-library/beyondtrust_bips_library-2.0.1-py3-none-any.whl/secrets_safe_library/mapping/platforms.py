"""
This file contains the fields mapping for each endpoint and version related to
Platforms.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/passwordsafe-api
"""

from secrets_safe_library.constants.endpoints import GET_PLATFORMS
from secrets_safe_library.constants.versions import Version

fields = {
    GET_PLATFORMS: {
        Version.DEFAULT.value: [
            "PlatformID",
            "Name",
            "ShortName",
            "PortFlag",
            "DefaultPort",
            "SupportsElevationFlag",
            "DomainNameFlag",
            "AutoManagementFlag",
            "DSSAutoManagementFlag",
            "ManageableFlag",
            "DSSFlag",
            "LoginAccountFlag",
            "DefaultSessionType",
            "ApplicationHostFlag",
            "RequiresApplicationHost",
            "RequiresTenantID",
            "RequiresObjectID",
            "RequiresSecret",
        ],
    },
}
