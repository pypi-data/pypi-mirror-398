"""
This file contains the fields mapping for each endpoint and version related to
Entitlements.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/beyondinsight-apis
"""

from secrets_safe_library.constants.endpoints import GET_ENTITLEMENTS
from secrets_safe_library.constants.versions import Version

fields = {
    GET_ENTITLEMENTS: {
        Version.DEFAULT.value: [
            "GroupID",
            "Name",
            "SmartRuleId",
            "Title",
            "SmartRuleType",
            "AccessLevel",
            "RoleId",
            "RoleName",
            "DedicatedAccountPermissionOverride",
            "DedicatedToAppUserID",
            "DedicatedToAppUserName",
            "IsAdministratorGroup",
            "UserID",
            "UserName",
            "ManagedAccountId",
            "AccountName",
            "RationalizedSystemName",
            "ApplicationName",
            "AccessPolicyName",
            "ManagedSystemID",
            "ApplicationID",
        ],
    },
}
