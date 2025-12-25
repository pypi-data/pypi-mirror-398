from secrets_safe_library.constants.versions import Version
from secrets_safe_library.validators.base import BaseValidator


class _ManagedSystemSchemaValidator:
    def __init__(self):
        self.common_schema = {
            "contact_email": {"type": "string", "maxlength": 1000, "nullable": False},
            "description": {"type": "string", "maxlength": 255, "nullable": True},
            "timeout": {"type": "integer", "min": 1, "max": 3600, "default": 30},
            "password_rule_id": {"type": "integer", "nullable": False, "default": 0},
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
            "auto_management_flag": {"type": "boolean", "default": False},
            "functional_account_id": {"type": "integer", "nullable": True},
            "check_password_flag": {"type": "boolean", "default": False},
            "change_password_after_any_release_flag": {
                "type": "boolean",
                "default": False,
            },
            "reset_password_on_mismatch_flag": {"type": "boolean", "default": False},
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
            },
            "change_time": {
                "type": "string",
                "regex": r"^(?:[01]\d|2[0-3]):[0-5]\d$",  # 24-hour format (HH:MM)
                "default": "23:30",
            },
        }

    def get_asset_schema(self, version: str) -> dict:
        if version == Version.V3_0.value:
            return {
                **self.common_schema,
                "platform_id": {"type": "integer", "nullable": False},
                "port": {"type": "integer", "nullable": True},
                "ssh_key_enforcement_mode": {
                    "type": "integer",
                    "allowed": [0, 1, 2],
                    "nullable": True,
                    "default": 0,
                },
                "dss_key_rule_id": {"type": "integer", "nullable": True, "default": 0},
                "login_account_id": {"type": "integer", "nullable": True},
                "elevation_command": {
                    "type": "string",
                    "allowed": ["sudo", "pbrun", "pmrun"],
                    "nullable": True,
                },
            }
        elif version == Version.V3_1.value:
            schema = self.get_asset_schema(Version.V3_0.value)
            schema["remote_client_type"] = {
                "type": "string",
                "allowed": ["None", "EPM"],
                "nullable": False,
            }
            return schema
        elif version == Version.V3_2.value:
            schema = self.get_asset_schema(Version.V3_1.value)
            schema["application_host_id"] = {"type": "integer", "nullable": True}
            schema["is_application_host"] = {"type": "boolean", "default": False}
            return schema
        else:
            raise ValueError(f"Unsupported version: {version}")

    def get_database_schema(self) -> dict:
        return self.common_schema

    def get_workgroup_schema(self, version: str) -> dict:
        if version == Version.V3_0.value:
            return {
                **self.common_schema,
                "entity_type_id": {"type": "integer", "nullable": False},
                "host_name": {"type": "string", "maxlength": 128, "nullable": False},
                "ip_address": {"type": "string", "maxlength": 45, "nullable": False},
                "dns_name": {"type": "string", "maxlength": 255, "nullable": False},
                "instance_name": {"type": "string", "maxlength": 100, "nullable": True},
                "is_default_instance": {"type": "boolean", "nullable": True},
                "template": {"type": "string", "nullable": True},
                "forest_name": {"type": "string", "maxlength": 64, "nullable": True},
                "use_ssl": {"type": "boolean", "nullable": True, "default": False},
                "platform_id": {"type": "integer", "nullable": False},
                "net_bios_name": {"type": "string", "maxlength": 15, "nullable": True},
                "account_name_format": {
                    "type": "integer",
                    "allowed": [0, 1, 2],
                    "nullable": False,
                },
                "oracle_internet_directory_id": {
                    "type": "string",
                    "regex": r"^[0-9a-fA-F-]{36}$",
                    "nullable": True,
                },
                "oracle_internet_directory_service_name": {
                    "type": "string",
                    "maxlength": 200,
                    "nullable": True,
                },
                "elevation_command": {
                    "type": "string",
                    "allowed": ["sudo", "pbrun", "pmrun"],
                    "nullable": True,
                },
                "access_url": {"type": "string", "maxlength": 2048, "nullable": True},
                "ssh_key_enforcement_mode": {
                    "type": "integer",
                    "allowed": [0, 1, 2],
                    "nullable": True,
                    "default": 0,
                },
            }
        elif version == Version.V3_1.value:
            schema = self.get_workgroup_schema(Version.V3_0.value)
            schema["remote_client_type"] = {
                "type": "string",
                "allowed": ["None", "EPM"],
                "nullable": True,
            }
            return schema
        elif version == Version.V3_2.value:
            schema = self.get_workgroup_schema(Version.V3_1.value)
            schema["application_host_id"] = {"type": "integer", "nullable": True}
            schema["is_application_host"] = {"type": "boolean", "default": False}
            return schema
        elif version == Version.V3_3.value:
            return self.get_workgroup_schema(Version.V3_2.value)
        else:
            raise ValueError(f"Unsupported version: {version}")

    def get_update_schema(self, version: str) -> dict:
        return self.get_workgroup_schema(version)


class ManagedSystemValidator(BaseValidator):
    """Validator for managed systems operations."""

    def __init__(self):
        self.schema_validator = _ManagedSystemSchemaValidator()

    def get_schema(self, operation: str, version: str = Version.DEFAULT.value) -> dict:
        """
        Retrieve the schema for the specified operation and version.

        Args:
            operation (str): The operation type (e.g., 'create_by_asset',
                'create_by_database', 'create_by_workgroup').
            version (str): The version (e.g., '3.0', '3.1', '3.2', '3.3', 'DEFAULT')

        Returns:
            dict: The schema for the specified operation and version.
        """
        if operation == "create_by_asset":
            return self.schema_validator.get_asset_schema(version)

        if operation == "create_by_database":
            return self.schema_validator.get_database_schema()

        if operation == "create_by_workgroup":
            return self.schema_validator.get_workgroup_schema(version)

        if operation == "update":
            return self.schema_validator.get_update_schema(version)

        raise ValueError(f"Unsupported operation: {operation}")

    def validate(
        self,
        data: dict,
        operation: str,
        version: str = Version.DEFAULT.value,
        allow_unknown: bool = True,
        update: bool = False,
    ) -> dict:
        schema = self.get_schema(operation, version)
        data = super().validate(data, schema, allow_unknown, update)
        return data
