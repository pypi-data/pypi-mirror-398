# flake8: noqa: S105
"""
Endpoints list used in Integration Library (verb:endpoint)
"""

# Secrets
GET_SECRETS_SAFE_SECRETS = "get:secrets-safe/secrets"
GET_SECRETS_SAFE_SECRETS_SECRETID = "get:secrets-safe/secrets/{secretid}"
GET_SECRETS_SAFE_SECRETS_SECRETID_TEXT = "get:secrets-safe/secrets/{secretid}/text"
GET_SECRETS_SAFE_SECRETS_SECRETID_FILE = "get:secrets-safe/secrets/{secretid}/file"
GET_SECRETS_SAFE_FOLDERS_FOLDERID_SECRETS = (
    "get:secrets-safe/folders/{folderid}/secrets"
)
GET_SECRETS_SAFE_FOLDERS_FOLDERID_TEXT = "get:secrets-safe/folders/{folderid}/text"
GET_SECRETS_SAFE_FOLDERS_FOLDERID_FILE = "get:secrets-safe/folders/{folderid}/file"
POST_SECRETS_SAFE_FOLDERS_FOLDERID = "post:secrets-safe/folders/{folderid}/secrets"
POST_SECRETS_SAFE_FOLDERS_FOLDERID_TEXT = (
    "post:secrets-safe/folders/{folderid}/secrets/text"
)
POST_SECRETS_SAFE_FOLDERS_FOLDERID_FILE = (
    "post:secrets-safe/folders/{folderid}/secrets/file"
)
PUT_SECRETS_SAFE_SECRETS_SECRETID = "put:secrets-safe/secrets/{secretid}"
PUT_SECRETS_SAFE_SECRETS_SECRETID_TEXT = "put:secrets-safe/secrets/{secretid}/text"
PUT_SECRETS_SAFE_SECRETS_SECRETID_FILE = "put:secrets-safe/secrets/{secretid}/file"

# Folders
GET_SECRETS_SAFE_FOLDERS = "get:secrets-safe/folders"
GET_SECRETS_SAFE_FOLDERS_FOLDERID = "get:secrets-safe/folders/{folderid}"

# Managed Systems
GET_MANAGED_SYSTEMS = "get:managedsystems"
GET_MANAGED_SYSTEMS_MANAGEDSYSTEMID = "get:managedsystems/{managedsystemid}"
GET_MANAGED_SYSTEMS_ASSETID = "get:assets/{assetid}/managedsystems"
GET_MANAGED_SYSTEMS_DATABASEID = "get:databases/{databaseid}/managedsystems"
GET_MANAGED_SYSTEMS_FUNCTIONALACCOUNTID = (
    "get:functionalaccounts/{functionalaccountid}/managedsystems"
)
GET_MANAGED_SYSTEMS_WORKGROUPID = "get:workgroups/{workgroupid}/managedsystems"
POST_MANAGED_SYSTEMS_ASSETID = "post:assets/{assetid}/managedsystems"
POST_MANAGED_SYSTEMS_DATABASEID = "post:databases/{databaseid}/managedsystems"
POST_MANAGED_SYSTEMS_WORKGROUPID = "post:workgroups/{workgroupid}/managedsystems"
DELETE_MANAGED_SYSTEMS_MANAGEDSYSTEMID = "delete:managedsystems/{managedsystemid}"
PUT_MANAGED_SYSTEMS_MANAGEDSYSTEMID = "put:managedsystems/{managedsystemid}"

# Safes
GET_SECRETS_SAFE_SAFES = "get:secrets-safe/safes"
GET_SECRETS_SAFE_SAFES_ID = "get:secrets-safe/safes/{ID}"

# Assets
GET_WORKGROUPS_ID_ASSETS = "get:workgroups/{workgroupid}/assets"
GET_ASSETS_ID_ATTRIBUTES = "get:assets/{assetid}/attributes"
GET_ASSETS_ID = "get:assets/{id}"
GET_WORKGROUPS_NAME_ASSETS_NAME = "get:workgroups/{workgroupname}/assets?name"
POST_WORKGROUPS_WORKGROUPID_ASSETS = "post:workgroups/{workgroupid}/assets"

# Smart Rules
GET_SMART_RULES = "get:smartrules"
GET_SMART_RULES_ID = "get:smartrules/{id}"
POST_SMART_RULES_FILTER_ASSET_ATTRIBUTE = "post:smartrules/filterassetattribute"
POST_SMART_RULES_ID_PROCESS = "post:smartrules/{id}/process"

