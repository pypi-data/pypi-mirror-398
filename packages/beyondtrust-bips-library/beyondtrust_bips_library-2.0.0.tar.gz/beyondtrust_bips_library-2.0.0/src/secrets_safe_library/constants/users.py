from enum import Enum


class UserType(Enum):
    """
    Available user types.
    """

    USER_TYPE_BI = "BeyondInsight"
    USER_TYPE_AD = "ActiveDirectory"
    USER_TYPE_LDAP = "LdapDirectory"
    USER_TYPE_APP = "Application"
    USER_TYPE_ENTRAID = "EntraId"
