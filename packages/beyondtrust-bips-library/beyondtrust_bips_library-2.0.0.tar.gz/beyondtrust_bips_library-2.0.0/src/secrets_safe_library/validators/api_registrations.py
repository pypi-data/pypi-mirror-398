from secrets_safe_library.constants.versions import Version
from secrets_safe_library.validators.base import BaseValidator


class _APIRegistrationSchemaValidator:
    def __init__(self):
        self.common_schema = {
            "access_token_duration": {"type": "integer", "min": 1, "nullable": True},
            "active": {"type": "boolean", "default": True},
            "visible": {"type": "boolean", "default": True},
            "multi_factor_authentication_enforced": {
                "type": "boolean",
                "default": False,
            },
            "client_certificate_required": {"type": "boolean", "default": False},
            "user_password_required": {"type": "boolean", "default": False},
            "verify_psrun_signature": {"type": "boolean", "default": False},
            "ip_authentication_rules": {
                "type": "list",
                "schema": {
                    "type": "dict",
                    "schema": {
                        "Type": {"type": "string", "nullable": False},
                        "Value": {"type": "string", "nullable": False},
                        "Description": {"type": "string", "nullable": True},
                    },
                },
                "nullable": True,
            },
            "psrun_rules": {
                "type": "list",
                "schema": {
                    "type": "dict",
                    "schema": {
                        "Id": {"type": "integer", "nullable": True},
                        "IPAddress": {"type": "string", "nullable": True},
                        "MacAddress": {"type": "string", "nullable": True},
                        "SystemName": {"type": "string", "nullable": True},
                        "FQDN": {"type": "string", "nullable": True},
                        "DomainName": {"type": "string", "nullable": True},
                        "UserId": {"type": "string", "nullable": True},
                        "RootVolumeId": {"type": "string", "nullable": True},
                        "OSVersion": {"type": "string", "nullable": True},
                    },
                },
                "nullable": True,
            },
            "x_forwarded_for_authentication_rules": {
                "type": "list",
                "schema": {
                    "type": "dict",
                    "schema": {
                        "Type": {"type": "string", "nullable": False},
                        "Value": {"type": "string", "nullable": False},
                        "Description": {"type": "string", "nullable": True},
                    },
                },
                "nullable": True,
            },
        }

    def get_create_schema(self, version: str = Version.DEFAULT.value) -> dict:
        """
        Get schema for creating API registrations.

        Args:
            version (str): The version (e.g., '3.0', '3.1', '3.2', '3.3', 'DEFAULT')

        Returns:
            dict: The schema for create operation.
        """
        schema = self.common_schema.copy()
        schema["name"] = {"type": "string", "maxlength": 256, "nullable": False}
        schema["registration_type"] = {
            "type": "string",
            "allowed": ["apikeypolicy", "apiaccesspolicy"],
            "nullable": False,
        }
        return schema

    def get_update_schema(self, version: str = Version.DEFAULT.value) -> dict:
        """
        Get schema for updating API registrations.

        Args:
            version (str): The version (e.g., '3.0', '3.1', '3.2', '3.3', 'DEFAULT')

        Returns:
            dict: The schema for update operation.
        """
        schema = self.common_schema.copy()
        schema["registration_id"] = {"type": "integer", "nullable": False}
        schema["name"] = {"type": "string", "maxlength": 256, "nullable": True}
        schema["registration_type"] = {
            "type": "string",
            "allowed": ["apikeypolicy", "apiaccesspolicy"],
            "nullable": True,
        }
        return schema

    def get_get_key_schema(self, version: str = Version.DEFAULT.value) -> dict:
        """
        Get schema for getting API key by ID.

        Args:
            version (str): The version (e.g., '3.0', '3.1', '3.2', '3.3', 'DEFAULT')

        Returns:
            dict: The schema for get key operation.
        """
        return {"api_registration_id": {"type": "integer", "nullable": False}}

    def get_rotate_key_schema(self, version: str = Version.DEFAULT.value) -> dict:
        """
        Get schema for rotating API key.

        Args:
            version (str): The version (e.g., '3.0', '3.1', '3.2', '3.3', 'DEFAULT')

        Returns:
            dict: The schema for rotate key operation.
        """
        return {"api_registration_id": {"type": "integer", "nullable": False}}


class APIRegistrationValidator(BaseValidator):
    """Validator for API registration operations."""

    def __init__(self):
        self.schema_validator = _APIRegistrationSchemaValidator()

    def get_schema(self, operation: str, version: str = Version.DEFAULT.value) -> dict:
        """
        Retrieve the schema for the specified operation and version.

        Args:
            operation (str): The operation type (e.g., 'create', 'update',
                'get_key', 'rotate_key').
            version (str): The version (e.g., '3.0', '3.1', '3.2', '3.3', 'DEFAULT')

        Returns:
            dict: The schema for the specified operation and version.
        """
        if operation == "create":
            return self.schema_validator.get_create_schema(version)

        if operation == "update":
            return self.schema_validator.get_update_schema(version)

        if operation == "get_key":
            return self.schema_validator.get_get_key_schema(version)

        if operation == "rotate_key":
            return self.schema_validator.get_rotate_key_schema(version)

        raise ValueError(f"Unsupported operation: {operation}")

    def validate(
        self,
        data: dict,
        operation: str,
        version: str = Version.DEFAULT.value,
        allow_unknown: bool = True,
        update: bool = False,
    ) -> dict:
        """
        Validate data for API registration operations.

        Args:
            data (dict): Data to validate.
            operation (str): The operation type (e.g., 'create', 'update',
                'get_key', 'rotate_key').
            version (str): The version (e.g., '3.0', '3.1', '3.2', '3.3', 'DEFAULT')
            allow_unknown (bool): Whether to allow unknown fields in the data.
            update (bool): Whether the validation is for an update operation.

        Returns:
            dict: The validated data.
        """
        schema = self.get_schema(operation, version)
        data = super().validate(data, schema, allow_unknown, update)
        return data
