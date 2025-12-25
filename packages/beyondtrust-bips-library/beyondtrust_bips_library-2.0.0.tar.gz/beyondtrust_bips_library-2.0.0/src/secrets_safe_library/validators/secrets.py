import copy

from secrets_safe_library.constants.versions import Version
from secrets_safe_library.validators.base import BaseValidator


class _SecretSchemaValidator:
    def __init__(self):
        self.common_schema = {
            "title": {
                "type": "string",
                "maxlength": 256,
                "minlength": 1,
                "required": True,
            },
            "description": {"type": "string", "maxlength": 256, "nullable": True},
            "notes": {"type": "string", "maxlength": 4000, "nullable": True},
            "folder_id": {"type": "string", "is_uuid": True, "nullable": True},
            "urls": {
                "type": "list",
                "schema": {
                    "type": "dict",
                    "schema": {
                        "id": {"type": "string"},
                        "credential_id": {"type": "string"},
                        "url": {"type": "string"},
                    },
                },
                "nullable": True,
            },
        }

        self.owners_v30 = {
            "type": "list",
            "schema": {
                "type": "dict",
                "schema": {
                    "owner_id": {"type": "integer", "required": True},
                    "owner": {"type": "string", "required": False, "nullable": True},
                    "email": {"type": "string", "required": False, "nullable": True},
                },
            },
            "required": True,
        }

        self.owners_v31 = {
            "type": "list",
            "schema": {
                "type": "dict",
                "schema": {
                    "group_id": {
                        "type": "integer",
                        "required": False,
                        "nullable": True,
                    },
                    "user_id": {"type": "integer", "required": True},
                    "name": {"type": "string", "required": False, "nullable": True},
                    "email": {"type": "string", "required": False, "nullable": True},
                },
            },
            "required": True,
        }

    def get_create_secret_schema(self, version: str, operation: str) -> dict:
        """
        Retrieve the schema for the specified operation and version.

        Args:
            operation (str): The operation type (e.g., 'create_credential_secret',
                'create_text_secret', 'create_file_secret').
            version (str): The version (e.g., '3.0', '3.1', '3.2', '3.3', 'DEFAULT')

        Returns:
            dict: The schema for the specified operation and version.
        """

        if operation == "create_credential_secret":
            # Create a deep copy of common schema to avoid modifying the original
            create_schema = copy.deepcopy(self.common_schema)
            create_schema.update(
                {
                    "username": {
                        "type": "string",
                        "maxlength": 1000,
                        "minlength": 1,
                        "required": True,
                    },
                    "password": {
                        "type": "string",
                        "maxlength": 256,
                        "minlength": 1,
                        "required": True,
                    },
                    "password_rule_id": {"type": "integer"},
                }
            )

            if version == Version.V3_0.value:
                return {
                    **create_schema,
                    "owner_id": {
                        "type": "integer",
                        "nullable": True,
                        "is_required_if": {
                            "field": "owner_type",
                            "value": "Group",
                        },
                    },
                    "owner_type": {"type": "string", "allowed": ["User", "Group"]},
                    "owners": self.owners_v30,
                }

            elif version == Version.V3_1.value:
                return {**create_schema, "owners": self.owners_v31}

        elif operation == "create_text_secret":
            # Create a copy of common schema to avoid modifying the original
            create_schema = self.common_schema.copy()
            create_schema.update(
                {
                    "text": {
                        "type": "string",
                        "maxlength": 4096,
                        "minlength": 1,
                        "required": True,
                    },
                }
            )

            if version == Version.V3_0.value:
                return {
                    **create_schema,
                    "owner_id": {
                        "type": "integer",
                        "nullable": True,
                        "is_required_if": {
                            "field": "owner_type",
                            "value": "Group",
                        },
                    },
                    "owner_type": {"type": "string", "allowed": ["User", "Group"]},
                    "owners": self.owners_v30,
                }

            elif version == Version.V3_1.value:
                return {**create_schema, "owners": self.owners_v31}

        elif operation == "create_file_secret":
            # Create a copy of common schema to avoid modifying the original
            create_schema = self.common_schema.copy()
            create_schema.update(
                {
                    "file_path": {
                        "type": "string",
                        "maxlength": 256,
                        "minlength": 1,
                        "required": True,
                    }
                }
            )

            if version == Version.V3_0.value:
                return {
                    **create_schema,
                    "owner_id": {
                        "type": "integer",
                        "nullable": True,
                        "is_required_if": {
                            "field": "owner_type",
                            "value": "Group",
                        },
                    },
                    "owner_type": {"type": "string", "allowed": ["User", "Group"]},
                    "owners": self.owners_v30,
                }

            elif version == Version.V3_1.value:
                return {**create_schema, "owners": self.owners_v31}

        else:
            raise ValueError(f"Unsupported operation: {operation}")

    def get_update_secret_schema(self, version: str, operation: str) -> dict:
        """
        Retrieve the schema for the specified update operation and version.

        Args:
            operation (str): The operation type (e.g., 'update_credential_secret',
                'update_text_secret', 'update_file_secret').
            version (str): The version (e.g., '3.0', '3.1', '3.2', '3.3', 'DEFAULT')

        Returns:
            dict: The schema for the specified update operation and version.
        """

        if operation == "update_credential_secret":
            # Create a copy of common schema to avoid modifying the original
            update_schema = self.common_schema.copy()
            update_schema.update(
                {
                    "username": {
                        "type": "string",
                        "maxlength": 1000,
                        "minlength": 1,
                        "required": True,
                    },
                    "password": {
                        "type": "string",
                        "maxlength": 256,
                        "minlength": 1,
                        "required": True,
                    },
                    "password_rule_id": {"type": "integer", "nullable": True},
                }
            )

            if version == Version.V3_0.value:
                return {
                    **update_schema,
                    "owner_id": {"type": "integer", "nullable": True},
                    "owner_type": {
                        "type": "string",
                        "allowed": ["User", "Group"],
                        "nullable": True,
                    },
                    "owners": self.owners_v30,
                }

            elif version == Version.V3_1.value:
                return {**update_schema, "owners": self.owners_v31}

        elif operation == "update_text_secret":
            # Create a copy of common schema to avoid modifying the original
            update_schema = self.common_schema.copy()

            if version == Version.V3_0.value:
                return {
                    **update_schema,
                    "owner_id": {"type": "integer", "nullable": True},
                    "owner_type": {
                        "type": "string",
                        "allowed": ["User", "Group"],
                        "nullable": True,
                    },
                    "owners": self.owners_v30,
                }

            elif version == Version.V3_1.value:
                return {**update_schema, "owners": self.owners_v31}

        elif operation == "update_file_secret":
            # Create a copy of common schema to avoid modifying the original
            update_schema = self.common_schema.copy()

            if version == Version.V3_0.value:
                return {
                    **update_schema,
                    "owner_id": {"type": "integer", "nullable": True},
                    "owner_type": {
                        "type": "string",
                        "allowed": ["User", "Group"],
                        "nullable": True,
                    },
                    "owners": self.owners_v30,
                }

            elif version == Version.V3_1.value:
                return {**update_schema, "owners": self.owners_v31}

        else:
            raise ValueError(f"Unsupported update operation: {operation}")

    def get_secret_by_path_schema(self) -> dict:
        """
        Retrieve the schema for get_secret_by_path operation.

        Returns:
            dict: The schema for get_secret_by_path operation.
        """
        # The maximum path length (1798) is derived from the BeyondInsight API formula:
        # MaxFolderPathNameLength = ((MaxFolderDepth + 1) * MaxFolderNameLength) +
        # MaxFolderDepth
        # where MaxFolderDepth = 6 and MaxFolderNameLength = 256
        return {
            "path": {"type": "string", "maxlength": 1798, "required": True},
            "title": {"type": "string", "maxlength": 256, "nullable": True},
            "path_depth": {"type": "integer", "max": 7, "required": True},
        }


class SecretsValidator(BaseValidator):
    """Validator for secrets operations."""

    def __init__(self):
        self.schema_validator = _SecretSchemaValidator()

    def get_schema(self, operation: str, version: str = Version.DEFAULT.value) -> dict:
        """
        Retrieve the schema for the specified operation and version.

        Args:
            operation (str): The operation type (e.g., 'create_credential_secret',
                'create_text_secret', 'create_file_secret', 'update_credential_secret',
                'update_text_secret', 'update_file_secret', 'get_secret_by_path').
            version (str): The version (e.g., '3.0', '3.1', '3.2', '3.3', 'DEFAULT')

        Returns:
            dict: The schema for the specified operation and version.
        """

        if operation.startswith("create_"):
            return self.schema_validator.get_create_secret_schema(version, operation)
        elif operation.startswith("update_"):
            return self.schema_validator.get_update_secret_schema(version, operation)
        elif operation == "get_secret_by_path":
            return self.schema_validator.get_secret_by_path_schema()
        else:
            raise ValueError(f"Unsupported operation type: {operation}")

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
