import json
from typing import Any, Optional, Type, overload, TypeVar, Callable, Generator, Dict
from pydantic import BaseModel

from .chat_tools_helper import StreamingToolCallWrapper
from .request_utils import RequestUtils
from scouttypes.chat import (
    ChatCompletionResponse,
    ChatCompletionRequest,
)
from scouttypes.conversations import (
    StreamFinishReason,
    StreamError,
    MessageRole,
    ConversationMessage,
)

ChatCompletionResponseType = TypeVar("ChatCompletionResponseType", bound=BaseModel)


class ChatAPI:
    def __init__(self, base_url: str, headers: dict, retry_strategy: Callable) -> None:
        self._base_url = base_url
        self._headers = headers
        self._retry_strategy = retry_strategy

    @overload
    def completion(
        self,
        messages: list[ConversationMessage] | str,
        response_format: Type[ChatCompletionResponseType],
        model: Optional[str] = None,
        assistant_id: Optional[str] = None,
        stream: bool = False,
        debug: Optional[bool] = False,
        allowed_tools: Optional[list[str]] = None,
        llm_args: Optional[dict] = None,
        tools: Optional[list[Callable]] = None,
        max_tool_iterations: int = 5,
    ) -> ChatCompletionResponseType: ...

    @overload
    def completion(
        self,
        messages: list[ConversationMessage] | str,
        response_format: Optional[None] = None,
        model: Optional[str] = None,
        assistant_id: Optional[str] = None,
        stream: bool = False,
        debug: Optional[bool] = False,
        allowed_tools: Optional[list[str]] = None,
        llm_args: Optional[dict] = None,
        tools: Optional[list[Callable]] = None,
        max_tool_iterations: int = 5,
    ) -> ChatCompletionResponse: ...

    def completion(
        self,
        messages: list[ConversationMessage] | str,
        response_format: Optional[Type[ChatCompletionResponseType]] = None,
        model: Optional[str] = None,
        assistant_id: Optional[str] = None,
        stream: bool = False,
        debug: Optional[bool] = False,
        allowed_tools: Optional[list[str]] = None,
        llm_args: Optional[dict] = None,
        tools: Optional[list[Callable]] = None,
        max_tool_iterations: int = 5,
    ) -> (
        ChatCompletionResponseType
        | ChatCompletionResponse
        | Generator[Dict[str, Any], None, None]
    ):
        """
        Send a chat completion request to the Scout API.

        Args:
            messages (list[ConversationMessage] | str): The list of chat messages or a single user message string.
            response_format (Optional[Type[ChatCompletionResponseType]]): Pydantic model to use for response validation.
            model (str): The model to use for completion (default: "gpt-4o").
            assistant_id (Optional[str]): The assistant ID to use for the request.
            stream (bool): Whether to stream the response (default: False).
            debug (Optional[bool]): If True, print the payload for debugging.
            allowed_tools (Optional[list[str]]): List of allowed tools for the assistant. None = Use all available tools, Empty list = No tools.
            llm_args (Optional[dict]): Additional arguments to pass to the LLM API.
            tools (Optional[list[Callable]]): List of functions that can be called as tools. If provided, enables tool calling functionality.
            max_tool_iterations (int): Maximum number of tool call iterations to prevent infinite loops (default: 5).

        Returns:
            ChatCompletionResponseType | ChatCompletionResponse: If response_format is provided, returns a validated instance of the specified ChatCompletionResponseType model. Otherwise, returns a ChatCompletionResponse object.

        Raises:
            Exception: If there is an error processing the response, especially when response_format is used.
        """

        # If tools are provided, use the tool calling functionality
        if tools is not None and len(tools) > 0:
            if stream:
                # Use streaming wrapper for tool calls
                stream_generator = self._completion_with_tools_streaming(
                    messages=messages,
                    tools=tools,
                    response_format=response_format,
                    model=model,
                    assistant_id=assistant_id,
                    debug=debug,
                    llm_args=llm_args,
                    allowed_tools=allowed_tools,
                    max_tool_iterations=max_tool_iterations,
                )
                final_chunk = RequestUtils.consume_stream_generator(stream_generator)
                chat_completion_response = self._convert_streaming_response(final_chunk)

                if response_format:
                    try:
                        if not chat_completion_response.messages:
                            raise ValueError(
                                "No messages in response to extract content from"
                            )
                        content = chat_completion_response.messages[-1].content
                        if not isinstance(content, str):
                            raise ValueError(
                                f"Expected string content for response format parsing, got {type(content)}"
                            )
                        return response_format.model_validate(json.loads(content))
                    except Exception as e:
                        raise Exception(
                            f"Error processing Response: {chat_completion_response}"
                        ) from e

                return chat_completion_response
            else:
                return self._completion_with_tools(
                    messages=messages,
                    tools=tools,
                    response_format=response_format,
                    model=model,
                    assistant_id=assistant_id,
                    stream=stream,
                    allowed_tools=allowed_tools,
                    debug=debug,
                    llm_args=llm_args,
                    max_tool_iterations=max_tool_iterations,
                )

        if isinstance(messages, str):
            messages = [ConversationMessage(role=MessageRole.USER, content=messages)]

        request_payload = ChatCompletionRequest(
            messages=messages,
            model=model,
            assistant_id=assistant_id,
            stream=stream,
            allowed_tools=allowed_tools,
            llm_args=llm_args,
            response_format=response_format.model_json_schema()
            if response_format
            else None,
        )

        json_payload = request_payload.model_dump(exclude_none=True)
        if debug:
            print(f"payload: {json_payload}")

        response, status_code = RequestUtils.post(
            url=f"{self._base_url}/api/chat/completion/",
            headers=self._headers,
            json_payload=json_payload,
            stream=stream,
            retry_strategy=self._retry_strategy,
        )

        if stream:
            chat_completion_response = self._convert_streaming_response(response)
        else:
            chat_completion_response = ChatCompletionResponse.model_validate(response)

        if response_format:
            # extract the last message from the response to ignore tools calls
            try:
                if not chat_completion_response.messages:
                    raise ValueError("No messages in response to extract content from")
                content = chat_completion_response.messages[-1].content
                # todo handle other content types
                if not isinstance(content, str):
                    raise ValueError(
                        f"Expected string content for response format parsing, got {type(content)}"
                    )
                return response_format.model_validate(json.loads(content))
            except Exception as e:
                raise Exception(f"Error processing Response: {response}") from e

        return chat_completion_response

    def _convert_streaming_response(self, response: Any) -> ChatCompletionResponse:
        if not isinstance(response, dict):
            message_data = {"role": "assistant", "content": str(response)}
            return ChatCompletionResponse(
                messages=[ConversationMessage.model_validate(message_data)]
            )

        if response.get("finish_reason", "") == StreamFinishReason.ERROR:
            error_data = response.get("error")
            # Handle case where error field is None or missing
            if error_data is None:
                # Create a default error if none is provided
                error = StreamError(
                    error_code="unknown_error",
                    reference_id="",
                    message="An error occurred but no error details were provided",
                )
            else:
                try:
                    error = StreamError.model_validate(error_data)
                except Exception as e:
                    # If error validation fails, create a fallback error
                    error = StreamError(
                        error_code="validation_error",
                        reference_id="",
                        message=f"Error validation failed: {str(e)}",
                    )

            return ChatCompletionResponse(messages=[], error=error)

        return ChatCompletionResponse(
            messages=[ConversationMessage.model_validate(response)]
        )

    def _convert_tools_to_openai_format(
        self, tools: list[Callable]
    ) -> tuple[dict[str, Callable], list[dict[str, Any]]]:
        """
        Convert Scout tools to OpenAI tool format.

        This method works with both:
        1. Functions decorated with @scout.function (legacy support)
        2. Plain functions (extracts info dynamically using scout.create_pydantic)

        Returns:
            Tuple of (tools_dict, tool_definitions) where:
            - tools_dict: Mapping of function names to callable functions
            - tool_definitions: List of OpenAI tool definition dictionaries
        """
        from .project_helpers import scout

        tools_dict = {}
        tool_definitions = []

        for tool in tools:
            # Use function name from __name__ (works for both decorated and plain functions)
            func_name = tool.__name__

            # Use function docstring for description (works for both decorated and plain functions)
            func_description = tool.__doc__ or "No description available"

            # For parameters, check if function has scout decorator metadata, otherwise generate it
            if hasattr(tool, "parameters"):
                # Function was decorated with @scout.function, use existing parameters
                func_parameters = tool.parameters
            else:
                # Plain function - generate parameters using scout.create_pydantic
                try:
                    params_model = scout.create_pydantic(tool)
                    func_parameters = params_model.model_json_schema()
                except Exception:
                    # Fallback to empty schema if pydantic creation fails
                    func_parameters = {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    }

            tools_dict[func_name] = tool
            tool_definitions.append(
                {
                    "type": "function",
                    "function": {
                        "name": func_name,
                        "description": func_description,
                        "parameters": func_parameters,
                    },
                }
            )
        return tools_dict, tool_definitions

    def _completion_with_tools(
        self,
        messages: list[ConversationMessage] | str,
        tools: list[Callable],
        response_format: Optional[Type[ChatCompletionResponseType]] = None,
        model: Optional[str] = None,
        assistant_id: Optional[str] = None,
        stream: bool = False,
        allowed_tools: Optional[list[str]] = None,
        debug: Optional[bool] = False,
        llm_args: Optional[dict] = None,
        max_tool_iterations: int = 5,
    ) -> ChatCompletionResponseType | ChatCompletionResponse:
        """
        Internal method for handling tool calling functionality.
        """
        from .project_helpers import scout

        # Convert tools to OpenAI tool format
        tools_dict, tool_definitions = self._convert_tools_to_openai_format(tools)

        # Prepare conversation history
        if isinstance(messages, str):
            conversation_messages = [
                ConversationMessage(role=MessageRole.USER, content=messages)
            ]
        else:
            conversation_messages = messages.copy()

        # Prepare llm_args with tools
        final_llm_args = llm_args.copy() if llm_args else {}

        final_llm_args["tools"] = tool_definitions

        iteration = 0

        while iteration < max_tool_iterations:
            # For tool calling, we need to disable streaming during intermediate calls
            # to properly detect and execute tool calls. Only enable streaming for the final response.
            current_stream = False

            # Call completion API without tools to avoid infinite recursion
            request_payload = ChatCompletionRequest(
                messages=conversation_messages,
                model=model,
                assistant_id=assistant_id,
                stream=current_stream,
                allowed_tools=allowed_tools,
                llm_args=final_llm_args,
                response_format=response_format.model_json_schema()
                if response_format
                else None,
            )

            json_payload = request_payload.model_dump(exclude_none=True)
            if debug:
                print(f"payload: {json_payload}")

            api_response, status_code = RequestUtils.post(
                url=f"{self._base_url}/api/chat/completion/",
                headers=self._headers,
                json_payload=json_payload,
                stream=current_stream,
                retry_strategy=self._retry_strategy,
            )

            if current_stream:
                response = self._convert_streaming_response(api_response)
            else:
                response = ChatCompletionResponse.model_validate(api_response)

            if not response.messages:
                break

            last_message = response.messages[-1]

            # Check if the last message has tool calls
            if not last_message.tool_calls:
                # No tool calls, we're done with the conversation
                conversation_messages.extend(response.messages)

                # Note: When tools are used, streaming is disabled during tool execution
                # for proper tool call detection and execution. This is standard behavior
                # for tool-enabled chat completion APIs.

                # If response_format is specified, parse the final content
                if response_format:
                    try:
                        if not last_message.content or not isinstance(
                            last_message.content, str
                        ):
                            raise ValueError(
                                "No valid content to parse for response format"
                            )
                        return response_format.model_validate(
                            json.loads(last_message.content)
                        )
                    except Exception as e:
                        raise Exception(f"Error processing Response: {response}") from e

                return response

            # Add the assistant's message with tool calls to conversation
            conversation_messages.extend(response.messages)

            # Find all messages with tool calls in the response
            tool_calls_to_execute = []
            for message in response.messages:
                if message.tool_calls:
                    tool_calls_to_execute.extend(message.tool_calls)

            # Execute all tool calls
            for tool_call in tool_calls_to_execute:
                func_name = tool_call.function.name
                func_args_str = tool_call.function.arguments

                try:
                    # Parse function arguments
                    func_args = json.loads(func_args_str) if func_args_str else {}

                    # Execute the tool
                    if func_name in tools_dict:
                        # Call function directly with parameter validation
                        function_to_call = tools_dict[func_name]

                        # Create Pydantic model and validate parameters
                        params_model = scout.create_pydantic(function_to_call)
                        validated_parameters = params_model.model_validate(func_args)
                        parameters = {
                            k: v for k, v in validated_parameters.__dict__.items()
                        }

                        # Call the function with validated parameters
                        tool_result = function_to_call(**parameters)
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
                    conversation_messages.append(tool_response)

                except Exception as e:
                    # Add error message for failed tool call
                    error_response = ConversationMessage(
                        role=MessageRole.TOOL,
                        content=f"Error executing tool '{func_name}': {str(e)}",
                        tool_call_id=tool_call.id,
                    )
                    conversation_messages.append(error_response)

            iteration += 1

        # If we hit max iterations, return the last response
        if iteration >= max_tool_iterations:
            raise Exception(f"Maximum tool iterations ({max_tool_iterations}) exceeded")

        # This shouldn't be reached, but just in case
        return ChatCompletionResponse(messages=conversation_messages)

    def _completion_with_tools_streaming(
        self,
        messages: list[ConversationMessage] | str,
        tools: list[Callable],
        response_format: Optional[Type[ChatCompletionResponseType]] = None,
        allowed_tools: Optional[list[str]] = None,
        model: Optional[str] = None,
        assistant_id: Optional[str] = None,
        debug: Optional[bool] = False,
        llm_args: Optional[dict] = None,
        max_tool_iterations: int = 5,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Internal method for handling streaming tool calling functionality.
        Returns a generator that yields streaming chunks.
        """
        # Convert tools to OpenAI tool format
        _, tool_definitions = self._convert_tools_to_openai_format(tools)

        # Prepare conversation history
        if isinstance(messages, str):
            conversation_messages = [
                ConversationMessage(role=MessageRole.USER, content=messages)
            ]
        else:
            conversation_messages = messages.copy()

        # Prepare llm_args with tools
        final_llm_args = llm_args.copy() if llm_args else {}

        final_llm_args["tools"] = tool_definitions

        # Create request payload
        request_payload = ChatCompletionRequest(
            messages=conversation_messages,
            model=model,
            assistant_id=assistant_id,
            stream=True,
            allowed_tools=allowed_tools,
            llm_args=final_llm_args,
            response_format=response_format.model_json_schema()
            if response_format
            else None,
        )

        # Create and use streaming wrapper
        wrapper = StreamingToolCallWrapper(
            chat_api=self,
            conversation_messages=conversation_messages,
            tools=tools,
            model=model,
            assistant_id=assistant_id,
            debug=debug,
            llm_args=final_llm_args,
            max_tool_iterations=max_tool_iterations,
        )

        yield from wrapper.stream_with_tools(request_payload)
