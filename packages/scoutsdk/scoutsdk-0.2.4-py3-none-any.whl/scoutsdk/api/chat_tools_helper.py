import json
from typing import Any, Optional, Callable, Generator, Dict, List, TYPE_CHECKING
import requests
from scouttypes.chat import (
    ChatCompletionRequest,
)
from scouttypes.conversations import (
    MessageRole,
    ConversationMessage,
    MessageToolCall,
    ToolCallFunction,
)

if TYPE_CHECKING:
    from .chat import ChatAPI


class ToolCallAccumulator:
    """Accumulates tool call data from streaming chunks."""

    def __init__(self) -> None:
        self.tool_calls: Dict[str, Dict[str, Any]] = {}

    def add_chunk(self, chunk: Dict[str, Any]) -> None:
        """Add a streaming chunk and accumulate tool call data."""
        tool_calls = chunk.get("tool_calls", [])

        for tool_call in tool_calls:
            # Handle Scout's streaming format
            call_id = tool_call.get("call_id", "") or tool_call.get("id", "")

            if call_id not in self.tool_calls:
                self.tool_calls[call_id] = {
                    "id": call_id,
                    "type": "function",  # Default to function type
                    "function": {
                        "name": tool_call.get("tool_name", "")
                        or tool_call.get("function", {}).get("name", ""),
                        "arguments": "",
                    },
                }

            # Update function name if provided
            if "tool_name" in tool_call and tool_call["tool_name"]:
                self.tool_calls[call_id]["function"]["name"] = tool_call["tool_name"]

            # Accumulate function arguments
            function_args = tool_call.get("arguments", "") or tool_call.get(
                "function", {}
            ).get("arguments", "")
            if function_args:
                self.tool_calls[call_id]["function"]["arguments"] += function_args

    def get_completed_tool_calls(self) -> List[MessageToolCall]:
        """Get completed tool calls as MessageToolCall objects."""
        tool_calls = []
        for tool_call_data in self.tool_calls.values():
            tool_call = MessageToolCall(
                id=tool_call_data["id"],
                type=tool_call_data["type"],
                function=ToolCallFunction(
                    name=tool_call_data["function"]["name"],
                    arguments=tool_call_data["function"]["arguments"],
                ),
            )
            tool_calls.append(tool_call)
        return tool_calls


