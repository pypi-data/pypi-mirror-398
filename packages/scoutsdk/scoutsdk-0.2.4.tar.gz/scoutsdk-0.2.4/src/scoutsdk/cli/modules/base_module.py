from abc import ABC, abstractmethod
import argparse


class BaseModule(ABC):
    @abstractmethod
    def get_command(self) -> str:
        """Return the command name for this module"""
        pass

    @abstractmethod
    def add_parser(self, subparsers: argparse._SubParsersAction) -> None:
        """Add command-specific parser to the subparsers"""
        pass

    @abstractmethod
    def execute(self, args: argparse.Namespace) -> None:
        """
        Execute the module's command

        This method should raise appropriate exceptions (ValidationError, APIError, etc.)
        when errors occur rather than handling them directly.
        The exceptions will be caught and handled at the top level.
        """
        pass
