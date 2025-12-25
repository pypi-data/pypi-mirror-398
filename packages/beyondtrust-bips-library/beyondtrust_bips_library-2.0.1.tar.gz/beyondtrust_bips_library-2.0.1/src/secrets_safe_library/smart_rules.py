"""SmartRules module, all the logic to manage Smart Rules from BeyondInsight API"""

import logging

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.constants.endpoints import (
    POST_SMART_RULES_FILTER_ASSET_ATTRIBUTE,
)
from secrets_safe_library.constants.versions import Version
from secrets_safe_library.core import APIObject
from secrets_safe_library.mapping.smart_rules import fields as smart_rules_fields
from secrets_safe_library.mixins import (
    DeleteByIdMixin,
    DeleteByKeyMixin,
    GetByIdMixin,
    ListByKeyMixin,
    ListMixin,
)


class SmartRule(
    APIObject,
    DeleteByIdMixin,
    DeleteByKeyMixin,
    GetByIdMixin,
    ListMixin,
    ListByKeyMixin,
):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/smartrules")

        # Schema rules used for validations
        self._schema = {
            "title": {"type": "string", "maxlength": 75, "nullable": True},
            "rule_id": {"type": "integer", "nullable": True},
            "category": {"type": "string", "maxlength": 50, "nullable": True},
            "description": {"type": "string", "nullable": True},
            "process_immediately": {
                "type": "boolean",
                "default": True,
                "nullable": True,
            },
            "attribute_ids": {
                "type": "list",
                "schema": {"type": "integer"},
                "minlength": 1,
                "nullable": True,
            },
        }
        self._validator = Validator(self._schema)

    def list_assets_by_smart_rule_id(
        self, smart_rule_id: int, limit: int = None, offset: int = None
    ) -> list:
        """
        Returns a list of assets for the given smart rule ID.

        API: GET SmartRules/{id}/Assets

        Args:
            smart_rule_id (int): The Smart Rule ID.
            limit (int, optional): limit the results.
            offset (int, optional): skip the first (offset) number of assets.

        Returns:
            list: List of assets for the specified smart_rule_id.
        """

        attributes = {"rule_id": smart_rule_id}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        params = {
            "limit": limit,
            "offset": offset,
        }
        query_string = self.make_query_string(params)

        endpoint = f"/smartrules/{smart_rule_id}/assets?{query_string}"

        utils.print_log(
            self._logger,
            "Calling list_assets_by_smart_rule_id endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint)

        return response.json()

    def create_filter_asset_attribute(
        self,
        attribute_ids: list[int],
        title: str,
        category: str = "Smart Rules",
        description: str = "",
        process_immediately: bool = True,
    ) -> dict:
        """
        Creates a new Smart Rule with the attributes referenced by ID.

        API: POST SmartRules/FilterAssetAttribute

        Args:
            attribute_ids (list): List of attribute IDs to filter by.
            title (str): The title/name of the new Smart Rule, max 75 characters.
            category (str, optional): The category in which to place the Smart Rule,
                default 'Smart Rules', max string length is 50.
            description (str, optional): The Smart Rule description.
            process_immediately (bool, optional): True to process immediately, default
                True.

        Returns:
            dict: The created Smart Rule.
        """

        attributes = {
            "title": title,
            "category": category,
            "description": description,
            "attribute_ids": attribute_ids,
            "process_immediately": process_immediately,
        }

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        req_structure = self.get_request_body_version(
            smart_rules_fields,
            POST_SMART_RULES_FILTER_ASSET_ATTRIBUTE,
            Version.DEFAULT.value,
        )
        req_body = self.generate_request_body(req_structure, **attributes)

        endpoint = f"{self.endpoint}/filterassetattribute"

        utils.print_log(
            self._logger,
            "Calling filterassetattribute endpoint with payload",
            logging.DEBUG,
        )
        response = self._run_post_request(
            endpoint, payload=req_body, include_api_version=False
        )

        return response.json()

    def list_smart_rules_by_user_group_id(self, user_group_id: int) -> list:
        """
        Returns a list of Smart Rules to which the given user group ID has at least
        read access.

        API: GET UserGroups/{id}/SmartRules

        Args:
            user_group_id (int): The User Group ID.

        Returns:
            list: List of Smart Rules for the specified user_group_id.
        """

        endpoint = f"/usergroups/{user_group_id}/smartrules"

        utils.print_log(
            self._logger,
            "Calling list_smart_rules_by_user_group_id endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint)

        return response.json()

    def run_smart_rule(
        self, smart_rule_id: int, queue: bool = False
    ) -> tuple[dict, int]:
        """
        Processes a Smart Rule by ID.

        Response codes:
            200: Request successful. Smart Rule in the response body.
            409: Conflict: the Smart Rule is currently processing.

        API: POST SmartRules/{id}/Process

        Args:
            smart_rule_id (int): The Smart Rule ID.
            queue (bool, optional): True to queue the Smart Rule for processing,
                False to process it immediately. Defaults to False.

        Returns:
            tuple: A tuple containing the response JSON and the int status code.
        """

        endpoint = f"/smartrules/{smart_rule_id}/process?queue={str(queue).lower()}"

        utils.print_log(
            self._logger,
            "Calling process_smart_rule_by_id endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(
            endpoint, payload={}, expected_status_code=[200, 409]
        )
        status_code = response.status_code

        return response.json(), status_code
