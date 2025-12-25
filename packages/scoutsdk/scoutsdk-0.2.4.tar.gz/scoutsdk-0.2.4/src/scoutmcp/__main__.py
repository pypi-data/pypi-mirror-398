import sys
import json
import logging
import asyncio
from pathlib import Path
from .native_mcp_server import run_native_server


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Check for help flag
    if len(sys.argv) >= 2 and sys.argv[1] in ["-h", "--help"]:
        logging.info("Usage: python -m scoutmcp [config.json]")
        logging.info("")
        logging.info("Optional config file containing JSON with:")
        logging.info("  - server_name: Name for the MCP server")
        logging.info("  - scout_mcp_assistant_id: Assistant UUID to use")
        logging.info("  - scout_api_token: API authentication token")
        logging.info("  - scout_api_url: Scout API base URL")
        logging.info("")
        logging.info("Alternatively, use environment variables:")
        logging.info("  - MCP_SERVER_NAME")
        logging.info("  - SCOUT_MCP_ASSISTANT_ID")
        logging.info("  - SCOUT_API_TOKEN")
        logging.info("  - SCOUT_API_URL")
        sys.exit(0)

    # Parse command line arguments
    config_file = None

    args = sys.argv[1:]
    for arg in args:
        if not arg.startswith("--"):
            config_file = arg
            break

    config = {}

    # Load config file if provided
    if config_file:
        config_path = Path(config_file)
        if not config_path.exists():
            logging.error(f"Config file not found: {config_path}")
            sys.exit(1)

        with open(config_path, "r") as f:
            config = json.load(f)

    # Run the native server implementation
    asyncio.run(run_native_server(config))


if __name__ == "__main__":
    main()
