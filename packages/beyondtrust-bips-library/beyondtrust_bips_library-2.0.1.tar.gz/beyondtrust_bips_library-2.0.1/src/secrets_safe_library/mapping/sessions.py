"""
This file contains the fields mapping for each endpoint and version related to
Sessions.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/passwordsafe-api
"""

from secrets_safe_library.constants.endpoints import (
    GET_SESSIONS,
    GET_SESSIONS_ID,
    POST_SESSIONS_ADMIN,
    POST_SESSIONS_REQUEST_ID,
)
from secrets_safe_library.constants.versions import Version

fields = {
    GET_SESSIONS: {
        Version.DEFAULT.value: [
            "SessionID",
            "UserID",
            "NodeID",
            "Status",
            "ArchiveStatus",
            "Protocol",
            "StartTime",
            "EndTime",
            "Duration",
            "AssetName",
            "ManagedSystemID",
            "ManagedAccountID",
            "ManagedAccountName",
            "RecordKey",
            "Token",
            "ApplicationID",
            "RequestID",
            "SessionType",
        ],
    },
    GET_SESSIONS_ID: {
        Version.DEFAULT.value: [
            "SessionID",
            "UserID",
            "NodeID",
            "Status",
            "ArchiveStatus",
            "Protocol",
            "StartTime",
            "EndTime",
            "Duration",
            "AssetName",
            "ManagedSystemID",
            "ManagedAccountID",
            "ManagedAccountName",
            "RecordKey",
            "Token",
            "ApplicationID",
            "RequestID",
            "SessionType",
        ],
    },
    POST_SESSIONS_REQUEST_ID: {
        Version.DEFAULT.value: {
            "SessionType": str,
            "NodeID": str,
        },
    },
    POST_SESSIONS_ADMIN: {
        Version.DEFAULT.value: {
            "SessionType": str,
            "HostName": str,
            "Port": int,
            "DomainName": str,
            "UserName": str,
            "Password": str,
            "Reason": str,
            "Resolution": str,
            "RDPAdminSwitch": bool,
            "SmartSizing": bool,
            "NodeID": str,
            "Record": bool,
        },
    },
}
