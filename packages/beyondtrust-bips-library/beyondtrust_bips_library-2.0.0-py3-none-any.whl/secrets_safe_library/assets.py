"""Assets module, all the logic to manage assets from PS API"""

import logging
from typing import List

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject
from secrets_safe_library.validators.base import CustomValidator


class Asset(APIObject):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger)

        # Schema rules used for validations
        self._schema = {
            "workgroup_id": {"type": "integer", "nullable": True},
            "workgroup_name": {"type": "string", "nullable": True},
            "ip_address": {
                "type": "string",
                "is_ip": True,
                "maxlength": 45,
                "nullable": False,
                "required": True,
            },
            "asset_name": {
                "type": "string",
                "maxlength": 128,
                "nullable": True,
                "required": False,
            },
            "dns_name": {
                "type": "string",
                "maxlength": 255,
                "nullable": True,
                "required": False,
            },
            "domain_name": {
                "type": "string",
                "maxlength": 64,
                "nullable": True,
                "required": False,
            },
            "mac_address": {
                "type": "string",
                "maxlength": 128,
                "nullable": True,
                "required": False,
            },
            "asset_type": {
                "type": "string",
                "maxlength": 64,
                "nullable": True,
                "required": False,
            },
            "description": {
                "type": "string",
                "maxlength": 255,
                "nullable": True,
                "required": False,
            },
            "operating_system": {
                "type": "string",
                "maxlength": 255,
                "nullable": True,
                "required": False,
            },
        }
        self._validator = CustomValidator(self._schema)

    def list_assets(
        self,
        workgroup_id: int = None,
        workgroup_name: str = None,
        limit: int = None,
        offset: int = None,
    ) -> list:
        """
        Returns a list of assets matching specified Workgroup ID or Name.
        parameters.

        API:
            - GET Workgroups/{workgroupID}/Assets
            - GET Workgroups/{workgroupName}/Assets

        Args:
            workgroup_id (int, optional): The Workgroup ID, if want to search by
                Workgroup ID.
            workgroup_name (str, optional): The Workgroup name, if want to search by
                Workgroup name.
            limit (int, optional): limit the results.
            offset (int, optional): skip the first (offset) number of assets.

        Returns:
            list: List of assets matching specified Workgroup ID or Name.
        """

        params = {
            "limit": limit,
            "offset": offset,
        }
        query_string = self.make_query_string(params)

        if workgroup_id:
            endpoint = f"/workgroups/{workgroup_id}/assets?{query_string}"
        elif workgroup_name:
            endpoint = f"/workgroups/{workgroup_name}/assets?{query_string}"
        else:
            raise exceptions.OptionsError(
                "Either workgroup_id or workgroup_name is required"
            )

        utils.print_log(self._logger, "Calling list_assets endpoint", logging.DEBUG)
        response = self._run_get_request(endpoint)

        return response.json()

    def get_asset_by_id(self, asset_id: str) -> dict:
        """
        Returns an asset by ID.

        API: GET Assets/{id}

        Args:
            asset_id (str): The asset ID (GUID).

        Returns:
            dict: Asset object.
        """

        endpoint = f"/assets/{asset_id}"

        utils.print_log(
            self._logger,
            "Calling get_asset_by_id endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def get_asset_by_workgroup_name(self, workgroup_name: str, asset_name: str) -> dict:
        """
        Returns an asset by Workgroup name and asset name.

        API: GET Workgroups/{workgroupName}/Assets?name={name}

        Args:
            workgroup_name (str): Name of the Workgroup.
            asset_name (str): Name of the asset.

        Returns:
            dict: Asset object.
        """

        params = {"name": asset_name}
        query_string = self.make_query_string(params)

        endpoint = f"/workgroups/{workgroup_name}/assets?{query_string}"

        utils.print_log(
            self._logger,
            "Calling get_asset_by_workgroup_name endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def list_asset_attributes(self, asset_id: int) -> List[dict]:
        """
        Returns a list of attributes for a specific asset.

        API: GET Assets/{assetID}/Attributes

        Args:
            asset_id (int): The asset ID.

        Returns:
            List[dict]: List of attributes for the specified asset.
        """

        endpoint = f"/assets/{asset_id}/attributes"

        utils.print_log(
            self._logger,
            "Calling list_asset_attributes endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def search_assets(
        self,
        asset_name: str = None,
        dns_name: str = None,
        domain_name: str = None,
        ip_address: str = None,
        mac_address: str = None,
        asset_type: str = None,
        limit: int = 100000,
        offset: int = 0,
    ) -> list:
        """
        Returns a list of assets that match the given search criteria.

        At least one request body property should be provided; any property not
        provided is ignored. All search criteria is case insensitive and is an exact
        match (equality), except for IPAddress.

        API: POST Assets/Search

        Args:
            asset_name (str, optional): The Asset name, if you want to search by
                Asset name.
            dns_name (str, optional): The DNS name, if you want to search by DNS name.
            domain_name (str, optional): The Domain name, if you want to search by
                Domain name.
            ip_address (str, optional): The IP address, if you want to search by IP
                address.
            mac_address (str, optional): The MAC address, if you want to search by MAC
                address.
            asset_type (str, optional): The Asset type, if you want to search by Asset
                type.
            limit (int, optional): Limit the number of results returned.
            offset (int, optional): Skip the first (offset) number of assets in the
                results.

        Returns:
            list: List of assets matching specified parameters.
        """

        if not any(
            [asset_name, dns_name, domain_name, ip_address, mac_address, asset_type]
        ):
            raise exceptions.OptionsError(
                "At least one of the following fields must be provided: "
                "asset_name, dns_name, domain_name, ip_address, mac_address, asset_type"
            )

        params = {
            "limit": limit,
            "offset": offset,
        }
        query_string = self.make_query_string(params)

        endpoint = f"/assets/search?{query_string}"

        utils.print_log(self._logger, "Calling list_assets endpoint", logging.DEBUG)

        body = {
            "AssetName": asset_name,
            "DnsName": dns_name,
            "DomainName": domain_name,
            "IPAddress": ip_address,
            "MacAddress": mac_address,
            "AssetType": asset_type,
        }

        req_body = {key: value for key, value in body.items() if value is not None}
        response = self._run_post_request(endpoint, req_body, expected_status_code=200)

        return response.json()

    def create_asset(
        self,
        *,
        workgroup_id: int = None,
        workgroup_name: str = None,
        ip_address: str = None,
        asset_name: str = None,
        dns_name: str = None,
        domain_name: str = None,
        mac_address: str = None,
        asset_type: str = None,
        description: str = None,
        operating_system: str = None,
    ) -> dict:
        """
        Creates a new asset in the Workgroup, referenced by ID (workgroup_id) or
        Workgroup Name.

        If both workgroup_id and workgroup_name are provided, the workgroup_id is used.

        API:
            - POST Workgroups/{workgroupID}/Assets
            - POST Workgroups/{workgroupName}/Assets

        Args:
            workgroup_id (int): Workgroup ID.
            ip_address (str): Asset IP address. Required. Max string length is 45.
            asset_name (str, optional): Asset name. If not provided, a padded IP address
                is used. Max string length is 128.
            dns_name (str, optional): Asset DNS name. Max string length is 255.
            domain_name (str, optional): Asset domain name. Max string length is 64.
            mac_address (str, optional): Asset MAC address. Max string length is 128.
            asset_type (str, optional): Asset type. Max string length is 64.
            description (str, optional): Asset description. Only updated if the version
                in the URL is 3.1 or greater. Max string length is 255.
            operating_system (str, optional): Asset operating system. Max string length
                is 255.

        Returns:
            dict: Asset object.
        """

        attributes = {
            "workgroup_id": workgroup_id,
            "ip_address": ip_address,
            "asset_name": asset_name,
            "dns_name": dns_name,
            "domain_name": domain_name,
            "mac_address": mac_address,
            "asset_type": asset_type,
            "description": description,
            "operating_system": operating_system,
        }

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        if workgroup_id is None and workgroup_name is None:
            raise exceptions.OptionsError(
                "Either workgroup_id or workgroup_name is required"
            )

        identifier = workgroup_id if workgroup_id is not None else workgroup_name
        endpoint = f"/workgroups/{identifier}/assets"

        utils.print_log(self._logger, "Calling create_asset endpoint", logging.DEBUG)

        body = {
            "IPAddress": ip_address,
            "AssetName": asset_name,
            "DnsName": dns_name,
            "DomainName": domain_name,
            "MacAddress": mac_address,
            "AssetType": asset_type,
            "Description": description,
            "OperatingSystem": operating_system,
        }

        req_body = {key: value for key, value in body.items() if value is not None}
        response = self._run_post_request(endpoint, req_body, expected_status_code=201)

        return response.json()

    def update_asset(
        self,
        asset_id: int,
        *,
        workgroup_id: int = None,
        asset_name: str = None,
        dns_name: str = None,
        domain_name: str = None,
        ip_address: str = None,
        mac_address: str = None,
        asset_type: str = None,
        description: str = None,
        operating_system: str = None,
    ) -> dict:
        """
        Updates an existing asset by ID.

        If both workgroup_id and workgroup_name are provided, the workgroup_id is used.

        API:
            - PUT Assets/{id}

        Args:
            asset_id (int): ID of the asset.
            workgroup_id (int): Workgroup ID.
            ip_address (str): Asset IP address. Required. Max string length is 45.
            asset_name (str, optional): Asset name. If not provided, a padded IP address
                is used. Max string length is 128.
            dns_name (str, optional): Asset DNS name. Max string length is 255.
            domain_name (str, optional): Asset domain name. Max string length is 64.
            mac_address (str, optional): Asset MAC address. Max string length is 128.
            asset_type (str, optional): Asset type. Max string length is 64.
            description (str, optional): Asset description. Only updated if the version
                in the URL is 3.1 or greater. Max string length is 255.
            operating_system (str, optional): Asset operating system. Max string length
                is 255.

        Returns:
            dict: Asset object.
        """

        attributes = {
            "workgroup_id": workgroup_id,
            "ip_address": ip_address,
            "asset_name": asset_name,
            "dns_name": dns_name,
            "domain_name": domain_name,
            "mac_address": mac_address,
            "asset_type": asset_type,
            "description": description,
            "operating_system": operating_system,
        }

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        if not workgroup_id:
            raise exceptions.OptionsError("workgroup_id is required")

        endpoint = f"/assets/{asset_id}"

        utils.print_log(self._logger, "Calling update_asset endpoint", logging.DEBUG)

        body = {
            "WorkgroupID": workgroup_id,
            "IPAddress": ip_address,
            "AssetName": asset_name,
            "DnsName": dns_name,
            "DomainName": domain_name,
            "MacAddress": mac_address,
            "AssetType": asset_type,
            "Description": description,
            "OperatingSystem": operating_system,
        }

        req_body = {key: value for key, value in body.items() if value is not None}
        response = self._run_put_request(endpoint, req_body, expected_status_code=200)

        return response.json()

    def delete_asset_by_id(self, asset_id: int) -> None:
        """
        Deletes an asset by ID.

        API: DELETE Assets/{id}

        Args:
            asset_id (int): The asset ID.

        Returns:
            None
        """

        endpoint = f"/assets/{asset_id}"

        utils.print_log(
            self._logger,
            "Calling delete_asset_by_id endpoint",
            logging.DEBUG,
        )
        self._run_delete_request(endpoint, expected_status_code=200)

    def assign_asset_attribute(self, asset_id: int, attribute_id: int) -> dict:
        """
        Assigns an attribute to an asset.

        API: POST Assets/{assetID}/Attributes/{attributeID}

        Args:
            asset_id (int): The asset ID.
            attribute_id (int): The attribute ID.

        Returns:
            dict: Asset object.
        """

        endpoint = f"/assets/{asset_id}/attributes/{attribute_id}"

        utils.print_log(
            self._logger,
            "Calling assign_asset_attribute endpoint",
            logging.DEBUG,
        )

        response = self._run_post_request(
            endpoint, payload={}, expected_status_code=201
        )

        return response.json()

    def delete_asset_attribute(self, asset_id: int, attribute_id: int) -> None:
        """
        Deletes an attribute from an asset.

        API: DELETE Assets/{assetID}/Attributes/{attributeID}

        Args:
            asset_id (int): The asset ID.
            attribute_id (int): The attribute ID.

        Returns:
            None
        """

        endpoint = f"/assets/{asset_id}/attributes/{attribute_id}"

        utils.print_log(
            self._logger,
            "Calling delete_asset_attribute endpoint",
            logging.DEBUG,
        )
        self._run_delete_request(endpoint, expected_status_code=200)
