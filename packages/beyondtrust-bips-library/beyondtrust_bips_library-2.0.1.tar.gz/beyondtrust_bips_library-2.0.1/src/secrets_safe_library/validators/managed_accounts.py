from secrets_safe_library.validators.base import BaseValidator


class _ManagedAccountValidator:

    def get_list_schema(self) -> dict:
        return {
            "system_name": {"type": "string", "maxlength": 129, "nullable": True},
            "account_name": {"type": "string", "maxlength": 246, "nullable": True},
            "system_id": {"type": "integer", "nullable": True},
            "workgroup_name": {"type": "string", "maxlength": 256, "nullable": True},
            "application_display_name": {
                "type": "string",
                "maxlength": 256,
                "nullable": True,
            },
            "ip_address": {"type": "string", "maxlength": 45, "nullable": True},
            "type": {
                "type": "string",
                "allowed": [
                    "system",
                    "recent",
                    "domainlinked",
                    "database",
                    "cloud",
                    "application",
                ],
                "nullable": True,
            },
            "limit": {"type": "integer", "min": 1, "max": 1000, "default": 1000},
            "offset": {"type": "integer", "min": 0, "default": 0},
        }

    def get_create_schema(self) -> dict:
        """
        Returns the schema for creating a managed account.
        """
        return {
            "system_id": {"type": "integer", "nullable": False},
            "account_name": {"type": "string", "maxlength": 245, "nullable": False},
            "password": {
                "type": "string",
                "maxlength": 1000,
                "nullable": True,
                "is_required_if": {
                    "field": "auto_management_flag",
                    "value": False,
                },
            },
            "domain_name": {"type": "string", "maxlength": 50, "nullable": True},
            "user_principal_name": {
                "type": "string",
                "maxlength": 500,
                "nullable": True,
            },
            "sam_account_name": {"type": "string", "maxlength": 20, "nullable": True},
            "distinguished_name": {
                "type": "string",
                "maxlength": 1000,
                "nullable": True,
            },
            "private_key": {"type": "string", "nullable": True},
            "passphrase": {"type": "string", "nullable": True},
            "password_fallback_flag": {"type": "boolean", "default": False},
            "login_account_flag": {"type": "boolean", "default": False},
            "description": {"type": "string", "maxlength": 1024, "nullable": True},
            "password_rule_id": {"type": "integer", "default": 0},
            "api_enabled": {"type": "boolean", "default": False},
            "release_notification_email": {
                "type": "string",
                "maxlength": 255,
                "nullable": True,
            },
            "change_services_flag": {"type": "boolean", "default": False},
            "restart_services_flag": {"type": "boolean", "default": False},
            "change_tasks_flag": {"type": "boolean", "default": False},
            "release_duration": {
                "type": "integer",
                "min": 1,
                "max": 525600,
                "default": 120,
            },
            "max_release_duration": {
                "type": "integer",
                "min": 1,
                "max": 525600,
                "default": 525600,
            },
            "isa_release_duration": {
                "type": "integer",
                "min": 1,
                "max": 525600,
                "default": 120,
            },
            "max_concurrent_requests": {
                "type": "integer",
                "min": 0,
                "max": 999,
                "default": 1,
            },
            "auto_management_flag": {"type": "boolean", "default": False},
            "dss_auto_management_flag": {"type": "boolean", "default": False},
            "check_password_flag": {"type": "boolean", "default": False},
            "reset_password_on_mismatch_flag": {"type": "boolean", "default": False},
            "change_password_after_any_release_flag": {
                "type": "boolean",
                "default": False,
            },
            "change_frequency_type": {
                "type": "string",
                "allowed": ["first", "last", "xdays"],
                "default": "first",
            },
            "change_frequency_days": {
                "type": "integer",
                "min": 1,
                "max": 999,
                "nullable": True,
                "is_required_if": {
                    "field": "change_frequency_type",
                    "value": "xdays",
                },
            },
            "change_time": {
                "type": "string",
                "regex": r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$",
                "default": "23:30",
            },
            "next_change_date": {
                "type": "string",
                "regex": r"^\d{4}-\d{2}-\d{2}$",
                "nullable": True,
            },
            "use_own_credentials": {"type": "boolean", "default": False},
            "change_iis_app_pool_flag": {"type": "boolean", "default": False},
            "restart_iis_app_pool_flag": {"type": "boolean", "default": False},
            "workgroup_id": {"type": "integer", "nullable": True},
            "change_windows_auto_logon_flag": {"type": "boolean", "default": False},
            "change_com_plus_flag": {"type": "boolean", "default": False},
            "change_dcom_flag": {"type": "boolean", "default": False},
            "change_scom_flag": {"type": "boolean", "default": False},
            "object_id": {"type": "string", "maxlength": 36, "nullable": True},
        }

    def get_update_schema(self) -> dict:
        """Returns the schema for updating a managed account."""
        return {
            "password": {
                "type": "string",
                "maxlength": 1000,
                "nullable": True,
            },
            "public_key": {
                "type": "string",
                "nullable": True,
            },
            "update_system": {"type": "boolean", "default": True},
            "private_key": {"type": "string", "nullable": True},
            "passphrase": {"type": "string", "nullable": True},
        }


class ManagedAccountValidator(BaseValidator):
    """Validator for managed accounts operations."""

    def __init__(self):
        self.schema_validator = _ManagedAccountValidator()

    def get_schema(self, operation: str) -> dict:
        """
        Retrieve the schema for the specified operation.

        Args:
            operation (str): The operation type (e.g., 'list', 'create').

        Returns:
            dict: The schema for the specified operation and version.
        """
        if operation == "list":
            return self.schema_validator.get_list_schema()

        if operation == "create":
            return self.schema_validator.get_create_schema()

        if operation == "update":
            return self.schema_validator.get_update_schema()

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
