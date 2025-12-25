"""
This file contains the fields mapping for each endpoint and version related to
Keystrokes.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/passwordsafe-apis
"""

from secrets_safe_library.constants.endpoints import (
    GET_KEYSTROKES_ID,
    GET_SESSIONS_SESSIONID_KEYSTROKES,
    POST_KEYSTROKES_SEARCH,
)
from secrets_safe_library.constants.versions import Version

GET_KEYSTROKES_DEFAULT = [
    "KeystrokeID",
    "SessionID",
    "TimeMarker",
    "Type",
    "Data",
]

fields = {
    GET_SESSIONS_SESSIONID_KEYSTROKES: {Version.DEFAULT.value: GET_KEYSTROKES_DEFAULT},
    GET_KEYSTROKES_ID: {
        Version.DEFAULT.value: GET_KEYSTROKES_DEFAULT,
    },
    POST_KEYSTROKES_SEARCH: {
        Version.DEFAULT.value: {
            "Data": str,
            "Type": int,
        }
    },
}
