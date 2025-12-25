from dataclasses import dataclass


@dataclass
class SSHConfig:
    """Data class to hold SSH configuration details."""

    private_key: str = ""
    passphrase: str = ""
    elevation_command: str = ""
