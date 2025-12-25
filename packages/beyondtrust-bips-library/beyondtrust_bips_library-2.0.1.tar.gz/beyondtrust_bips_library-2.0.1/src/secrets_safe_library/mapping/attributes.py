"""
This file contains the fields mapping for each endpoint and version related to
Attributes.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/beyondinsight-apis
- https://docs.beyondtrust.com/bips/docs/password-safe-apis
"""

from secrets_safe_library.constants.endpoints import (
    GET_ATTRIBUTE_ID,
    GET_ATTRIBUTES_ATTRIBUTE_TYPE_ID,
    GET_ATTRIBUTES_MANAGED_ACCOUNT_ID,
    GET_ATTRIBUTES_MANAGED_SYSTEM_ID,
    POST_ATTRIBUTE_ATTRIBUTE_TYPE_ID,
    POST_ATTRIBUTE_MANAGED_ACCOUNT_ID,
    POST_ATTRIBUTE_MANAGED_SYSTEM_ID,
)
from secrets_safe_library.constants.versions import Version

fields = {
    GET_ATTRIBUTES_ATTRIBUTE_TYPE_ID: {
        Version.DEFAULT.value: [
            "AttributeID",
            "AttributeTypeID",
            "ParentAttributeID",
            "ShortName",
            "LongName",
            "Description",
            "ValueInt",
            "IsReadOnly",
            "ChildAttributes",
        ],
    },
    GET_ATTRIBUTE_ID: {
        Version.DEFAULT.value: [
            "AttributeID",
            "AttributeTypeID",
            "ParentAttributeID",
            "ShortName",
            "LongName",
            "Description",
            "ValueInt",
            "IsReadOnly",
            "ChildAttributes",
        ]
    },
    POST_ATTRIBUTE_ATTRIBUTE_TYPE_ID: {
        Version.DEFAULT.value: {
            "ParentAttributeID": int,
            "ShortName": str,
            "LongName": str,
            "Description": str,
            "ValueInt": int,
        },
    },
    GET_ATTRIBUTES_MANAGED_ACCOUNT_ID: {
        Version.DEFAULT.value: [
            "AttributeID",
            "AttributeTypeID",
            "ParentAttributeID",
            "ShortName",
            "LongName",
            "Description",
            "IsReadOnly",
        ],
    },
    GET_ATTRIBUTES_MANAGED_SYSTEM_ID: {
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
    POST_ATTRIBUTE_MANAGED_ACCOUNT_ID: {
        Version.DEFAULT.value: {
            "AttributeID": int,
            "AttributeTypeID": int,
            "ParentAttributeID": int,
            "ShortName": str,
            "LongName": str,
            "Description": str,
            "IsReadOnly": bool,
        },
    },
    POST_ATTRIBUTE_MANAGED_SYSTEM_ID: {
        Version.DEFAULT.value: {
            "AttributeID": int,
            "AttributeTypeID": int,
            "ParentAttributeID": int,
            "ShortName": str,
            "LongName": str,
            "Description": str,
            "ValueInt": int,
            "IsReadOnly": bool,
        },
    },
}
