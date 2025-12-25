import os
import logging
import json
from typing import Any, Optional

from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from scoutsdk import ScoutAPI
from scouttypes.assistants import (
    AssistantCustomFunction,
    AssistantCustomFunctionsResponse,
)
from .config import MCPConfig
from .exceptions import ScoutMCPError

logger = logging.getLogger(__name__)


class NativeScoutMCPServer:
    def __init__(self, config: MCPConfig):
        self.config = config
        self.scout_api = ScoutAPI(
            base_url=config.scout_api_url, api_access_token=config.scout_api_token
        )
        self.server = Server(name=config.server_name, version="1.0.0")
        self._available_functions: list[AssistantCustomFunction] = []

        self._register_handlers()

    def _register_handlers(self) -> None:
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            try:
                logger.debug(
                    f"Listing tools for assistant: {self.config.scout_mcp_assistant_id}"
                )

                functions_response: AssistantCustomFunctionsResponse = (
                    self.scout_api.assistants.get_functions(
                        self.config.scout_mcp_assistant_id
                    )
                )
                functions: list[AssistantCustomFunction] = functions_response.functions

                self._available_functions = functions

                logger.info(
                    f"Found {len(functions)} functions for assistant {self.config.scout_mcp_assistant_id}"
                )

                tools = []
                for func in functions:
                    tool = types.Tool(
                        name=func.function_name,
                        description=func.description or f"Execute {func.function_name}",
                        inputSchema=func.parameters,
                    )
                    tools.append(tool)
                    logger.debug(f"Added tool: {func.function_name}")

                return tools

            except Exception as e:
                logger.error(f"Failed to list tools: {e}", exc_info=True)
                raise ScoutMCPError(
                    f"Failed to list tools: {str(e)}",
                    assistant_id=self.config.scout_mcp_assistant_id,
                ) from e

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Optional[dict[str, Any]]
        ) -> list[types.ContentBlock]:
            try:
                logger.debug(f"Calling tool '{name}' with arguments: {arguments}")

                available_tool_names = [
                    func.function_name for func in self._available_functions
                ]
                if name not in available_tool_names:
                    error_msg = f"Tool '{name}' not found. Available tools: {available_tool_names}"
                    logger.error(error_msg)
                    return [types.TextContent(type="text", text=f"Error: {error_msg}")]

                result = self.scout_api.assistants.execute_function(
                    assistant_id=self.config.scout_mcp_assistant_id,
                    function_name=name,
                    payload=arguments or {},
                )

                logger.debug(f"Tool '{name}' execution result: {result}")

                if isinstance(result, dict):
                    result_text = json.dumps(result, indent=2)
                elif isinstance(result, str):
                    result_text = result
                else:
                    result_text = str(result)

                return [types.TextContent(type="text", text=result_text)]

            except Exception as e:
                logger.error(f"Failed to execute tool '{name}': {e}", exc_info=True)
                return [
                    types.TextContent(
                        type="text", text=f"Error executing tool '{name}': {str(e)}"
                    )
                ]

    async def run(self) -> None:
        try:
            logger.info(f"Starting Scout MCP Server: {self.config.server_name}")
            logger.info(f"MCP Assistant ID: {self.config.scout_mcp_assistant_id}")
            logger.info(f"Scout API URL: {self.config.scout_api_url}")

            async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name=self.config.server_name,
                        server_version="1.0.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={},
                        ),
                    ),
                )

        except Exception as e:
            logger.error(f"Failed to run MCP server: {e}", exc_info=True)
            raise ScoutMCPError(
                f"Server runtime failed: {str(e)}",
                assistant_id=self.config.scout_mcp_assistant_id,
            ) from e


async def run_native_server(config_dict: dict[str, Any]) -> None:
    config = MCPConfig(
        server_name=os.getenv("MCP_SERVER_NAME")
        or config_dict.get("server_name")
        or "Scout Native MCP Server",
        scout_mcp_assistant_id=os.getenv("SCOUT_MCP_ASSISTANT_ID")
        or config_dict.get("scout_mcp_assistant_id")
        or "",
        scout_api_token=os.getenv("SCOUT_API_TOKEN")
        or config_dict.get("scout_api_token")
        or "",
        scout_api_url=os.getenv("SCOUT_API_URL")
        or config_dict.get("scout_api_url")
        or "",
    )

    server = NativeScoutMCPServer(config=config)
    await server.run()
