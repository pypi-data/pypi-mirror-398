"""
Propagation Actions module, all the logic to manage Propagation Actions
from Password Safe API
"""

import logging

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.constants.endpoints import (
    POST_MANAGED_ACCOUNT_PROPAGATION_ACTIONS,
)
from secrets_safe_library.constants.versions import Version
from secrets_safe_library.core import APIObject
from secrets_safe_library.mapping.propagation_actions import (
    fields as propagation_actions_fields,
)
from secrets_safe_library.mixins import GetByIdMixin, ListMixin


class PropagationActions(APIObject, ListMixin, GetByIdMixin):
    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/propagationactions")

        # Schema rules used for validations
        self._schema = {
            "smart_rule_id": {"type": "integer", "nullable": True},
            "managed_account_id": {"type": "integer", "min": 1, "nullable": False},
            "propagation_action_id": {"type": "integer", "min": 1, "nullable": False},
        }

        self._validator = Validator(self._schema)

    def get_managed_account_propagation_actions(self, managed_account_id: int) -> list:
        """
        Retrieve a list of propagation actions for a specific managed account.

        API: GET /ManagedAccounts/{managed_account_id}/PropagationActions

        Args:
            managed_account_id (int): The ID of the managed account.

        Returns:
            list: A list of propagation actions for the specified managed account.
        """

        attributes = {"managed_account_id": managed_account_id}

        if not self._validator.validate(attributes):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"/managedaccounts/{managed_account_id}{self.endpoint}"

        utils.print_log(
            self._logger,
            "Calling get_managed_account_propagation_actions endpoint",
            logging.DEBUG,
        )

        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def post_managed_account_propagation_action_by_id(
        self,
        managed_account_id: int,
        propagation_action_id: int,
        smart_rule_id: int = None,
    ) -> dict:
        """
        Assigns a propagation action to the managed account referenced by ID.

        API: POST
        /ManagedAccounts/{managed_account_id}/PropagationActions/{propagation_action_id}

        Args:
            managed_account_id (int): The ID of the managed account.
            propagation_action_id (int): The ID of the propagation action to initiate.
            smart_rule_id (int, optional): The ID of the smart rule to associate with
                                           the propagation action.

        Returns:
            dict: The response from the API after initiating the propagation action.
        """

        attributes = {
            "smart_rule_id": smart_rule_id,
            "managed_account_id": managed_account_id,
            "propagation_action_id": propagation_action_id,
        }

        if not self._validator.validate(attributes):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        req_structure = self.get_request_body_version(
            propagation_actions_fields,
            POST_MANAGED_ACCOUNT_PROPAGATION_ACTIONS,
            Version.DEFAULT.value,
        )

        req_body = self.generate_request_body(
            req_structure,
            smart_rule_id=smart_rule_id,
        )

        endpoint = (
            f"/managedaccounts/{managed_account_id}{self.endpoint}/"
            f"{propagation_action_id}"
        )

        utils.print_log(
            self._logger,
            "Calling post_managed_account_propagation_action_by_id endpoint",
            logging.DEBUG,
        )

        response = self._run_post_request(
            endpoint,
            req_body,
            include_api_version=False,
            expected_status_code=[200, 201],
        )

        return response.json()

    def delete_managed_account_propagation_action(
        self, managed_account_id: int
    ) -> None:
        """
        Unassigns all propagation actions from the managed account by ID.

        API: DELETE /ManagedAccounts/{managed_account_id}/PropagationActions

        Args:
            managed_account_id (int): The ID of the managed account.

        Returns:
            None
        """
        attributes = {
            "managed_account_id": managed_account_id,
        }

        if not self._validator.validate(attributes):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"/managedaccounts/{managed_account_id}{self.endpoint}"

        utils.print_log(
            self._logger,
            "Calling delete_managed_account_propagation_action endpoint",
            logging.DEBUG,
        )

        self._run_delete_request(endpoint)

    def delete_managed_account_propagation_action_by_id(
        self, managed_account_id: int, propagation_action_id: int
    ) -> None:
        """
        Unassigns a propagation action from the managed account by ID.

        API: DELETE /ManagedAccounts/{managed_account_id}/PropagationActions/
             {propagation_action_id}

        Args:
            managed_account_id (int): The ID of the managed account.
            propagation_action_id (int): The ID of the propagation action to unassign.

        Returns:
            None
        """
        attributes = {
            "managed_account_id": managed_account_id,
            "propagation_action_id": propagation_action_id,
        }

        if not self._validator.validate(attributes):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = (
            f"/managedaccounts/{managed_account_id}{self.endpoint}/"
            f"{propagation_action_id}"
        )

        utils.print_log(
            self._logger,
            "Calling delete_managed_account_propagation_action_by_id endpoint",
            logging.DEBUG,
        )

        self._run_delete_request(endpoint)
