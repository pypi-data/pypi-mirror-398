"""Logger class, used for logging messages."""

# flake8: noqa: E402
# -*- coding: utf-8 -*-
# (c) 2025 BeyondTrust Inc.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
try:
    import logging
    from logging.handlers import RotatingFileHandler
except ImportError:
    pass


class Logger:
    """
    Logger class, used to define a logger instance.
    """

    def __init__(self, log_level: int, log_file_name: str) -> None:
        """
        Initialize a new Logger instance.

        Args:
            log_level (int): Logging level.
            log_file_name (str): Name of the log file.
        """
        self.logger = logging.getLogger(log_file_name)
        self.logger.setLevel(log_level)

        if not self.logger.handlers:
            handler = RotatingFileHandler(
                f"{log_file_name}.log",
                maxBytes=1_000_000,
                backupCount=5,
                encoding="utf-8",
            )
            formatter = logging.Formatter(
                "%(asctime)-5s %(name)-15s %(levelname)-8s %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        return
