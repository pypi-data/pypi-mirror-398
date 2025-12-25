"""
This file contains the fields mapping for each endpoint and version related to Safes.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/passwordsafe-api
- https://docs.beyondtrust.com/bips/docs/secrets-safe-api
"""

from secrets_safe_library.constants.endpoints import (
    GET_ASSETS_ID,
    GET_ASSETS_ID_ATTRIBUTES,
    GET_WORKGROUPS_ID_ASSETS,
    GET_WORKGROUPS_NAME_ASSETS_NAME,
)
from secrets_safe_library.constants.versions import Version

fields = {
    GET_WORKGROUPS_ID_ASSETS: {
        Version.DEFAULT.value: [
            "WorkgroupID",
            "AssetID",
            "AssetName",
            "DnsName",
            "DomainName",
            "IPAddress",
            "MacAddress",
            "AssetType",
            "OperatingSystem",
            "CreateDate",
            "LastUpdateDate",
        ],
    },
    GET_ASSETS_ID: {
        Version.DEFAULT.value: [
            "WorkgroupID",
            "AssetID",
            "AssetName",
            "DnsName",
            "DomainName",
            "IPAddress",
            "MacAddress",
            "AssetType",
            "OperatingSystem",
            "CreateDate",
            "LastUpdateDate",
        ],
    },
    GET_WORKGROUPS_NAME_ASSETS_NAME: {
        Version.DEFAULT.value: [
            "WorkgroupID",
            "AssetID",
            "AssetName",
            "DnsName",
            "DomainName",
            "IPAddress",
            "MacAddress",
            "AssetType",
            "OperatingSystem",
            "CreateDate",
            "LastUpdateDate",
        ],
    },
    GET_ASSETS_ID_ATTRIBUTES: {
        Version.DEFAULT.value: [
            "AttributeID",
            "AttributeTypeID",
            "ParentAttributeID",
            "ShortName",
            "LongName",
            "Description",
            "ValueInt",
            "IsReadOnly",
        ],
    },
}
