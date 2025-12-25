"""QuickRules module, all the logic to manage Quick Rules from PS API"""

import logging

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject
from secrets_safe_library.mixins import (
    DeleteByIdMixin,
    DeleteByKeyMixin,
    GetByIdMixin,
    ListByKeyMixin,
    ListMixin,
)


class QuickRule(
    APIObject,
    DeleteByIdMixin,
    DeleteByKeyMixin,
    GetByIdMixin,
    ListMixin,
    ListByKeyMixin,
):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/quickrules")

        # Schema rules used for validations
        self._schema = {
            "title": {"type": "string", "maxlength": 256, "nullable": True},
            "organization_id": {"type": "integer", "nullable": True},
            "category": {"type": "string", "maxlength": 256, "nullable": True},
            "description": {"type": "string", "maxlength": 512, "nullable": True},
            "rule_type": {
                "type": "string",
                "allowed": ["managedaccount", "managedsystem"],
                "nullable": True,
            },
        }
        self._validator = Validator(self._schema)

    def get_by_org_and_title(self, organization_id: int, title: str = None) -> dict:
        """
        Returns a Quick Rule by organization ID and title.

        API: GET Organizations/{orgID}/QuickRules?title={title}

        Args:
            organization_id (int): The Organization ID.
            title (str, optional): The QuickRule title.

        Returns:
            dict: QuickRule.
        """

        attributes = {"title": title}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        query_string = self.make_query_string(attributes)
        endpoint = f"/organizations/{organization_id}/quickrules?{query_string}"

        utils.print_log(
            self._logger,
            "Calling get_by_org_and_title endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def delete_by_org_and_title(self, organization_id: int, title: str) -> None:
        """
        Deletes a Quick Rule by organization ID and title.
        Only valid in a multi-tenant environment.

        API: DELETE Organizations/{orgID}/QuickRules?title={title}

        Args:
            organization_id (int): The Organization ID.
            title (str): The QuickRule title.

        Returns:
            None.
        """

        attributes = {"title": title}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        query_string = self.make_query_string(attributes)
        endpoint = f"/organizations/{organization_id}/quickrules?{query_string}"

        utils.print_log(
            self._logger,
            "Calling delete_by_org_and_title endpoint",
            logging.DEBUG,
        )
        _ = self._run_delete_request(endpoint)

    def create_quick_rule(
        self,
        ids: list[int],
        title: str,
        category: str = "Quick Rules",
        description: str = "",
        rule_type: str = "ManagedAccount",
    ) -> dict:
        """
        Creates a new Quick Rule with the managed accounts or systems referenced by ID
            and Rule Type.

        Args:
            ids (list): List of IDs to add to the Quick Rule.
            title (str): The title/name of the new Quick Rule.
            category (str, optional): The category in which to place the Quick Rule,
                default 'Quick Rules'.
            description (str, optional): The Quick Rule description.
            rule_type (str, optional): The type of the rule, either 'ManagedAccount' or
                'ManagedSystem', default 'ManagedAccount'.

        Returns:
            dict: The created Quick Rule.
        """
        payload = {
            "IDs": ids,
            "Title": title,
            "Category": category,
            "Description": description,
            "RuleType": rule_type,
        }

        utils.print_log(self._logger, "Creating Quick Rule with payload", logging.DEBUG)
        response = self._run_post_request(self.endpoint, payload=payload)

        return response.json()

    def add_accounts_to_quick_rule(
        self, quick_rule_id: int, account_ids: list[int]
    ) -> dict:
        """
        Updates the entire list of managed accounts in a Quick Rule by removing all
        Managed Account Fields - Quick Group ID filters and adding a new one with the
        managed accounts referenced by ID.

        API: PUT QuickRules/{quickRuleID}/ManagedAccounts

        Args:
            quick_rule_id (int): The ID of the Quick Rule.
            account_ids (list): List of account IDs to add to the Quick Rule.

        Returns:
            dict: The updated Quick Rule.
        """
        payload = {"AccountIDs": account_ids}

        utils.print_log(
            self._logger,
            f"Adding accounts to Quick Rule {quick_rule_id} with payload: {payload}",
            logging.DEBUG,
        )
        endpoint = f"{self.endpoint}/{quick_rule_id}/managedaccounts"
        response = self._run_put_request(endpoint, payload=payload)

        return response.json()
