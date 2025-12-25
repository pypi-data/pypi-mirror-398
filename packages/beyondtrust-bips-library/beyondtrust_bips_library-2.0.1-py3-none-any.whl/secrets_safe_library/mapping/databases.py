"""
This file contains the fields mapping for each endpoint and version related to
DATABASES.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/beyondinsight-api
- https://docs.beyondtrust.com/bips/docs/secrets-safe-api
"""

from secrets_safe_library.constants.endpoints import (
    GET_DATABASES,
    GET_DATABASES_ASSET_ID,
    GET_DATABASES_ID,
    POST_DATABASES_ASSET_ID,
    PUT_DATABASES_ID,
)
from secrets_safe_library.constants.versions import Version

fields = {
    GET_DATABASES: {
        Version.DEFAULT.value: [
            "AssetID",
            "DatabaseID",
            "PlatformID",
            "InstanceName",
            "IsDefaultInstance",
            "Port",
            "Version",
            "Template",
        ],
    },
    GET_DATABASES_ID: {
        Version.DEFAULT.value: [
            "AssetID",
            "DatabaseID",
            "PlatformID",
            "InstanceName",
            "IsDefaultInstance",
            "Port",
            "Version",
        ],
    },
    GET_DATABASES_ASSET_ID: {
        Version.DEFAULT.value: [
            "AssetID",
            "DatabaseID",
            "PlatformID",
            "InstanceName",
            "IsDefaultInstance",
            "Port",
            "Version",
            "Template",
        ],
    },
    POST_DATABASES_ASSET_ID: {
        Version.DEFAULT.value: {
            "PlatformID": int,
            "InstanceName": str,
            "IsDefaultInstance": bool,
            "Port": int,
            "Version": str,
            "Template": str,
        },
    },
    PUT_DATABASES_ID: {
        Version.DEFAULT.value: {
            "PlatformID": int,
            "InstanceName": str,
            "IsDefaultInstance": bool,
            "Port": int,
            "Version": str,
            "Template": str,
        },
    },
}
