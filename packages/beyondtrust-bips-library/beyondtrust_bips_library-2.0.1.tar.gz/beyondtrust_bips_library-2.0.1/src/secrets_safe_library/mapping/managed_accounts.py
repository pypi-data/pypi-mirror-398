"""
This file contains the fields mapping for each endpoint and version related to Safes.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/passwordsafe-api
- https://docs.beyondtrust.com/bips/docs/secrets-safe-api
"""

from secrets_safe_library.constants.endpoints import (
    GET_MANAGED_ACCOUNTS_ID,
    GET_MANAGED_ACCOUNTS_ID_ATTRIBUTES,
    GET_MANAGED_SYSTEMS_SYSTEM_ID_MANAGED_ACCOUNTS,
    POST_MANAGED_SYSTEMS_SYSTEM_ID_MANAGED_ACCOUNTS,
    PUT_MANAGED_ACCOUNTS_CREDENTIALS,
)
from secrets_safe_library.constants.versions import Version

fields = {
    GET_MANAGED_SYSTEMS_SYSTEM_ID_MANAGED_ACCOUNTS: {
        Version.DEFAULT.value: [
            "ManagedAccountID",
            "ManagedSystemID",
            "DomainName",
            "AccountName",
            "DistinguishedName",
            "PasswordFallbackFlag",
            "UserPrincipalName",
            "SAMAccountName",
            "LoginAccountFlag",
            "Description",
            "PasswordRuleID",
            "ApiEnabled",
            "ReleaseNotificationEmail",
            "ChangeServicesFlag",
            "RestartServicesFlag",
            "ChangeTasksFlag",
            "ReleaseDuration",
            "MaxReleaseDuration",
            "ISAReleaseDuration",
            "MaxConcurrentRequests",
            "AutoManagementFlag",
            "DSSAutoManagementFlag",
            "CheckPasswordFlag",
            "ResetPasswordOnMismatchFlag",
            "ChangePasswordAfterAnyReleaseFlag",
            "ChangeFrequencyType",
            "ChangeFrequencyDays",
            "ChangeTime",
            "ParentAccountID",
            "IsSubscribedAccount",
            "LastChangeDate",
            "NextChangeDate",
            "IsChanging",
            "ChangeState",
            "UseOwnCredentials",
            "WorkgroupID",
            "ChangeIISAppPoolFlag",
            "RestartIISAppPoolFlag",
            "ChangeWindowsAutoLogonFlag",
            "ChangeComPlusFlag",
            "ChangeDComFlag",
            "ChangeSComFlag",
        ]
    },
    GET_MANAGED_ACCOUNTS_ID: {
        Version.DEFAULT.value: [
            "ManagedAccountID",
            "ManagedSystemID",
            "DomainName",
            "AccountName",
            "DistinguishedName",
            "PasswordFallbackFlag",
            "UserPrincipalName",
            "SAMAccountName",
            "LoginAccountFlag",
            "Description",
            "PasswordRuleID",
            "ApiEnabled",
            "ReleaseNotificationEmail",
            "ChangeServicesFlag",
            "RestartServicesFlag",
            "ChangeTasksFlag",
            "ReleaseDuration",
            "MaxReleaseDuration",
            "ISAReleaseDuration",
            "MaxConcurrentRequests",
            "AutoManagementFlag",
            "DSSAutoManagementFlag",
            "CheckPasswordFlag",
            "ResetPasswordOnMismatchFlag",
            "ChangePasswordAfterAnyReleaseFlag",
            "ChangeFrequencyType",
            "ChangeFrequencyDays",
            "ChangeTime",
            "ParentAccountID",
            "IsSubscribedAccount",
            "LastChangeDate",
            "NextChangeDate",
            "IsChanging",
            "ChangeState",
            "UseOwnCredentials",
            "WorkgroupID",
            "ChangeIISAppPoolFlag",
            "RestartIISAppPoolFlag",
            "ObjectID",
        ]
    },
    GET_MANAGED_ACCOUNTS_ID_ATTRIBUTES: {
        Version.DEFAULT.value: [
            "AttributeID",
            "AttributeTypeID",
            "ParentAttributeID",
            "ShortName",
            "LongName",
            "Description",
            "IsReadOnly",
        ]
    },
    PUT_MANAGED_ACCOUNTS_CREDENTIALS: {
        Version.DEFAULT.value: {
            "Password": str,
            "PublicKey": str,
            "PrivateKey": str,
            "Passphrase": str,
            "UpdateSystem": bool,
        },
    },
}

# POST fields according 3.0 to 3.5 versions (these have incremental changes)
POST_MANAGED_ACCOUNT_V3_0 = {
    "AccountName": str,
    "Password": str,
    "DomainName": str,
    "UserPrincipalName": str,
    "SAMAccountName": str,
    "DistinguishedName": str,
    "PrivateKey": str,
    "Passphrase": str,
    "PasswordFallbackFlag": bool,
    "LoginAccountFlag": bool,
    "Description": str,
    "PasswordRuleID": int,
    "ApiEnabled": bool,
    "ReleaseNotificationEmail": str,
    "ChangeServicesFlag": bool,
    "RestartServicesFlag": bool,
    "ChangeTasksFlag": bool,
    "ReleaseDuration": int,
    "MaxReleaseDuration": int,
    "ISAReleaseDuration": int,
    "MaxConcurrentRequests": int,
    "AutoManagementFlag": bool,
    "DSSAutoManagementFlag": bool,
    "CheckPasswordFlag": bool,
    "ResetPasswordOnMismatchFlag": bool,
    "ChangePasswordAfterAnyReleaseFlag": bool,
    "ChangeFrequencyType": str,
    "ChangeFrequencyDays": int,
    "ChangeTime": str,
    "NextChangeDate": str,
}

POST_MANAGED_ACCOUNT_V3_1 = {**POST_MANAGED_ACCOUNT_V3_0, "UseOwnCredentials": bool}
POST_MANAGED_ACCOUNT_V3_2 = {
    **POST_MANAGED_ACCOUNT_V3_1,
    "ChangeIISAppPoolFlag": bool,
    "RestartIISAppPoolFlag": bool,
}
POST_MANAGED_ACCOUNT_V3_3 = {**POST_MANAGED_ACCOUNT_V3_2, "WorkgroupID": int}
POST_MANAGED_ACCOUNT_V3_4 = {
    **POST_MANAGED_ACCOUNT_V3_3,
    "ChangeWindowsAutoLogonFlag": bool,
    "ChangeComPlusFlag": bool,
    "ChangeDComFlag": bool,
    "ChangeSComFlag": bool,
}
POST_MANAGED_ACCOUNT_V3_5 = {**POST_MANAGED_ACCOUNT_V3_4, "ObjectID": str}

post_fields = {
    POST_MANAGED_SYSTEMS_SYSTEM_ID_MANAGED_ACCOUNTS: {
        Version.V3_0.value: POST_MANAGED_ACCOUNT_V3_0,
        Version.V3_1.value: POST_MANAGED_ACCOUNT_V3_1,
        Version.V3_2.value: POST_MANAGED_ACCOUNT_V3_2,
        Version.V3_3.value: POST_MANAGED_ACCOUNT_V3_3,
        Version.V3_4.value: POST_MANAGED_ACCOUNT_V3_4,
        Version.V3_5.value: POST_MANAGED_ACCOUNT_V3_5,
    }
}

fields.update(post_fields)
