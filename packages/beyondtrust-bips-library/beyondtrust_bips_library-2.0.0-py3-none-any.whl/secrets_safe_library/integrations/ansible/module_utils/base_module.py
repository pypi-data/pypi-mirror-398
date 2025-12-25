"""Module Base class"""

# flake8: noqa: E402
# -*- coding: utf-8 -*-
# (c) 2025 BeyondTrust Inc.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
import logging
from typing import Any

from ansible.module_utils.basic import AnsibleModule

from secrets_safe_library.integrations.ansible.common_utils.logger import Logger


class BaseModule:
    """
    Module Base class.
    """

    def __init__(self, module: AnsibleModule):
        self.module = module
        self.params = self.module.params
        self.res_args: dict[str, Any] = {}

        self.log = Logger(
            getattr(logging, self.params.get("log_level", "DEBUG"), logging.DEBUG),
            self.params.get("log_file_name", "ansible-collection-modules-logs"),
        )
        self.log.logger.debug("Log Level: %s", self.log.logger.level)

    def fail(self, msg: str):
        """
        Fail return.
        Args:
            msg (str): Error message.
        """
        self.module.fail_json(msg=msg, **self.res_args)

    def success(self, **kwargs):
        """
        Success return.
        Args:
            kwargs (dict): Data to return.
        """
        self.res_args.update(kwargs)
        self.module.exit_json(**self.res_args)