class StreamingToolCallWrapper:
    """Wrapper for streaming responses that handles tool calls."""

    def __init__(
        self,
        chat_api: "ChatAPI",
        conversation_messages: List[ConversationMessage],
        tools: List[Callable],
        model: Optional[str] = None,
        assistant_id: Optional[str] = None,
        debug: Optional[bool] = False,
        llm_args: Optional[dict] = None,
        max_tool_iterations: int = 5,
    ):
        self.chat_api = chat_api
        self.conversation_messages = conversation_messages.copy()
        self.tools = tools
        self.model = model
        self.assistant_id = assistant_id
        self.debug = debug
        self.llm_args = llm_args or {}
        self.max_tool_iterations = max_tool_iterations
        self.tools_dict = {}

        # Build tools dictionary
        for tool in tools:
            if hasattr(tool, "function_name"):
                func_name = tool.function_name
            else:
                func_name = tool.__name__
            self.tools_dict[func_name] = tool

    def stream_with_tools(
        self, request_payload: ChatCompletionRequest
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream response and handle tool calls."""
        from .project_helpers import scout

        iteration = 0
        current_messages = self.conversation_messages.copy()

        while iteration < self.max_tool_iterations:
            # Make streaming request
            json_payload = request_payload.model_dump(exclude_none=True)
            # Clean up messages for API - remove fields that might cause issues
            clean_messages = []
            for msg in current_messages:
                clean_msg = msg.model_dump(exclude_none=True)
                # Remove fields that might not be expected in streaming requests
                if "metadata" in clean_msg and clean_msg["metadata"] is None:
                    del clean_msg["metadata"]
                if "reasoning" in clean_msg and clean_msg["reasoning"] is None:
                    del clean_msg["reasoning"]
                if "finish_reason" in clean_msg and clean_msg["finish_reason"] is None:
                    del clean_msg["finish_reason"]
                clean_messages.append(clean_msg)
            json_payload["messages"] = clean_messages

            if self.debug:
                print(f"streaming payload: {json_payload}")

            response = requests.post(
                url=f"{self.chat_api._base_url}/api/chat/completion/",
                headers=self.chat_api._headers,
                json=json_payload,
                stream=True,
            )

            # Process streaming response
            accumulated_current_data = ""
            finish_reason = None
            has_tool_calls = False

            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    decoded_chunk = chunk.decode("utf-8")
                    if decoded_chunk.strip() == ":" or len(decoded_chunk) == 0:
                        continue

                    current_data = accumulated_current_data + decoded_chunk
                    accumulated_current_data = ""

                    if not current_data.endswith("\n"):
                        accumulated_current_data += current_data
                        continue

                    chunks = current_data.strip().split("\n")

                    for chunk_line in chunks:
                        if chunk_line and chunk_line.strip() != ":":
                            try:
                                chunk_data = json.loads(chunk_line)

                                # Check for tool calls and finish reason
                                if "tool_calls" in chunk_data:
                                    has_tool_calls = True

                                if "finish_reason" in chunk_data:
                                    finish_reason = chunk_data["finish_reason"]

                                # Always yield the chunk to the user
                                yield chunk_data

                            except json.JSONDecodeError:
                                continue

            # Check if we need to execute tool calls
            if finish_reason == "tool_call" and has_tool_calls:
                # Extract tool calls from the final chunks
                final_tool_calls = []

                # Re-process the last batch of chunks to extract complete tool calls
                for chunk_line in chunks:
                    if chunk_line and chunk_line.strip() != ":":
                        try:
                            chunk_data = json.loads(chunk_line)
                            if (
                                chunk_data.get("finish_reason") == "tool_call"
                                and "tool_calls" in chunk_data
                            ):
                                for tool_call in chunk_data["tool_calls"]:
                                    call_id = tool_call.get(
                                        "call_id", ""
                                    ) or tool_call.get("id", "")
                                    func_name = tool_call.get(
                                        "tool_name", ""
                                    ) or tool_call.get("function", {}).get("name", "")
                                    func_args = tool_call.get(
                                        "arguments", ""
                                    ) or tool_call.get("function", {}).get(
                                        "arguments", ""
                                    )

                                    final_tool_call = MessageToolCall(
                                        id=call_id,
                                        type="function",
                                        function=ToolCallFunction(
                                            name=func_name, arguments=func_args
                                        ),
                                    )
                                    final_tool_calls.append(final_tool_call)
                        except json.JSONDecodeError:
                            continue

                if final_tool_calls:
                    # Add assistant message with tool calls to conversation
                    assistant_message = ConversationMessage(
                        role=MessageRole.ASSISTANT,
                        content=None,  # Tool calls usually don't have content
                        tool_calls=final_tool_calls,
                    )
                    current_messages.append(assistant_message)

                    # Execute tool calls
                    for tool_call in final_tool_calls:
                        func_name = tool_call.function.name
                        func_args_str = tool_call.function.arguments

                        try:
                            # Parse function arguments
                            func_args = (
                                json.loads(func_args_str) if func_args_str else {}
                            )

                            # Execute the tool
                            if func_name in self.tools_dict:
                                tool_result = scout.call_custom_function(
                                    self.tools_dict[func_name], func_args
                                )
                                result_content = (
                                    json.dumps(tool_result)
                                    if not isinstance(tool_result, str)
                                    else tool_result
                                )
                            else:
                                result_content = f"Error: Tool '{func_name}' not found"

                            # Add tool result to conversation
                            tool_response = ConversationMessage(
                                role=MessageRole.TOOL,
                                content=result_content,
                                tool_call_id=tool_call.id,
                            )
                            current_messages.append(tool_response)

                        except Exception as e:
                            # Add error message for failed tool call
                            error_response = ConversationMessage(
                                role=MessageRole.TOOL,
                                content=f"Error executing tool '{func_name}': {str(e)}",
                                tool_call_id=tool_call.id,
                            )
                            current_messages.append(error_response)

                    # Continue with next iteration to get assistant's response to tool results
                    iteration += 1
                    continue  # Go back to while loop for next streaming request

            # If no tool calls or not a tool_call finish_reason, we're done
            break

        if iteration >= self.max_tool_iterations:
            raise Exception(
                f"Maximum tool iterations ({self.max_tool_iterations}) exceeded"
            )
