"""EPM Policies module, all the logic to manage EPM Policies from BI API"""

import logging

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.constants.endpoints import (
    POST_EPM_POLICIES_ID_EPMAPPLICATIONS_ADD,
)
from secrets_safe_library.constants.versions import Version
from secrets_safe_library.core import APIObject
from secrets_safe_library.mapping.epm_policies import fields as epm_fields


class EPMPolicies(APIObject):
    """Class to interact with EPM Policies in BI API."""

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/epmpolicies")

        # Schema rules used for validations
        self._schema = {
            "policy_id": {"type": "string", "nullable": False},
            "group_name": {"type": "string", "maxlength": 128, "nullable": False},
            "name": {"type": "string", "maxlength": 128, "nullable": False},
            "path": {"type": "string", "maxlength": 256, "nullable": False},
            "publisher": {"type": "string", "maxlength": 128, "nullable": False},
            "children_inherit_token": {"type": "boolean", "nullable": False},
        }
        self._validator = Validator(self._schema)

    def add_epm_application(
        self,
        *,
        policy_id: str,
        group_name: str,
        name: str,
        path: str,
        publisher: str,
        children_inherit_token: bool,
    ) -> None:
        """
        Edits a policy to add an application, and updates this policy in the
        BeyondInsight database. Touches the LastModifiedDate to indicate that a change
        is made. Updated policy is deployed to agents per the usual process in
        BeyondInsight.

        API: POST /epmpolicies/{id}/epmapplications/add

        Args:
            policy_id (str): The GUID of the policy to update.
            group_name (str): The name of the group to add the application to.
            name (str): The name of the application.
            path (str): The path to the application.
            publisher (str): The publisher of the application.
            children_inherit_token (bool): Whether child applications inherit the token.

        Returns:
            None
        """

        attributes = {
            "policy_id": policy_id,
            "group_name": group_name,
            "name": name,
            "path": path,
            "publisher": publisher,
            "children_inherit_token": children_inherit_token,
        }

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"{self.endpoint}/{policy_id}/epmapplications/add"

        req_structure = self.get_request_body_version(
            epm_fields, POST_EPM_POLICIES_ID_EPMAPPLICATIONS_ADD, Version.DEFAULT.value
        )

        req_body = self.generate_request_body(req_structure, **attributes)

        utils.print_log(
            self._logger,
            "Calling add_epm_application endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(
            endpoint,
            payload=req_body,
            include_api_version=False,
            expected_status_code=200,
        )

        return response.json()
