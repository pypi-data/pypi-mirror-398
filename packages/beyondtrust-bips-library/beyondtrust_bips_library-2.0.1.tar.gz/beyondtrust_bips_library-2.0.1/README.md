# Password Safe API integration
[![License](https://img.shields.io/badge/license-MIT%20-brightgreen.svg)](LICENSE)

Password Safe API integration written in Python, Abstract complexity of managing secrets with the API

## Python version compatibility
  
This library is compatible with Python >= v3.11.

## Install Package

```sh
# PyPI
pip install beyondtrust-bips-library
```
## Arguments

### Retrieve Secrets
- api_url:
    - description: BeyondTrust Password Safe API URL.
    - type: string
    - required: True
- api_key:
    - description: The API Key configured in BeyondInsight for your application. If not set, then client credentials must be provided.
    - type: string
    - required: False
- client_id:
    - description: API OAuth Client ID.
    - type: string
    - required: True
- client_secret:
    - description: API OAuth Client Secret.
    - type: string
    - required: True
- secret_list:
    - description: List of secrets ["path/title","path/title"] or managed accounts ["ms/ma","ms/ma"] to be retrieved, separated by a comma.
    - type: list
    - required: True
- certificate_path:
    - description: Password Safe API pfx Certificate Path. For use when authenticating using a Client Certificate.
    - type: string
    - required: False
- certificate_password:
    - description: Password Safe API pfx Certificate Password. For use when authenticating using a Client Certificate.
    - type: string
    - required: False
- verify_ca:
    - description: Indicates whether to verify the certificate authority on the Secrets Safe instance.
    - type: boolean 
    - default: True
    - required: False

## Available Methods 

### Access Management

### AccessLevels Class
- **`get_access_levels()`** - List all available access levels
- **`post_access_levels_usergroupid_smartruleid(usergroupid, smartruleid, accesslevelid)`** - Assign access level to user group and smart rule

### AccessPolicy Class  
- **`test_access_policy(system_id, account_id, duration_minutes)`** - Test access policy configuration

### Permission Class
- **`get_usergroup_permissions(usergroup_id)`** - Get permissions for user group
- **`set_usergroup_permissions(usergroup_id, permissions)`** - Set user group permissions
- **`delete_usergroup_permissions(usergroup_id)`** - Remove user group permissions

---

## Asset & System Management

### Asset Class
- **`list_assets(workgroup_id, workgroup_name, limit, ...)`** - List assets with filtering
- **`get_asset_by_id(asset_id)`** - Get specific asset by ID
- **`get_asset_by_workgroup_name(workgroup_name, asset_name)`** - Find asset by workgroup and name
- **`list_asset_attributes(asset_id)`** - List attributes for an asset
- **`search_assets(asset_name, dns_name, domain_name, ...)`** - Search assets by criteria
- **`create_asset()`** - Create new asset
- **`update_asset(asset_id)`** - Update existing asset
- **`delete_asset_by_id(asset_id)`** - Delete asset by ID

### ManagedSystem Class
- **`get_managed_systems(limit, offset, type, name)`** - List managed systems with filtering
- **`get_managed_system_by_id(managed_system_id)`** - Get specific managed system
- **`get_managed_system_by_asset_id(asset_id)`** - Get managed system by asset ID
- **`get_managed_system_by_database_id(database_id)`** - Get managed system by database ID
- **`post_managed_system_by_asset_id(**kwargs)`** - Create managed system for asset
- **`post_managed_system_by_database_id(**kwargs)`** - Create managed system for database
- **`post_managed_system_by_workgroup_id(**kwargs)`** - Create managed system for workgroup
- **`put_managed_system_by_id(managed_system_id, **kwargs)`** - Update managed system
- **`delete_managed_system_by_id(managed_system_id)`** - Delete managed system

### Database Class
- **`get_databases()`** - List all databases
- **`get_database_by_id(database_id)`** - Get specific database
- **`get_databases_by_asset_id(asset_id)`** - Get databases for an asset
- **`post_database_by_asset_id(asset_id, platform_id, port, ...)`** - Create database for asset
- **`put_database_by_id(database_id, **kwargs)`** - Update database
- **`delete_database_by_id(database_id)`** - Delete database

---

## Secret Management

### SecretsSafe Class
- **`get_secret(path)`** - Get single secret by path
- **`get_secret_with_metadata(path)`** - Get secret with metadata by path
- **`get_secrets(paths)`** - Get multiple secrets by paths
- **`get_secrets_with_metadata(paths)`** - Get multiple secrets with metadata
- **`get_all_secrets_by_folder_path(folder_path)`** - Get all secrets in a folder
- **`get_file_secret_data(secret_id)`** - Download file secret content
- **`list_secrets(**filters)`** - List secrets with optional filtering
- **`list_secrets_by_folder_id(folder_id)`** - List secrets in specific folder
- **`create_secret(title, folder_id, **kwargs)`** - Create new secret (normal/text/file)
- **`update_secret(secret_id, **kwargs)`** - Update existing secret
- **`delete_secret_by_id(secret_id)`** - Delete secret by ID
- **`get_secret_by_id(secret_id)`** - Get secret details by ID

### Safe Class
- **`create_safe(name, description)`** - Create new safe container
- **`update_safe(safe_id, name, description)`** - Update safe information
- **`get_by_id(safe_id)`** - Get safe by ID (inherited)
- **`delete_by_id(safe_id)`** - Delete safe by ID (inherited)
- **`list()`** - List all safes (inherited)

### Folder Class
- **`list_folders(folder_name, folder_path, include_subfolders, ...)`** - List folders with filtering
- **`create_folder(name, parent_id, description, ...)`** - Create new folder

---

## Managed Account Operations

### ManagedAccount Class  
- **`get_secret(path)`** - Get managed account credential by path
- **`get_secret_with_metadata(path)`** - Get credential with metadata
- **`get_secrets(paths)`** - Get multiple credentials by paths
- **`get_secrets_with_metadata(paths)`** - Get multiple credentials with metadata
- **`create_request(system_id, account_id)`** - Request access to managed account
- **`get_credential_by_request_id(request_id)`** - Get account credentials
- **`request_check_in(request_id, reason)`** - Release managed account
- **`get_managed_accounts(**kwargs)`** - Search and filter managed accounts
- **`list_by_managed_system(managed_system_id)`** - List accounts by system
- **`list_by_smart_rule_id(smart_rule_id)`** - List accounts by smart rule
- **`list_by_quick_rule_id(quick_rule_id)`** - List accounts by quick rule
- **`create_managed_account(**kwargs)`** - Create new managed account
- **`assign_attribute(managed_account_id, attribute_id)`** - Assign attribute to account
- **`delete_attribute(managed_account_id, attribute_id)`** - Remove attribute from account
- **`delete_all_attributes(managed_account_id)`** - Remove all attributes from account

### Credentials Class
- **`get_credentials_by_request_id(request_id, type)`** - Get credentials for a request
- **`get_credentials_by_alias_id(alias_id, request_id, type)`** - Get credentials by alias

---

## User & Group Management

### User Class
- **`get_users(username, include_inactive)`** - List/search users
- **`get_user_by_id(user_id)`** - Get specific user details
- **`get_users_by_usergroup_id(usergroup_id)`** - Get users in group
- **`post_user_beyondinsight(user_name, first_name, email_address, ...)`** - Create BeyondInsight user
- **`post_user_active_directory(user_name, forest_name, domain_name, ...)`** - Create AD user integration
- **`post_user_ldap(host_name, distinguished_name, ...)`** - Create LDAP user
- **`post_user_application(user_name, access_policy_id)`** - Create application user
- **`post_user_quarantine(user_id)`** - Quarantine user account
- **`put_user_beyondinsight(user_id, **kwargs)`** - Update BeyondInsight user
- **`put_user_application(user_id, **kwargs)`** - Update application user
- **`delete_user(user_id)`** - Delete user account

### Usergroups Class
- **`get_usergroups()`** - List all user groups
- **`get_usergroup_by_id(usergroup_id)`** - Get specific user group
- **`get_usergroups_by_name(name)`** - Find user groups by name
- **`post_usergroups_beyondinsight(group_name, description, is_active, ...)`** - Create BeyondInsight group
- **`post_usergroups_entraid(description, group_name, client_id, ...)`** - Create Entra ID group
- **`post_usergroups_ad(group_name, domain_name, description, ...)`** - Create AD group
- **`post_usergroups_ldap(group_name, group_distinguished_name, ...)`** - Create LDAP group
- **`delete_usergroup_by_name(name)`** - Delete user group

### UserGroupRoles Class
- **`get_roles(user_group_id, smart_rule_id)`** - Get roles for user group and smart rule
- **`set_roles(user_group_id, smart_rule_id, roles, ...)`** - Set user group roles
- **`delete_roles(user_group_id, smart_rule_id)`** - Remove user group roles

---

## Session Management

### Session Class
- **`get_sessions(status, user_id)`** - List active sessions
- **`post_sessions_request_id(request_id, session_type, node_id)`** - Create session from request
- **`post_sessions_admin(session_type, host_name, user_name, ...)`** - Create admin session

### SessionLocking Class
- **`post_session_lock_sessionid(session_id)`** - Lock specific session
- **`post_session_lock_managed_account_id(managed_account_id)`** - Lock sessions for account
- **`post_session_lock_managed_system_id(managed_system_id)`** - Lock sessions for system

### SessionTermination Class
- **`post_session_terminate_sessionid(session_id)`** - Terminate specific session
- **`post_session_terminate_managedaccountid(managed_account_id)`** - Terminate account sessions
- **`post_session_terminate_managedsystemid(managed_system_id)`** - Terminate system sessions

### Keystroke Class
- **`get_keystrokes_by_session_id(session_id)`** - Get keystrokes for session
- **`search_keystrokes(data, type)`** - Search keystroke data

### Replay Class
- **`create_replay_session(session_id, record_key, protocol, ...)`** - Create session replay
- **`get_replay_session(replay_id, jpeg_scale, png_scale, ...)`** - Get replay session data
- **`control_replay_session(replay_id, speed, offset, ...)`** - Control replay playback
- **`get_by_id(replay_id)`** - Get replay by ID (inherited)
- **`delete_by_id(replay_id)`** - Delete replay by ID (inherited)

---

## Request Management

### Request Class
- **`get_requests(status, queue)`** - List requests with filtering
- **`post_request(system_id, account_id, duration_minutes, ...)`** - Create access request
- **`post_request_alias(alias_id, duration_minutes, access_type, ...)`** - Create alias request
- **`put_request_checkin(request_id, reason)`** - Check in active request
- **`put_request_approve(request_id, reason)`** - Approve pending request
- **`put_request_deny(request_id, reason)`** - Deny pending request
- **`put_request_rotate_on_checkin(request_id)`** - Set password rotation on checkin

### RequestSets Class
- **`get_request_sets(status)`** - Get request sets by status
- **`post_request_sets(access_types, system_id, account_id, ...)`** - Create request set

### RequestTermination Class
- **`post_request_termination_managed_account_id(managed_account_id, reason)`** - Terminate account requests
- **`post_request_termination_managed_system_id(managed_system_id, reason)`** - Terminate system requests
- **`post_request_termination_user_id(userid, reason)`** - Terminate user requests

### ISARequest Class
- **`create_isa_request(system_id, account_id, duration_minutes, ...)`** - Create ISA access request

---

## Rule Management

### SmartRule Class
- **`list_assets_by_smart_rule_id(smart_rule_id, limit, offset)`** - List assets in smart rule
- **`create_filter_asset_attribute(attribute_ids, title, category, ...)`** - Create attribute filter rule
- **`list_smart_rules_by_user_group_id(user_group_id)`** - List smart rules for user group
- **`run_smart_rule(smart_rule_id, queue)`** - Execute smart rule

### QuickRule Class
- **`get_by_org_and_title(organization_id, title)`** - Get quick rule by organization and title
- **`delete_by_org_and_title(organization_id, title)`** - Delete quick rule
- **`create_quick_rule(ids, title, category, ...)`** - Create new quick rule
- **`add_accounts_to_quick_rule(quick_rule_id, account_ids)`** - Add accounts to quick rule

---

## System Configuration

### Authentication Class
- **`oauth()`** - Perform OAuth authentication
- **`sign_app_in()`** - Sign into API with credentials
- **`get_api_access()`** - Get API access token
- **`sign_app_out()`** - Sign out of API session
- **`send_post_sign_app_in()`** - Send sign-in POST request
- **`validate_input(parameter_name, parameter_value)`** - Validate authentication parameters

### CertUtil Class
- **`get_certificate()`** - Get certificate data
- **`get_certificate_key()`** - Get certificate private key
- **`set_certificate_data_from_pfx_file(certificate_path, certificate_password)`** - Load certificate from PFX file
- **`get_certificate_and_certificate_key(certificate_path, certificate_password)`** - Get both certificate and key

### Platform Class
- **`list_by_entity_type(entity_type_id)`** - List platforms by entity type
- **`list()`** - List all platforms (inherited)
- **`get_by_id(platform_id)`** - Get platform by ID (inherited)

---

## Attribute Management

### AttributeType Class
- **`create_attribute_type(name)`** - Create new attribute type

### Attributes Class
- **`get_attributes_by_attribute_type_id(attribute_type_id)`** - Get attributes by type
- **`post_attribute_by_attribute_type_id(attribute_type_id, short_name, long_name, ...)`** - Create attribute
- **`get_attributes_by_managed_account_id(managed_account_id)`** - Get account attributes
- **`get_attributes_by_managed_system_id(managed_system_id)`** - Get system attributes
- **`post_attribute_by_managed_account_id(managed_account_id, attribute_id)`** - Assign attribute to account
- **`post_attribute_by_managed_system_id(managed_system_id, attribute_id)`** - Assign attribute to system
- **`delete_attributes_by_managed_account_id(managed_account_id)`** - Remove all account attributes
- **`delete_attributes_by_managed_system_id(managed_system_id)`** - Remove all system attributes

---

## Network & Infrastructure

### AddressGroup Class
- **`get_address_group_by_id(address_group_id)`** - Get address group by ID
- **`get_address_group_by_name(address_group_name)`** - Get address group by name
- **`create_address_group(name)`** - Create new address group
- **`update_address_group(address_group_id, name)`** - Update address group

### Aliases Class
- **`get_aliases(state)`** - Get aliases by state (active/inactive)

---

## Application Management

### Application Class
- **`get_managed_account_apps(account_id)`** - Get applications for managed account
- **`assign_app_to_managed_account(account_id, application_id)`** - Assign application to account
- **`remove_app_from_managed_account(account_id, application_id)`** - Remove application from account
- **`unassign_all_apps_from_managed_account(account_id)`** - Remove all applications from account

### APIRegistration Class
- **`get_key_by_id(api_registration_id)`** - Get API key by registration ID
- **`rotate_api_key(api_registration_id)`** - Rotate API key
- **`create_api_registration(name, registration_type, access_token_duration, ...)`** - Create API registration
- **`update_api_registration(registration_id, name, registration_type, ...)`** - Update API registration

---

## Policy Management

### EPMPolicies Class
- **`add_epm_application()`** - Add EPM application policy

### PropagationActions Class
- **`get_managed_account_propagation_actions(managed_account_id)`** - Get propagation actions for account
- **`post_managed_account_propagation_action_by_id(managed_account_id, propagation_action_id, smart_rule_id)`** - Add propagation action
- **`delete_managed_account_propagation_action(managed_account_id)`** - Remove all propagation actions
- **`delete_managed_account_propagation_action_by_id(managed_account_id, propagation_action_id)`** - Remove specific action

---

## Organization Management

### Organization Class
- **`get_organization_by_id(organization_id)`** - Get organization by ID
- **`list_organizations()`** - List all organizations
- **`get_organization_by_name(organization_name)`** - Find organization by name

### Workgroup Class
- **`get_workgroup_by_id(workgroup_id)`** - Get workgroup by ID
- **`get_workgroup_by_name(workgroup_name)`** - Get workgroup by name
- **`get_workgroups()`** - List all workgroups
- **`post_workgroup(name, organization_id)`** - Create new workgroup

---

## Additional Services

### FunctionalAccount Class
- **`create_functional_account()`** - Create functional account for automation

### Entitlement Class
- **`list_entitlements(group_ids)`** - List entitlements for groups

### SubscriptionDelivery Class
- **`download(request_id)`** - Download subscription delivery content

---

## Example of usage

We strongly recommend you to use a virtual environment and install dependences from requirements.txt file.

Import `secrets_safe_library`

```sh
pip install -r ~/requirements.txt
```

By default urllib3 logs are not shown, If need to show them:

```sh
export URLLIB3_PROPAGATE=True
```

script example using library:
```python
import  os
import  logging
from  secrets_safe_library  import  secrets_safe, authentication, utils, managed_account
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

env  =  os.environ
LOGGER_NAME  =  "custom_logger"

logging.basicConfig(format  =  '%(asctime)-5s  %(name)-15s  %(levelname)-8s  %(message)s',

level  =  logging.DEBUG)

# logger object is optional but is strongly recommended
logger  =  logging.getLogger(LOGGER_NAME)

TIMEOUT_CONNECTION_SECONDS = 30
TIMEOUT_REQUEST_SECONDS = 30

CERTIFICATE = env['CERTIFICATE']
CERTIFICATE_KEY = env['CERTIFICATE_KEY']

def  main():
    try:
        with requests.Session() as session:
            retry_strategy = Retry(
                total=3,
                backoff_factor=0.2,
                status_forcelist=[400, 408, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            
            certificate, certificate_key = utils.prepare_certificate_info(CERTIFICATE, CERTIFICATE_KEY)
            
            authentication_obj = authentication.Authentication(
                req=session,
                timeout_connection=TIMEOUT_CONNECTION_SECONDS,
                timeout_request=TIMEOUT_REQUEST_SECONDS,
                api_url="https://example.com:443/BeyondTrust/api/public/v3",
                client_id="<client_id>",
                client_secret="<client_secret>",
                certificate=certificate,
                certificate_key=certificate_key,
                verify_ca=True,
                logger=None
            )

            # sign app in password safe API
            get_api_access_response  =  authentication_obj.get_api_access()

            if  get_api_access_response.status_code ==  200:
                # instantiate secrets safe object
                secrets_safe_obj  =  secrets_safe.SecretsSafe(authentication_obj, logger)

                get_secrets_response  =  secrets_safe_obj.get_secrets(["oagrp/text,oagrp/credential"])
                utils.print_log(logger, f"=> Retrive secrets: {get_secrets_response}", logging.DEBUG)
            else:
                print(f"Please check credentials, error {get_api_access_response.text}")
            
            authentication_obj.sign_app_out()

    except  Exception  as  e:
        utils.print_log(logger, f"Error: {e}", logging.ERROR)

# calling main method
main()
```
