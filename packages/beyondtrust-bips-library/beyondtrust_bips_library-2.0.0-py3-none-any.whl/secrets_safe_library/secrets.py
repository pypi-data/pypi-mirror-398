"""Secrets Interface"""

from abc import ABC, abstractmethod


class Secrets(ABC):
    @abstractmethod
    def get_secrets(self, paths):
        pass
        # Parameters => ["path1/secret_title", "path2/secret_title"] => Keeping same
        # order
        # response => {"path1": "password_content", "path2": "password_content"}

    def get_secrets_with_metadata(self, paths):
        pass
        # Parameters => ["path1/secret_title", "path2/secret_title"] => Keeping same
        # order
        # response => {"path1": "password_content", "path1-metadata": "{}", "path2":
        # "password_content",  "path2-metadata": "{}"}

    @abstractmethod
    def get_secret(self, path):
        pass
        # Parameters => "path/secret_title"
        # response => "password_content"

    def get_secret_with_metadata(self, path):
        pass
        # Parameters => "path/secret_title"
        # response => {"path1": "password_content", "path1-metadata": "{}"}
