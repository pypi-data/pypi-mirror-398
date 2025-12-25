"""
This file contains the fields mapping for each endpoint and version related to Oracle
Internet Directories.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/password-safe-apis
"""

from secrets_safe_library.constants.endpoints import (
    GET_ORACLE_INTERNET_DIRECTORIES,
    GET_ORACLE_INTERNET_DIRECTORIES_ID,
    POST_ORACLE_INTERNET_DIRECTORIES_ID_SERVICES_QUERY,
    POST_ORACLE_INTERNET_DIRECTORIES_ID_TEST,
)
from secrets_safe_library.constants.versions import Version

fields = {
    GET_ORACLE_INTERNET_DIRECTORIES: {
        Version.DEFAULT.value: [
            "OrganizationID",
            "OracleInternetDirectoryID",
            "Name",
            "Description",
        ],
    },
    GET_ORACLE_INTERNET_DIRECTORIES_ID: {
        Version.DEFAULT.value: [
            "OrganizationID",
            "OracleInternetDirectoryID",
            "Name",
            "Description",
        ],
    },
    POST_ORACLE_INTERNET_DIRECTORIES_ID_SERVICES_QUERY: {
        Version.DEFAULT.value: [
            "Success",
            "Message",
            "Services",
        ]
    },
    POST_ORACLE_INTERNET_DIRECTORIES_ID_TEST: {
        Version.DEFAULT.value: [
            "Success",
        ],
    },
}
