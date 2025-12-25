from secrets_safe_library.validators.base import BaseValidator


class _FunctionalAccountValidator:
    common_schema = {}

    def get_create_schema(self):
        """
        Returns the schema for creating a functional account.
        """
        return {
            **self.common_schema,
            "platform_id": {"type": "integer", "nullable": False},
            "domain_name": {"type": "string", "maxlength": 500, "nullable": True},
            "account_name": {
                "type": "string",
                "maxlength": 245,
                "nullable": False,
            },
            "display_name": {
                "type": "string",
                "maxlength": 100,
                "nullable": True,
            },
            "password": {
                "type": "string",
                "maxlength": 1000,
                "nullable": True,
                "is_required_if": {
                    "field": "requires_secret",
                    "value": False,
                },
            },
            "private_key": {  # Comes from SSHConfig
                "type": "string",
                "nullable": True,
            },
            "passphrase": {  # Comes from SSHConfig
                "type": "string",
                "nullable": True,
            },
            "description": {
                "type": "string",
                "maxlength": 1000,
                "nullable": True,
            },
            "elevation_command": {  # Comes from SSHConfig
                "type": "string",
                "maxlength": 80,
                "nullable": True,
            },
            "tenant_id": {
                "type": "string",
                "maxlength": 36,
                "nullable": True,
            },
            "object_id": {
                "type": "string",
                "maxlength": 36,
                "nullable": True,
            },
            "secret": {
                "type": "string",
                "maxlength": 255,
                "nullable": True,
            },
            "service_account_email": {
                "type": "string",
                "maxlength": 255,
                "nullable": True,
            },
            "azure_instance": {
                "type": "string",
                "allowed": ["AzurePublic", "AzureUsGovernment"],
                "nullable": True,
            },
        }


class FunctionalAccountValidator(BaseValidator):
    """Validator for functional accounts operations."""

    def __init__(self):
        self.schema_validator = _FunctionalAccountValidator()

    def get_schema(self, operation: str) -> dict:
        """
        Retrieve the schema for the specified operation.

        Args:
            operation (str): The operation type (e.g., 'list', 'create').

        Returns:
            dict: The schema for the specified operation and version.
        """
        if operation == "create":
            return self.schema_validator.get_create_schema()

        raise ValueError(f"Unsupported operation: {operation}")

    def validate(
        self,
        data: dict,
        operation: str,
        allow_unknown: bool = True,
        update: bool = False,
    ) -> dict:
        schema = self.get_schema(operation)
        data = super().validate(data, schema, allow_unknown, update)
        return data
