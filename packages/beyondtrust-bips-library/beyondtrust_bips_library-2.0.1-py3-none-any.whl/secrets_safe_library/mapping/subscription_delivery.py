"""
This file contains the fields mapping for each endpoint and version related to
Subscription Deliveries.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/passwordsafe-apis
"""

from secrets_safe_library.constants.endpoints import (
    POST_SUBSCRIPTIONS_DELIVERY_DOWNLOAD,
)
from secrets_safe_library.constants.versions import Version

fields = {
    POST_SUBSCRIPTIONS_DELIVERY_DOWNLOAD: {
        Version.DEFAULT.value: [
            "ReportDeliveryId",
            "ScheduleId",
            "Filename",
            "ApplicationType",
            "Snapshot",
        ]
    },
}
