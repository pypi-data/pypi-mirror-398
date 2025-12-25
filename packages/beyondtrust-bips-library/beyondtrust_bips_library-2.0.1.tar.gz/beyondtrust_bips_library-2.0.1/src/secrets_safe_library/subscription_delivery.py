"""Subscription Delivery module, all the logic to manage Subscription
Delivery from PS API"""

import logging

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject
from secrets_safe_library.mixins import ListMixin


class SubscriptionDelivery(APIObject, ListMixin):
    """Class to interact with Subscription Deliveries in PS API."""

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/subscriptions/delivery")

        # Schema rules used for validations
        self._schema = {
            "id": {"type": "integer", "nullable": False},
        }
        self._validator = Validator(self._schema)

    def download(self, request_id: int) -> list:
        """
        Downloads a specific subscription delivery by ID.

        API: POST Subscriptions/Delivery/download?id={id}

        Args:
            request_id (int): ID of the request for which to retrieve the subscription
                delivery.

        Returns:
            list: List of delivery details including ReportDeliveryId, ScheduleId,
                  Filename, ApplicationType, and Snapshot.
        """

        attributes = {"id": request_id}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"{self.endpoint}/download/id={request_id}"

        utils.print_log(
            self._logger,
            "Calling download_subscription_delivery endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(
            endpoint,
            payload={},
            include_api_version=False,
            expected_status_code=200,
        )

        return response.json()
