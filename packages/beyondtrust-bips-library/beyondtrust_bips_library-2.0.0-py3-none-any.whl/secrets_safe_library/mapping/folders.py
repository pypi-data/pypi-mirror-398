"""
This file contains the fields mapping for each endpoint and version related to FOLDERS.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/passwordsafe-api
- https://docs.beyondtrust.com/bips/docs/secrets-safe-api
"""

from secrets_safe_library.constants.endpoints import (
    GET_SECRETS_SAFE_FOLDERS,
    GET_SECRETS_SAFE_FOLDERS_FOLDERID,
)
from secrets_safe_library.constants.versions import Version

fields = {
    GET_SECRETS_SAFE_FOLDERS: {
        Version.DEFAULT.value: [
            "Id",
            "Name",
            "Description",
            "ParentId",
            "UserGroupId",
            "UserId",
            "FolderOwnerId",
        ],
    },
    GET_SECRETS_SAFE_FOLDERS_FOLDERID: {
        Version.DEFAULT.value: [
            "Id",
            "Name",
            "Description",
            "ParentId",
            "UserGroupId",
            "UserId",
            "FolderOwnerId",
        ],
    },
}
