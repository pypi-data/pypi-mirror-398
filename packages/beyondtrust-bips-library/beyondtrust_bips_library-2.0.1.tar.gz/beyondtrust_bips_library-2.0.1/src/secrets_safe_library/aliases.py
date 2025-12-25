"""Aliases module, all the logic to manage aliases from PS API"""

import logging
from typing import List

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject
from secrets_safe_library.mixins import GetByIdMixin, ListByKeyMixin


class Aliases(APIObject, ListByKeyMixin, GetByIdMixin):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/aliases")

        # Schema rules used for validations
        self._schema = {
            "state": {
                "type": ["integer", "list"],
                "nullable": True,
                "default": [1, 2],
                "schema": {"type": "integer", "allowed": [0, 1, 2]},
                "allowed": [0, 1, 2],
            }
        }
        self._validator = Validator(self._schema)

    def get_aliases(self, state: int | List[int] = [1, 2]):
        """
        Retrieve a list of aliases.

        Args:
            state (int | List[int], optional): Zero or more state values. (Default: 1,2)
                                   i.e., 'state=2', 'state=1,2', 'state=0,1,2'.
                        - 0: Unmapped
                        - 1: Mapped
                        - 2: Highly Available

        Returns:
            list: A list of aliases.
        """

        params = {"state": state}

        if not self._validator.validate(params):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        if isinstance(state, list):
            state = ",".join(map(str, state))

        endpoint = f"{self.endpoint}?state={state}"

        utils.print_log(self._logger, "Calling get_aliases endpoint", logging.DEBUG)

        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()
