"""Custom validator for Cerberus."""

import ipaddress
import logging
import uuid

from cerberus import Validator

from secrets_safe_library import exceptions, utils


class CustomValidator(Validator):
    def _validate_is_required_if(self, is_required_if, field, value):
        """
        Custom rule to make a field required if another field has a specific value.

        The rule's arguments are validated against this schema:
        {'type': 'dict', 'schema': {'field': {'type': 'string'}, 'value': {}}}
        """
        other_field = is_required_if["field"]
        required_value = is_required_if["value"]

        # Check if the other field exists and has the required value
        if (
            other_field in self.document
            and self.document[other_field] == required_value
        ):
            if value is None or value == "":
                self._error(
                    field,
                    f"'{field}' is required when '{other_field}' is {required_value}",
                )

    def _validate_is_ip(self, is_ip, field, value):
        """Custom validation rule to check if a value is a valid IP address.

        The rule's arguments are validated against this schema:
        {'type': 'boolean'}
        """
        if is_ip and value:
            try:
                ipaddress.ip_address(value)  # Validate IP address
            except ValueError:
                self._error(field, f"'{value}' is not a valid IP address.")

    def _validate_is_uuid(self, is_uuid, field, value):
        """Custom validation rule to check if a value is a valid UUID.

        The rule's arguments are validated against this schema:
        {'type': 'boolean'}
        """
        if is_uuid and value:
            try:
                uuid.UUID(value)  # Validate UUID
            except ValueError:
                self._error(field, f"'{value}' is not a valid UUID.")


class BaseValidator:
    """Base class for validators."""

    def validate(
        self,
        data: dict,
        schema: dict,
        allow_unknown: bool = False,
        update: bool = False,
    ) -> dict:
        """
        Validate data using the provided schema.

        Args:
            data (dict): Data to validate.
            schema (dict): Schema to validate against.
            allow_unknown (bool): Whether to allow unknown fields in the data.
            update (bool): Whether the validation is for an update operation.

        Raises:
            exceptions.OptionsError: If validation fails, an error is raised with
            details.

        Returns:
            dict: The validated data if validation is successful.
        """
        validator = CustomValidator(schema, allow_unknown=allow_unknown)

        if not validator.validate(data, update=update):
            utils.print_log(
                self._logger,
                f"Validation failed: {validator.errors}",
                logging.ERROR,
            )
            raise exceptions.OptionsError(f"Please check: {validator.errors}")

        return validator.document
