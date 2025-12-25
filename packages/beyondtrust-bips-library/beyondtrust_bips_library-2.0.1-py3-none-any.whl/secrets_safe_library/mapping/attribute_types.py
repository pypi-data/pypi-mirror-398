"""
This file contains the fields mapping for each endpoint and version related to
Attribute Types.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/beyondinsight-api
"""

from secrets_safe_library.constants.endpoints import (
    GET_ATTRIBUTE_TYPES,
    GET_ATTRIBUTE_TYPES_ID,
    POST_ATTRIBUTE_TYPES,
)
from secrets_safe_library.constants.versions import Version

fields = {
    GET_ATTRIBUTE_TYPES: {
        Version.DEFAULT.value: [
            "AttributeTypeID",
            "Name",
            "IsReadOnly",
        ]
    },
    GET_ATTRIBUTE_TYPES_ID: {
        Version.DEFAULT.value: [
            "AttributeTypeID",
            "Name",
            "IsReadOnly",
        ]
    },
    POST_ATTRIBUTE_TYPES: {
        Version.DEFAULT.value: [
            "Name",
        ]
    },
}
