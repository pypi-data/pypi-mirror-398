"""
This file contains the fields mapping for each endpoint and version related to API
registrations.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/beyondinsight-apis
"""

from secrets_safe_library.constants.endpoints import (
    GET_API_REGISTRATIONS,
    GET_API_REGISTRATIONS_ID,
    POST_API_REGISTRATIONS,
    PUT_API_REGISTRATIONS_ID,
)
from secrets_safe_library.constants.versions import Version

AUTHENTICATION_RULES = [
    {
        "Type": str,
        "Value": str,
        "Description": str,
    }
]

DEFAULT_GET_FIELDS = [
    "Id",
    "Name",
    "RegistrationType",
    "Active",
    "Visible",
    "AccessTokenDuration",
    "MultiFactorAuthenticationEnforced",
    "ClientCertificateRequired",
    "UserPasswordRequired",
    "VerifyPsrunSignature",
    "IPAuthenticationRules",
    "PSRUNRules",
    "XForwardedForAuthenticationRules",
]

# Used for POST and PUT requests for API Key and API Access policies
DEFAULT_BODY_API_REGISTRATIONS_API_KEY = {
    "Name": str,
    "RegistrationType": str,
    "AccessTokenDuration": int,
    "Active": bool,
    "Visible": bool,
    "MultiFactorAuthenticationEnforced": bool,
    "ClientCertificateRequired": bool,
    "UserPasswordRequired": bool,
    "VerifyPsrunSignature": bool,
    "IPAuthenticationRules": AUTHENTICATION_RULES,
    "PSRUNRules": [
        {
            "IPAddress": str,
            "MacAddress": str,
            "SystemName": str,
            "FQDN": str,
            "DomainName": str,
            "UserId": str,
            "RootVolumeId": str,
            "OSVersion": str,
        }
    ],
    "XForwardedForAuthenticationRules": AUTHENTICATION_RULES,
}

fields = {
    GET_API_REGISTRATIONS: {
        Version.DEFAULT.value: DEFAULT_GET_FIELDS,
    },
    GET_API_REGISTRATIONS_ID: {
        Version.DEFAULT.value: DEFAULT_GET_FIELDS,
    },
    POST_API_REGISTRATIONS: {
        Version.DEFAULT.value: DEFAULT_BODY_API_REGISTRATIONS_API_KEY,
    },
    PUT_API_REGISTRATIONS_ID: {
        Version.DEFAULT.value: DEFAULT_BODY_API_REGISTRATIONS_API_KEY,
    },
}
