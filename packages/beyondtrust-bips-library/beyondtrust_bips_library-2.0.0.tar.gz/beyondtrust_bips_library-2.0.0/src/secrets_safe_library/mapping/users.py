"""
This file contains the fields mapping for each endpoint and version related to
Users.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/beyondinsight-api
- https://docs.beyondtrust.com/bips/docs/secrets-safe-api
"""

from secrets_safe_library.constants.endpoints import (
    GET_USERS,
    GET_USERS_ID,
    GET_USERS_USERGROUPID,
    POST_USERS_AD,
    POST_USERS_APP,
    POST_USERS_BI,
    POST_USERS_LDAP,
    POST_USERS_QUARANTINE,
    POST_USERS_USERGROUPID,
    PUT_USERS_ID_APP,
    PUT_USERS_ID_BI,
)
from secrets_safe_library.constants.versions import Version

fields = {
    GET_USERS: {
        Version.DEFAULT.value: [
            "UserID",
            "UserName",
            "DomainName",
            "DistinguishedName",
            "FirstName",
            "LastName",
            "EmailAddress",
            "LastLoginDate",
            "LastLoginAuthenticationType",
            "LastLoginConfigurationName",
            "LastLoginSAMLIDPURL",
            "LastLoginSSOURL",
            "IsQuarantined",
            "IsActive",
            "ClientID",
            "ClientSecret",
            "AccessPolicyID",
            "UserType",
        ],
    },
    GET_USERS_ID: {
        Version.DEFAULT.value: [
            "UserID",
            "UserName",
            "DomainName",
            "DistinguishedName",
            "FirstName",
            "LastName",
            "EmailAddress",
            "LastLoginDate",
            "LastLoginAuthenticationType",
            "LastLoginConfigurationName",
            "LastLoginSAMLIDPURL",
            "LastLoginSSOURL",
            "IsQuarantined",
            "IsActive",
            "ClientID",
            "ClientSecret",
            "AccessPolicyID",
            "UserType",
        ],
    },
    GET_USERS_USERGROUPID: {
        Version.DEFAULT.value: [
            "UserID",
            "UserName",
            "DomainName",
            "DistinguishedName",
            "FirstName",
            "LastName",
            "EmailAddress",
            "LastLoginDate",
            "LastLoginAuthenticationType",
            "LastLoginConfigurationName",
            "LastLoginSAMLIDPURL",
            "LastLoginSSOURL",
            "IsQuarantined",
            "IsActive",
            "ClientID",
            "ClientSecret",
            "AccessPolicyID",
            "UserType",
        ],
    },
    POST_USERS_BI: {
        Version.DEFAULT.value: {
            "UserType": str,
            "UserName": str,
            "FirstName": str,
            "LastName": str,
            "EmailAddress": str,
            "Password": str,
        },
    },
    POST_USERS_AD: {
        Version.DEFAULT.value: {
            "UserType": str,
            "UserName": str,
            "ForestName": str,
            "DomainName": str,
            "BindUser": str,
            "BindPassword": str,
            "UseSSL": bool,
        },
    },
    POST_USERS_LDAP: {
        Version.DEFAULT.value: {
            "UserType": str,
            "HostName": str,
            "DistinguishedName": str,
            "AccountNameAttribute": str,
            "BindUser": str,
            "BindPassword": str,
            "Port": int,
            "UseSSL": bool,
        },
    },
    POST_USERS_APP: {
        Version.DEFAULT.value: {
            "UserType": str,
            "UserName": str,
            "AccessPolicyID": int,
        },
    },
    POST_USERS_QUARANTINE: {
        Version.DEFAULT.value: {
            "UserID": int,
            "UserName": str,
            "DomainName": str,
            "DistinguishedName": str,
            "FirstName": str,
            "LastName": str,
            "EmailAddress": str,
            "IsQuarantined": bool,
            "IsActive": bool,
        },
    },
    POST_USERS_USERGROUPID: {
        Version.DEFAULT.value: {
            "UserName": str,
            "FirstName": str,
            "LastName": str,
            "EmailAddress": str,
            "Password": str,
        },
    },
    PUT_USERS_ID_BI: {
        Version.DEFAULT.value: {
            "UserName": str,
            "FirstName": str,
            "LastName": str,
            "EmailAddress": str,
            "Password": str,
        },
    },
    PUT_USERS_ID_APP: {
        Version.DEFAULT.value: {
            "UserName": str,
            "AccessPolicyID": int,
        },
    },
}
