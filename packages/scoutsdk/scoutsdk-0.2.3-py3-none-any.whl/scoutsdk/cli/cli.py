import argparse
import importlib.metadata
from .config import Config, CONFIG_API_ACCESS_TOKEN, CONFIG_API_URL
from .error_handler import handle_exception, set_verbosity
from .modules.assistants_module import AssistantsModule
from .modules.functions_module import FunctionsModule
from .modules.apps_module import AppsModule
from .modules.mcp_module import MCPModule
from .modules.skills_module import SkillsModule
from ..api.api import ScoutAPI


class ScoutCLI:
    def __init__(self) -> None:
        # Initialize modules
        self.config = Config()
        self.modules = [
            AssistantsModule(config=self.config),
            FunctionsModule(config=self.config),
            AppsModule(config=self.config),
            MCPModule(config=self.config),
            SkillsModule(config=self.config),
        ]

        # Create command mapping
        self.commands = {
            module.get_command(): module.execute for module in self.modules
        }

        # Get version from package metadata
        version = importlib.metadata.version("scoutsdk")

        # Setup parser
        self.parser = argparse.ArgumentParser(description="Scout CLI")
        self.parser.add_argument("--version", action="version", version=version)
        self.parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Enable verbose output with detailed error information",
        )

        # Create subparsers for commands
        subparsers = self.parser.add_subparsers(required=False)

        # Add module parsers
        for module in self.modules:
            module.add_parser(subparsers=subparsers)

    def _create_scout_api(self) -> ScoutAPI:
        api_access_token = self.config.get(CONFIG_API_ACCESS_TOKEN, None)
        api_url = self.config.get(CONFIG_API_URL, None)  # Returns None if not found
        return ScoutAPI(base_url=api_url, api_access_token=api_access_token)

    def execute(self) -> None:
        """Execute the specified command with given arguments"""
        args = self.parser.parse_args()

        # Set verbosity level
        set_verbosity(verbose=args.verbose)

        # If no subcommand was provided, show help
        if not hasattr(args, "func"):
            self.parser.print_help()
            return

        # Execute the command through the handle_exception decorator
        handle_exception(args.func)(args)


@handle_exception
def main() -> None:
    cli = ScoutCLI()
    cli.execute()