# Organizations
GET_ORGANIZATIONS = "get:organizations"
GET_ORGANIZATIONS_ID = "get:organizations/{id}"
GET_ORGANIZATIONS_NAME = "get:organizations/{name}"

# Workgroups
GET_WORKGROUPS_ID = "get:workgroups/{id}"
GET_WORKGROUPS_NAME = "get:workgroups?name={name}"
GET_WORKGROUPS = "get:workgroups"
POST_WORKGROUPS = "post:workgroups"

# Databases
GET_DATABASES = "get:databases"
GET_DATABASES_ID = "get:databases/{id}"
GET_DATABASES_ASSET_ID = "get:assets/{assetid}/databases"
POST_DATABASES_ASSET_ID = "post:assets/{assetid}/databases"
PUT_DATABASES_ID = "put:databases/{id}"
DELETE_DATABASES_ID = "delete:databases/{id}"

# Address Groups
GET_ADDRESS_GROUPS = "get:addressgroups"
GET_ADDRESS_GROUPS_ID = "get:addressgroups/{id}"
GET_ADDRESS_GROUPS_NAME = "get:addressgroups/{name}"

# Users
GET_USERS = "get:users"
GET_USERS_ID = "get:users/{id}"
GET_USERS_USERGROUPID = "get:usergroups/{usergroupid}/users"
POST_USERS_USERGROUPID = "post:usergroups/{usergroupid}/users"
POST_USERS_BI = "post:users:bi"
POST_USERS_AD = "post:users:ad"
POST_USERS_LDAP = "post:users:ldap"
POST_USERS_APP = "post:users:app"
POST_USERS_QUARANTINE = "post:users/{id}/quarantine"
POST_USERS_RECYCLE_CLIENT_SECRET = "post:users/{id}/recycleclientsecret"  # nosec
PUT_USERS_ID_BI = "put:users/{id}:bi"
PUT_USERS_ID_APP = "put:users/{id}:app"

# Managed Accounts
GET_MANAGED_SYSTEMS_SYSTEM_ID_MANAGED_ACCOUNTS = (
    "get:managedsystems/{systemid}/managedaccounts"
)
GET_MANAGED_ACCOUNTS_ID = "get:managedaccounts/{id}"
POST_MANAGED_SYSTEMS_SYSTEM_ID_MANAGED_ACCOUNTS = (
    "post:managedsystems/{systemid}/managedaccounts"
)
GET_MANAGED_ACCOUNTS_ID_ATTRIBUTES = "get:managedaccounts/{managedaccountid}/attributes"
PUT_MANAGED_ACCOUNTS_CREDENTIALS = "put:managedaccounts/{managedaccountid}/credentials"

# Functional Accounts
GET_FUNCTIONAL_ACCOUNTS = "get:functionalaccounts"
GET_FUNCTIONAL_ACCOUNTS_ID = "get:functionalaccounts/{id}"
POST_FUNCTIONAL_ACCOUNTS = "post:functionalaccounts"

# Entitlements
GET_ENTITLEMENTS = "get:entitlements"
GET_ENTITLEMENTS_GROUP_IDS = "get:entitlements:groupids"

# Entity Types
GET_ENTITY_TYPES = "get:entitytypes"

# User Groups
GET_USERGROUPS = "get:usergroups"
GET_USERGROUPS_ID = "get:usergroups/{id}"
GET_USERGROUPS_NAME = "get:usergroups?name={name}"
POST_USERGROUPS_BI = "post:usergroups:bi"
POST_USERGROUPS_ENTRAID = "post:usergroups:entraid"
POST_USERGROUPS_AD = "post:usergroups:ad"
POST_USERGROUPS_LDAP = "post:usergroups:ldap"
DELETE_USERGROUPS = "delete:usergroups?name={name}"
GET_USERGROUPS_ID_SMARTRULES = "get:usergroups/{id}/smartrules"

# Roles
GET_ROLES = "get:roles"

# User group roles constants for GET and POST
GET_USERGROUPS_ID_SMARTRULES_ROLES = (
    "get:usergroups/{id}/smartrules/{smartruleid}/roles"
)
POST_USERGROUPS_ID_SMARTRULES_ROLES = (
    "post:usergroups/{id}/smartrules/{smartruleid}/roles"
)

# ISA Requests
POST_ISA_REQUESTS = "post:isarequests"

# Platforms
GET_PLATFORMS = "get:platforms"

# Operating Systems
GET_OPERATING_SYSTEMS = "get:operatingsystems"

