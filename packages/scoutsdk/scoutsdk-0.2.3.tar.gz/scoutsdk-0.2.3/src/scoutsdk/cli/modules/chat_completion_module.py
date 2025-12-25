import argparse
import json
import logging
from .base_module import BaseModule
from ..config import Config, CONFIG_ASSISTANT_ID
from ..error_handler import ValidationError, APIError, logger
from ...api import ScoutAPI
from ...api.types.chat import ChatCompletionMessage
from typing import Optional


class ChatCompletionModule(BaseModule):
    def __init__(self, config: Config) -> None:
        """Initialize the chat completion module."""
        self.assistant_id = config.get(CONFIG_ASSISTANT_ID, None)

    def get_command(self) -> str:
        return "chat-completion"

    def add_parser(self, subparsers: argparse._SubParsersAction) -> None:
        completion_parser = subparsers.add_parser(
            self.get_command(), help="Send a message to the chat completion API"
        )
        completion_parser.add_argument(
            "-u", "--user-message", type=str, required=True, help="The message to send"
        )
        completion_parser.add_argument(
            "-s", "--system-prompt", type=str, help="Optional system prompt to use"
        )
        completion_parser.add_argument(
            "-m", "--model", type=str, help="The model to use for chat completion"
        )
        completion_parser.add_argument(
            "-str", "--stream", type=bool, default=False, help="Stream the response"
        )
        completion_parser.add_argument(
            "-a",
            "--assistant-id",
            type=str,
            help="The assistant ID to use for chat completion",
        )
        completion_parser.add_argument(
            "-r",
            "--raw",
            action="store_true",
            help="Display raw response",
        )

        completion_parser.set_defaults(func=self.execute)

    def execute(self, args: argparse.Namespace) -> None:
        """Execute the chat completion command."""

        # Validate required parameters
        assistant_id = self._get_assistant_id(args)
        if not assistant_id:
            raise ValidationError(
                "Assistant ID is required. Provide it with --assistant-id or set it in your environment."
            )

        messages: list[ChatCompletionMessage] = []
        system_prompt = self._get_system_prompt(args)
        if system_prompt:
            messages.append(
                ChatCompletionMessage(
                    role="system",
                    content=system_prompt,
                )
            )
        messages.append(ChatCompletionMessage(role="user", content=args.user_message))

        try:
            response = ScoutAPI().chat_completion(
                messages=messages,
                model=self._get_model(args),
                assistant_id=assistant_id,
                stream=self._get_stream(args),
            )
        except Exception as e:
            raise APIError(f"Failed to get chat completion: {str(e)}")

        # Print the response
        print("\nResponse:")
        if args.raw:
            print(json.dumps(response, indent=2))
        else:
            if "messages" in response and len(response["messages"]) > 0:
                print(response["messages"][0]["content"])
            else:
                logger.warning("Received an empty or invalid response")
                if logger.level <= logging.DEBUG:
                    logger.debug(f"Raw response: {json.dumps(response, indent=2)}")

    def _get_assistant_id(self, args: argparse.Namespace) -> Optional[str]:
        """Get the assistant ID from the arguments."""
        if args.assistant_id:
            return args.assistant_id
        return self.assistant_id

    def _get_model(self, args: argparse.Namespace) -> Optional[str]:
        """Get the model from the arguments."""
        if args.model:
            return args.model
        return None

    def _get_system_prompt(self, args: argparse.Namespace) -> Optional[str]:
        """Get the system prompt from the arguments."""
        if args.system_prompt:
            return args.system_prompt
        return None

    def _get_stream(self, args: argparse.Namespace) -> bool:
        """Get the stream from the arguments."""
        if args.stream:
            return args.stream
        return False
