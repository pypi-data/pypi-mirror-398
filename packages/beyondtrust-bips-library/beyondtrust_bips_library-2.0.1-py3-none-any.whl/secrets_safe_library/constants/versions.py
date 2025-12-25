from enum import Enum


class Version(Enum):
    """
    Available request body versions from PS API.
    """

    DEFAULT = "DEFAULT"  # Used for entities that doesn't have versioning.
    V3_0 = "3.0"
    V3_1 = "3.1"
    V3_2 = "3.2"
    V3_3 = "3.3"
    V3_4 = "3.4"
    V3_5 = "3.5"
