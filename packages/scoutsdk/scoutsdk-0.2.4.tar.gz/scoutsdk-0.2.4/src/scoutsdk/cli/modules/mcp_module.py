import argparse
import json
import asyncio
from pathlib import Path
from scoutsdk.cli.modules.base_module import BaseModule
from scoutsdk.cli.config import Config
from ..error_handler import ValidationError


class MCPModule(BaseModule):
    def __init__(self, config: Config):
        self.config = config

    def get_command(self) -> str:
        return "mcp"

    def add_parser(self, subparsers: argparse._SubParsersAction) -> None:
        mcp_parser = subparsers.add_parser(
            self.get_command(), help="Run MCP server for Scout assistant"
        )

        mcp_parser.add_argument(
            "-c",
            "--config",
            help="Path to JSON configuration file",
            type=str,
        )

        mcp_parser.add_argument(
            "--debug", help="Enable debug logging", action="store_true"
        )

        mcp_parser.set_defaults(func=self.execute)

    def execute(self, args: argparse.Namespace) -> None:
        try:
            from scoutmcp import run_native_server
        except ImportError:
            raise ValidationError(
                "MCP dependencies are not installed. "
                "Install them with: pip install scoutsdk[mcp]"
            )

        import logging

        if args.debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

        mcp_config = {}

        # Load from config file if provided
        if args.config:
            config_path = Path(args.config)

            if not config_path.exists():
                raise ValidationError(f"Config file not found: {config_path}")

            try:
                with open(config_path, "r") as f:
                    mcp_config = json.load(f)
            except json.JSONDecodeError as e:
                raise ValidationError(f"Invalid JSON in config file: {e}")

            print(f"Starting MCP server with config from {config_path}")
        else:
            print("Starting MCP server with environment variables")

        try:
            asyncio.run(run_native_server(mcp_config))
        except KeyboardInterrupt:
            print("MCP server stopped by user")
        except Exception as e:
            raise ValidationError(f"MCP server error: {e}")