# Requests
GET_REQUESTS = "get:requests"
POST_REQUESTS = "post:requests"
POST_REQUESTS_ALIASES = "post:aliases/{aliasid}/requests"
PUT_REQUESTS_CHECKIN = "put:requests/{requestid}/checkin"
PUT_REQUESTS_APPROVE = "put:requests/{requestid}/approve"
PUT_REQUESTS_DENY = "put:requests/{requestid}/deny"
PUT_REQUESTS_ROTATE_ON_CHECKIN = "put:requests/{requestid}/rotateoncheckin"

# Request Termination
POST_REQUEST_TERMINATION_MANAGED_ACCOUNT_ID = (
    "post:managedaccounts/{managedaccountid}/requests/terminate"
)
POST_REQUEST_TERMINATION_MANAGED_SYSTEM_ID = (
    "post:managedsystems/{managedsystemid}/requests/terminate"
)
POST_REQUEST_TERMINATION_USER_ID = "post:users/{userid}/requests/terminate"

# Request Sets
GET_REQUEST_SETS = "get:requestsets"
POST_REQUEST_SETS = "post:requestsets"

# Password Rules
GET_PASSWORD_RULES = "get:passwordrules"  # nosec
GET_PASSWORD_RULES_ID = "get:passwordrules/{id}"  # nosec
GET_PASSWORD_RULES_ENABLED_PRODUCTS = (
    "get:passwordrules?enabledproducts={productname}"  # nosec
)

# Permissions
GET_PERMISSIONS = "get:permissions"
GET_USERGROUP_PERMISSIONS = "get:usergroups/{usergroupid}/permissions"
POST_USERGROUP_PERMISSIONS = "post:usergroups/{usergroupid}/permissions"
DELETE_USERGROUP_PERMISSIONS = "delete:usergroups/{usergroupid}/permissions"

# Credentials
GET_CREDENTIALS_REQUESTID = "get:credentials/{requestid}"
GET_CREDENTIALS_ALIASID = "get:aliases/{aliasid}/credentials/{requestid}"

# Access Policies
GET_ACCESS_POLICIES = "get:accesspolicies"
POST_ACCESS_POLICIES_TEST = "post:accesspolicies/test"

# API Registrations
GET_API_REGISTRATIONS = "get:apiregistrations"
GET_API_REGISTRATIONS_ID = "get:apiregistrations/{id}"
POST_API_REGISTRATIONS = "post:apiregistrations"
PUT_API_REGISTRATIONS_ID = "put:apiregistrations/{id}"

# Access levels
GET_ACCESS_LEVELS = "get:accesslevels"
POST_ACCESS_LEVELS_USERGROUPID_SMARTRULEID = (
    "post:usergroups/{usergroupid}/smartrules/{smartruleid}/accesslevels"
)

# Sessions
GET_SESSIONS = "get:sessions"
GET_SESSIONS_ID = "get:sessions/{id}"
POST_SESSIONS_REQUEST_ID = "post:requests/{requestid}/sessions"
POST_SESSIONS_ADMIN = "post:sessions/admin"

# Session locking
POST_SESSION_LOCK_SESSIONID = "post:sessions/{sessionid}/lock"
POST_SESSION_LOCK_MANAGED_ACCOUNT_ID = (
    "post:managedaccounts/{managedaccountid}/sessions/lock"
)
POST_SESSION_LOCK_MANAGED_SYSTEM_ID = (
    "post:managedsystems/{managedsystemid}/sessions/lock"
)

# Session termination
POST_SESSION_TERMINATE_SESSIONID = "post:sessions/{sessionid}/terminate"
POST_SESSION_TERMINATE_MANAGED_ACCOUNT_ID = (
    "post:managedaccounts/{managedaccountid}/sessions/terminate"
)
POST_SESSION_TERMINATE_MANAGED_SYSTEM_ID = (
    "post:managedsystems/{managedsystemid}/sessions/terminate"
)

# Quick Rules
GET_QUICK_RULES = "get:quickrules"
GET_QUICK_RULES_ID = "get:quickrules/{id}"

# Keystrokes
GET_SESSIONS_SESSIONID_KEYSTROKES = "get:sessions/{sessionid}/keystrokes"
GET_KEYSTROKES_ID = "get:keystrokes/{id}"
POST_KEYSTROKES_SEARCH = "post:keystrokes/search"

# Subscription Deliveries
GET_SUBSCRIPTIONS_DELIVERY = "get:subscriptions/delivery"
POST_SUBSCRIPTIONS_DELIVERY_DOWNLOAD = "post:subscriptions/delivery/download"

