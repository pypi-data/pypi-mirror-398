"""
This file contains the fields mapping for each endpoint and version related to
Usergroups.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/beyondinsight-api
"""

from secrets_safe_library.constants.endpoints import (
    GET_USERGROUPS,
    GET_USERGROUPS_ID,
    GET_USERGROUPS_NAME,
    POST_USERGROUPS_AD,
    POST_USERGROUPS_BI,
    POST_USERGROUPS_ENTRAID,
    POST_USERGROUPS_LDAP,
)
from secrets_safe_library.constants.versions import Version

fields = {
    GET_USERGROUPS: {
        Version.DEFAULT.value: [
            "GroupID",
            "Name",
            "DistinguishedName",
            "Description",
            "GroupType",
            "AccountAttribute",
            "ApplicationRegistrationIDs",
            "MembershipAttribute",
            "IsActive",
        ],
    },
    GET_USERGROUPS_ID: {
        Version.DEFAULT.value: [
            "GroupID",
            "Name",
            "DistinguishedName",
            "Description",
            "GroupType",
            "AccountAttribute",
            "ApplicationRegistrationIDs",
            "MembershipAttribute",
            "IsActive",
        ],
    },
    GET_USERGROUPS_NAME: {
        Version.DEFAULT.value: [
            "GroupID",
            "Name",
            "DistinguishedName",
            "GroupType",
            "AccountAttribute",
            "ApplicationRegistrationIDs",
            "MembershipAttribute",
            "IsActive",
        ],
    },
    POST_USERGROUPS_BI: {
        Version.DEFAULT.value: {
            "groupType": str,
            "groupName": str,
            "description": str,
            "isActive": bool,
            "Permissions": [
                {
                    "PermissionID": int,
                    "AccessLevelID": int,
                },
            ],
            "SmartRuleAccess": [
                {"SmartRuleID": int, "AccessLevelID": int},
            ],
            "ApplicationRegistrationIDs": list[int],
        },
    },
    POST_USERGROUPS_ENTRAID: {
        Version.DEFAULT.value: {
            "groupType": str,
            "description": str,
            "groupName": str,
            "ClientId": str,
            "TenantId": str,
            "ClientSecret": str,
            "AzureInstance": str,
            "isActive": bool,
            "Permissions": [
                {
                    "PermissionID": int,
                    "AccessLevelID": int,
                },
            ],
            "SmartRuleAccess": [
                {"SmartRuleID": int, "AccessLevelID": int},
            ],
            "ApplicationRegistrationIDs": list[int],
        },
    },
    POST_USERGROUPS_AD: {
        Version.DEFAULT.value: {
            "groupType": str,
            "groupName": str,
            "forestName": str,
            "domainName": str,
            "description": str,
            "bindUser": str,
            "bindPassword": str,
            "useSSL": bool,
            "isActive": bool,
            "ExcludedFromGlobalSync": bool,
            "OverrideGlobalSyncSettings": bool,
            "Permissions": [
                {
                    "PermissionID": int,
                    "AccessLevelID": int,
                },
            ],
            "SmartRuleAccess": [
                {"SmartRuleID": int, "AccessLevelID": int},
            ],
            "ApplicationRegistrationIDs": list[int],
        },
    },
    POST_USERGROUPS_LDAP: {
        Version.DEFAULT.value: {
            "groupType": str,
            "groupName": str,
            "groupDistinguishedName": str,
            "hostName": str,
            "bindUser": str,
            "bindPassword": str,
            "port": int,
            "useSSL": bool,
            "membershipAttribute": str,
            "accountAttribute": str,
            "isActive": bool,
            "Permissions": [
                {
                    "PermissionID": int,
                    "AccessLevelID": int,
                },
            ],
            "SmartRuleAccess": [
                {"SmartRuleID": int, "AccessLevelID": int},
            ],
            "ApplicationRegistrationIDs": list[int],
        },
    },
}