# EPM Policies
POST_EPM_POLICIES_ID_EPMAPPLICATIONS_ADD = "post:epmpolicies/{id}/epmapplications/add"

# Imports
POST_IMPORTS = "post:imports"

# Applications
GET_APPLICATIONS = "get:applications"
GET_APPLICATIONS_ID = "get:applications/{id}"
POST_MANAGED_ACCOUNT_APPLICATIONS = "post:managed_accounts/applications/{applicationid}"
DELETE_MANAGED_ACCOUNT_APPLICATIONS = (
    "delete:managed_accounts/applications/{applicationid}"
)

# Attribute types
GET_ATTRIBUTE_TYPES = "get:attributetypes"
GET_ATTRIBUTE_TYPES_ID = "get:attributetypes/{id}"
POST_ATTRIBUTE_TYPES = "post:attributetypes"
DELETE_ATTRIBUTE_TYPES_ID = "delete:attributetypes/{id}"

# Attributes
GET_ATTRIBUTES_ATTRIBUTE_TYPE_ID = "get:attributetypes/{id}/attributes"
GET_ATTRIBUTE_ID = "get:attributes/{id}"
POST_ATTRIBUTE_ATTRIBUTE_TYPE_ID = "post:attributetypes/{id}/attributes"
DELETE_ATTRIBUTE_ID = "delete:attributes/{id}"
GET_ATTRIBUTES_MANAGED_ACCOUNT_ID = "get:managedaccounts/{managedaccountid}/attributes"
GET_ATTRIBUTES_MANAGED_SYSTEM_ID = "get:managedsystems/{managedsystemid}/attributes"
POST_ATTRIBUTE_MANAGED_ACCOUNT_ID = (
    "post:managedaccounts/{managedaccountid}/attributes/{attributeid}"
)
POST_ATTRIBUTE_MANAGED_SYSTEM_ID = (
    "post:managedsystems/{managedsystemid}/attributes/{attributeid}"
)
DELETE_ATTRIBUTES_MANAGED_ACCOUNT_ID = (
    "delete:managedaccounts/{managedaccountid}/attributes"
)
DELETE_ATTRIBUTE_MANAGED_ACCOUNT_ID = (
    "delete:managedaccounts/{managedaccountid}/attributes/{attributeid}"
)
DELETE_ATTRIBUTES_MANAGED_SYSTEM_ID = (
    "delete:managedsystems/{managedsystemid}/attributes"
)
DELETE_ATTRIBUTE_MANAGED_SYSTEM_ID = (
    "delete:managedsystems/{managedsystemid}/attributes/{attributeid}"
)

# Oracle Internet Directories
GET_ORACLE_INTERNET_DIRECTORIES = "get:oracleinternetdirectories"
GET_ORACLE_INTERNET_DIRECTORIES_ID = "get:oracleinternetdirectories/{id}"
POST_ORACLE_INTERNET_DIRECTORIES_ID_SERVICES_QUERY = (
    "post:oracleinternetdirectories/{id}/services/query"
)
POST_ORACLE_INTERNET_DIRECTORIES_ID_TEST = "post:oracleinternetdirectories/{id}/test"

# Ticket Systems
GET_TICKET_SYSTEMS = "get:ticketsystems"

# Aliases
GET_ALIASES = "get:aliases"
GET_ALIASES_ID = "get:aliases/{id}"
GET_ALIASES_NAME = "get:aliases?name={name}"

# Propagation action types
GET_PROPAGATION_ACTION_TYPES = "get:propagationactiontypes"

# Propagation actions
GET_PROPAGATION_ACTIONS = "get:propagationactions"
GET_PROPAGATION_ACTIONS_ID = "get:propagationactions/{id}"
GET_MANAGED_ACCOUNTS_PROPAGATION_ACTIONS = (
    "get:managedaccounts/{managedaccountid}/propagationactions"
)
POST_MANAGED_ACCOUNT_PROPAGATION_ACTIONS = (
    "post:managedaccounts/{managedaccountid}/propagationactions/{propagationactionid}"
)
DELETE_MANAGED_ACCOUNTS_PROPAGATION_ACTIONS = (
    "delete:managedaccounts/{managedaccountid}/propagationactions"
)
DELETE_MANAGED_ACCOUNT_ID_PROPAGATION_ACTION_ID = (
    "delete:managedaccounts/{managedaccountid}/propagationactions/{propagationactionid}"
)

# DSS Key policies
GET_DSS_KEY_RULES = "get:dsskeyrules"
GET_DSS_KEY_RULES_ID = "get:dsskeyrules/{id}"
