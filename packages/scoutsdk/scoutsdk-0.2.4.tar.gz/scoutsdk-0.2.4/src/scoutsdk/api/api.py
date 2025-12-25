from __future__ import annotations
from typing import Optional, Any, Type, Generic, cast, TypeVar
from pydantic import BaseModel

from .request_utils import RequestUtils
from .retry_config import RetryConfig, create_retry_strategy, retry_on_api_errors
from scouttypes.constants import VariableNames
from scouttypes.chat import (
    ChatCompletionResponse,
)
from scouttypes.conversations import (
    ConversationMessage,
    ConversationMessageContentPartTextParam,
    ConversationMessageContentPartImageParam,
    ConversationMessageContentPartPDFParam,
    MessageRole,
    ConversationResponse,
)
from scouttypes.assistants import (
    AssistantUploadImageResponse as AssistantUploadImageResponseType,
    AssistantFileUploadResponse as AssistantFileUploadResponseType,
    AssistantFile as AssistantFileType,
    AssistantResponse as AssistantResponseType,
    AssistantData as AssistantDataType,
    AssistantDataList as AssistantDataListType,
)
from scouttypes.conversations import (
    SignedUploadUrlResponse as SignedUploadUrlResponseType,
)
from scouttypes.protected import (
    SignedUrlResponse as SignedUrlResponseType,
)
from .project_helpers import scout

from .chat import ChatAPI
from .assistants import AssistantsAPI
from .conversations import ConversationsAPI
from .utils import UtilsAPI, get_validated_data
from .audio import AudioAPI
from .image import ImageAPI
from .protected import ProtectedAPI
from .skills import SkillsAPI
from .deprecated import deprecated, deprecated_class

# Import deprecated types
from ..shared.assistants_types import (
    AssistantUploadImageResponse,
    AssistantFileUploadResponse,
    AssistantFile,
)
from ..shared.conversations_types import SignedUploadUrlResponse, UploadMode
from ..shared.protected_types import SignedUrlResponse
from .types.chat import (
    ChatCompletionMessage,
    ChatCompletionMessageTextContent,
    ChatCompletionMessageImageContent,
    ChatCompletionMessagePDFContent,
)
from .types.assistants import (
    AssistantResponse,
)


# Create generic type variables for request and response
RequestType = TypeVar("RequestType", bound=BaseModel)
ResponseType = TypeVar("ResponseType", bound=BaseModel)
ResponseFormatType = TypeVar("ResponseFormatType", bound=BaseModel)


class Response(Generic[ResponseType]):
    def __init__(self, status_code: int, data: ResponseType):
        self.status_code = status_code
        self.data = data


@deprecated_class(
    version="0.1.42",
    reason="Use the AssistantData class from the scoutypes.assistants module instead",
    removal_version="0.2.0",
)
class AssistantData(BaseModel):
    metadata: dict
    content: str
    embedding: Optional[list] = None


@deprecated_class(
    version="0.1.42",
    reason="Use the AssistantDataList class from the scoutypes.assistants module instead",
    removal_version="0.2.0",
)
class AssistantDataList(BaseModel):
    list: list[AssistantData]


class ScoutAPI:
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_access_token: Optional[str] = None,
        retry_config: Optional[RetryConfig] = None,
    ) -> None:
        self._base_url = base_url or scout.context.get(VariableNames.SCOUT_API_URL)
        if self._base_url is None or self._base_url == "":
            raise ValueError(
                f"{VariableNames.SCOUT_API_URL} is not set in SCOUT_CONTEXT"
            )

        api_access_token = api_access_token or scout.context.get(
            VariableNames.SCOUT_API_ACCESS_TOKEN
        )
        if api_access_token is None or api_access_token == "":
            raise ValueError(
                f"{VariableNames.SCOUT_API_ACCESS_TOKEN} is not set in SCOUT_CONTEXT"
            )

        self._headers = {
            "Authorization": f"Bearer {api_access_token}",
            "Content-Type": "application/json",
        }

        # Create retry strategy from config or use default
        if retry_config is not None:
            # Empty dict means no retries
            if not retry_config:
                self._retry_strategy = create_retry_strategy(max_attempts=0)
            else:
                self._retry_strategy = create_retry_strategy(**retry_config)
        else:
            self._retry_strategy = retry_on_api_errors

        # Initialize specialized API clients
        self.chat = ChatAPI(self._base_url, self._headers, self._retry_strategy)
        self.assistants = AssistantsAPI(
            self._base_url, self._headers, self._retry_strategy
        )
        self.conversations = ConversationsAPI(
            self._base_url, self._headers, self._retry_strategy
        )
        self.utils = UtilsAPI(self._base_url, self._headers, self._retry_strategy)
        self.audio = AudioAPI(self._base_url, self._headers, self._retry_strategy)
        self.image = ImageAPI(self._base_url, self._headers, self._retry_strategy)
        self.protected = ProtectedAPI(
            self._base_url, self._headers, self._retry_strategy
        )
        self.skills = SkillsAPI(self._base_url, self._headers, self._retry_strategy)

    # Generic requests
    def get(
        self,
        url: str,
        params: RequestType,
        response_model: Optional[Type[ResponseType]] = None,
    ) -> Response[Any]:
        """Make a GET request to the Scout API.

        Args:
            url: The endpoint URL to make the request to (will be appended to base_url).
            params: Request parameters to include in the query string. Can be a BaseModel
                instance or a dictionary.
            response_model: Optional response model class to validate and deserialize
                the response data.

        Returns:
            Response: A Response object containing the status code and validated data.

        Raises:
            ValueError: If the request parameters are invalid.
            RequestException: If the HTTP request fails.
        """
        request_data = params.model_dump() if isinstance(params, BaseModel) else params

        response, status_code = RequestUtils.get(
            url=f"{self._base_url}{url}",
            headers=self._headers,
            params=request_data,
            retry_strategy=self._retry_strategy,
        )

        validated_data = get_validated_data(response, response_model)

        return Response(status_code=status_code, data=validated_data)

    def put(
        self,
        url: str,
        data: RequestType,
        response_model: Optional[Type[ResponseType]] = None,
    ) -> Response[Any]:
        """Make a PUT request to the Scout API.

        Args:
            url: The endpoint URL to make the request to (will be appended to base_url).
            data: Request data to include in the request body. Can be a BaseModel
                instance or a dictionary.
            response_model: Optional response model class to validate and deserialize
                the response data.

        Returns:
            Response: A Response object containing the status code and validated data.

        Raises:
            ValueError: If the request data is invalid.
            RequestException: If the HTTP request fails.
        """
        request_data = data.model_dump() if isinstance(data, BaseModel) else data

        response, status_code = RequestUtils.put(
            url=f"{self._base_url}{url}",
            headers=self._headers,
            payload=request_data,
            retry_strategy=self._retry_strategy,
        )

        validated_data = get_validated_data(response, response_model)

        return Response(status_code=status_code, data=validated_data)

    def post(
        self,
        url: str,
        data: RequestType | dict,
        response_model: Optional[Type[ResponseType]] = None,
        files: Optional[dict] = None,
    ) -> Response[Any]:
        """Make a POST request to the Scout API.

        Args:
            url: The endpoint URL to make the request to (will be appended to base_url).
            data: Request data to include in the request body. Can be a BaseModel
                instance or a dictionary.
            response_model: Optional response model class to validate and deserialize
                the response data.
            files: Optional dictionary of files to upload with the request.

        Returns:
            Response: A Response object containing the status code and validated data.

        Raises:
            ValueError: If the request data is invalid.
            RequestException: If the HTTP request fails.
        """
        request_data = data.model_dump() if isinstance(data, BaseModel) else data

        if files:
            local_headers = self._headers.copy()
            local_headers.pop("Content-Type")

            response, status_code = RequestUtils.post(
                url=f"{self._base_url}{url}",
                headers=local_headers,
                data=request_data,
                files=files,
                retry_strategy=self._retry_strategy,
            )
        else:
            response, status_code = RequestUtils.post(
                url=f"{self._base_url}{url}",
                headers=self._headers,
                json_payload=request_data,
                retry_strategy=self._retry_strategy,
            )

        validated_data = get_validated_data(response, response_model)

        return Response(status_code=status_code, data=validated_data)

    def delete(
        self, url: str, response_model: Optional[Type[ResponseType]] = None
    ) -> Response[Any]:
        """Make a DELETE request to the Scout API.

        Args:
            url: The endpoint URL to make the request to (will be appended to base_url).
            response_model: Optional response model class to validate and deserialize
                the response data.

        Returns:
            Response: A Response object containing the status code and validated data.

        Raises:
            ValueError: If the request parameters are invalid.
            RequestException: If the HTTP request fails.
        """
        response, status_code = RequestUtils.delete(
            url=f"{self._base_url}{url}",
            headers=self._headers,
            retry_strategy=self._retry_strategy,
        )

        validated_data = get_validated_data(response, response_model)

        return Response(status_code=status_code, data=validated_data)

    @deprecated(
        reason="Use utils.create_embeddings() instead.",
        version="0.1.42",
        removal_version="0.2.0",
    )
    def create_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Create embeddings for a list of text strings.

        .. deprecated:: Use `utils.create_embeddings()` instead.

        Args:
            texts (list[str]): List of text strings to create embeddings for.

        Returns:
            list[list[float]]: List of embedding vectors, where each vector is a list of floats.
        """
        return self.utils.create_embeddings(texts)

    @deprecated(
        version="0.1.42",
        reason="Use chat.completion() instead.",
        removal_version="0.2.0",
    )
    def chat_completion(
        self,
        messages: list[ChatCompletionMessage] | str,
        model: Optional[str] = None,
        assistant_id: Optional[str] = None,
        stream: Optional[bool] = None,
        response_format: Optional[Type[ResponseType]] = None,
        debug: Optional[bool] = False,
        allowed_tools: Optional[list[str]] = None,
        llm_args: Optional[dict] = None,
    ) -> Any:
        """
        Send a chat completion request to the Scout API.

        .. deprecated:: Use `chat.completion()` instead.

        Args:
            messages (list[ChatCompletionMessage] | str): The list of chat messages or a single user message string.
            model (Optional[str]): The model to use for completion (default: first available model).
            assistant_id (Optional[str]): The assistant ID to use for the request.
            stream (Optional[bool]): Whether to stream the response (default: False).
            response_format (Optional[Type[ResponseType]]): Pydantic model to use for response validation.
            debug (Optional[bool]): If True, print the payload for debugging.
            allowed_tools (Optional[list[str]]): List of allowed tools for the assistant. None = Use all available tools, Empty list = No tools.
            llm_args (Optional[dict]): Additional arguments to pass to the LLM API.

        Returns:
            Any: The response from the Scout API. If response_format is provided, returns a validated response model.

        Raises:
            Exception: If there is an error processing the response, especially when response_format is used.
        """
        converted_messages: str | list[ConversationMessage]
        if isinstance(messages, str):
            converted_messages = messages
        else:
            converted_messages = []
            for message in messages:
                converted_content: Any = None
                if isinstance(message.content, list):
                    converted_content = []
                    for content in message.content:
                        if isinstance(content, ChatCompletionMessageTextContent):
                            converted_content.append(
                                ConversationMessageContentPartTextParam(
                                    text=content.text
                                )
                            )
                        elif isinstance(content, ChatCompletionMessageImageContent):
                            converted_content.append(
                                ConversationMessageContentPartImageParam(
                                    data=content.data,
                                    content_type=content.content_type,
                                    filename=content.filename,
                                )
                            )
                        elif isinstance(content, ChatCompletionMessagePDFContent):
                            converted_content.append(
                                ConversationMessageContentPartPDFParam(
                                    data=content.data,
                                    filename=content.filename,
                                )
                            )
                        elif isinstance(content, dict):
                            converted_content.append(content)
                        else:
                            raise ValueError(
                                f"Unsupported content type: {type(content)}"
                            )
                elif isinstance(message.content, str):
                    converted_content = message.content

                converted_messages.append(
                    ConversationMessage(
                        role=MessageRole(message.role),
                        content=converted_content,
                    )
                )

        chat_completion_response = self.chat.completion(
            messages=converted_messages,
            response_format=response_format,
            model=model,
            assistant_id=assistant_id,
            stream=stream or False,
            debug=debug,
            allowed_tools=allowed_tools,
            llm_args=llm_args,
        )
        return (
            chat_completion_response.messages[-1].model_dump()
            if isinstance(chat_completion_response, ChatCompletionResponse)
            and chat_completion_response.messages
            else chat_completion_response
        )

    # Assistants

    @deprecated(
        version="0.1.42",
        reason="Use assistants.create() instead",
        removal_version="0.2.0",
    )
    def create_assistant(
        self,
        name: str,
        description: str,
        instructions: str,
        use_system_prompt: bool = True,
        prompt_starters: Optional[list[str]] = None,
        visibility_type: str = "private",
        avatar_url: Optional[str] = None,
        allowed_functions: Optional[list[str]] = None,
        variables: Optional[dict[str, str]] = None,
        secrets: Optional[dict[str, str]] = None,
        allowed_external_services: Optional[list[str]] = None,
        ui_url: Optional[str] = None,
    ) -> Any:
        """
        Create a new assistant in the Scout API.

        .. deprecated:: Use `assistants.create()` instead.

        Args:
            name (str): The name of the assistant.
            description (str): A brief description of the assistant.
            instructions (str): Instructions or system prompt for the assistant.
            use_system_prompt (bool, optional): Whether to use the system prompt of the scout instance.
            prompt_starters (Optional[list[str]], optional): List of prompt starters for the assistant. Defaults to None.
            visibility_type (str, optional): Visibility type for the assistant (e.g., "private", "public"). Defaults to "private".
            avatar_url (Optional[str], optional): URL to the assistant's avatar image. Defaults to None.
            allowed_functions (Optional[list[str]], optional): List of allowed function names. None = Use all available tools, Empty list = No tools.
            variables (Optional[dict[str, str]], optional): Variables to include with the assistant. Defaults to None.
            secrets (Optional[dict[str, str]], optional): Secrets to include with the assistant. Defaults to None.
            allowed_external_services (Optional[list[str]], optional): List of allowed external services. None = Use all available tools, Empty list = No tools.
            ui_url (Optional[str], optional): URL for the assistant's UI. Defaults to None.

        Returns:
            Any: The response from the Scout API after creating the assistant.
        """
        return self.assistants.create(
            name=name,
            description=description,
            instructions=instructions,
            use_system_prompt=use_system_prompt,
            prompt_starters=prompt_starters,
            visibility_type=visibility_type,
            avatar_url=avatar_url,
            allowed_functions=allowed_functions,
            variables=variables,
            secrets=secrets,
            allowed_external_services=allowed_external_services,
            ui_url=ui_url,
        )

    @deprecated(
        version="0.1.42",
        reason="Use assistants.update() instead",
        removal_version="0.2.0",
    )
    def update_assistant(
        self,
        assistant_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        instructions: Optional[str] = None,
        use_system_prompt: Optional[bool] = None,
        prompt_starters: Optional[list[str]] = None,
        visibility_type: Optional[str] = None,
        avatar_url: Optional[str] = None,
        ui_url: Optional[str] = None,
        links: Optional[list[str]] = None,
        allowed_functions: Optional[list[str]] = None,
        variables: Optional[dict[str, str]] = None,
        secrets: Optional[dict[str, Optional[str]]] = None,
        allowed_external_services: Optional[list[str]] = None,
    ) -> Any:
        """
        .. deprecated:: Use `assistants.update()` instead.
        """
        return self.assistants.update(
            assistant_id=assistant_id,
            name=name,
            description=description,
            instructions=instructions,
            use_system_prompt=use_system_prompt,
            prompt_starters=prompt_starters,
            visibility_type=visibility_type,
            avatar_url=avatar_url,
            ui_url=ui_url,
            links=links,
            allowed_functions=allowed_functions,
            variables=variables,
            secrets=secrets,
            allowed_external_services=allowed_external_services,
        )

    @deprecated(
        version="0.1.42",
        reason="Use assistants.get_all() instead",
        removal_version="0.2.0",
    )
    def get_assistants(self) -> list:
        """
        Retrieve a list of all assistants the token has access to.

        .. deprecated:: Use `assistants.get_all()` instead.

        Returns:
            list: A list of assistant objects retrieved from the API.
        """
        assistants = self.assistants.list_all()
        return [assistant.model_dump() for assistant in assistants]

    @deprecated(
        version="0.1.42",
        reason="Use assistants.upload_avatar() instead",
        removal_version="0.2.0",
    )
    def upload_assistant_avatar(
        self,
        assistant_id: str,
        file_path: str,
    ) -> AssistantUploadImageResponse:
        """Upload an avatar image for a specific assistant.

        .. deprecated:: Use `assistants.upload_avatar()` instead.

        Args:
            assistant_id (str): The ID of the assistant to upload the avatar for.
            file_path (str): The local file path to the avatar image.

        Returns:
            AssistantUploadImageResponse: The response object containing information about the uploaded avatar.

        Raises:
            Exception: If there is an error during the file upload process.
        """
        upload_response: AssistantUploadImageResponseType = (
            self.assistants.upload_avatar(
                assistant_id=assistant_id,
                file_path=file_path,
            )
        )

        return AssistantUploadImageResponse(
            content_type=upload_response.content_type,
            protected_url=upload_response.protected_url,
        )

    @deprecated(
        version="0.1.42",
        reason="Use assistants.upload_file() instead",
        removal_version="0.2.0",
    )
    def upload_assistant_file(
        self,
        assistant_id: str,
        file_path: str,
    ) -> AssistantFileUploadResponse:
        """Upload a file to the knowledge section of a specific assistant.

        .. deprecated:: Use `assistants.upload_file()` instead.

        Args:
            assistant_id (str): The ID of the assistant to upload the file for.
            file_path (str): The local file path to the file to upload.

        Returns:
            AssistantFileUploadResponse: The response object containing information about the uploaded file.

        Raises:
            Exception: If there is an error during the file upload process.
        """
        upload_response: AssistantFileUploadResponseType = self.assistants.upload_file(
            assistant_id=assistant_id,
            file_path=file_path,
        )

        return AssistantFileUploadResponse(
            message=upload_response.message,
            file_id=upload_response.file_id,
            assistant_id=upload_response.assistant_id,
        )

    @deprecated(
        version="0.1.42",
        reason="Use assistants.list_files() instead",
        removal_version="0.2.0",
    )
    def list_assistant_files(
        self,
        assistant_id: str,
    ) -> list[AssistantFile]:
        """Retrieve a list of files associated with a specific assistant.

        .. deprecated:: Use `assistants.list_files()` instead.

        Args:
            assistant_id (str): The ID of the assistant whose files are to be listed.

        Returns:
            list[AssistantFile]: A list of AssistantFile objects representing the files associated with the assistant.
        """
        files: list[AssistantFileType] = self.assistants.list_files(
            assistant_id=assistant_id,
        )
        return [
            AssistantFile(
                id=file.id,
                filename=file.filename,
                description=file.description,
                status=file.status,
            )
            for file in files
        ]

    @deprecated(
        version="0.1.42",
        reason="Use assistants.edit_file() instead",
        removal_version="0.2.0",
    )
    def edit_assistant_file(
        self,
        assistant_id: str,
        file_uid: str,
        filename: str = "Default",
        description: Optional[str] = None,
    ) -> Any:
        """
        Edit the metadata of a file associated with a specific assistant.

        .. deprecated:: Use `assistants.edit_file()` instead.

        Args:
            assistant_id (str): The ID of the assistant.
            file_uid (str): The unique identifier of the file to edit.
            filename (str, optional): The new name for the file. Defaults to "Default".
            description (Optional[str], optional): The new description for the file. Defaults to None.

        Returns:
            Any: The response from the Scout API after updating the file information.
        """
        return self.assistants.edit_file(
            assistant_id=assistant_id,
            file_uid=file_uid,
            filename=filename,
            description=description,
        )

    @deprecated(
        version="0.1.42",
        reason="Use assistants.delete_file() instead",
        removal_version="0.2.0",
    )
    def delete_assistant_file(
        self,
        assistant_id: str,
        file_uid: str,
    ) -> AssistantResponse:
        """Delete a file associated with a specific assistant.

        .. deprecated:: Use `assistants.delete_file()` instead.

        Args:
            assistant_id (str): The ID of the assistant.
            file_uid (str): The unique identifier of the file to delete.

        Returns:
            AssistantResponse: The response object after deleting the assistant's file.
        """
        delete_response: AssistantResponseType = self.assistants.delete_file(
            assistant_id=assistant_id,
            file_uid=file_uid,
        )

        return AssistantResponse(
            message=delete_response.message,
            assistant_id=delete_response.assistant_id,
        )

    # Conversations

    @deprecated(
        version="0.1.42",
        reason="Use conversations.create() instead",
        removal_version="0.2.0",
    )
    def create_conversation(
        self,
        assistant_id: Optional[str] = None,
        model: Optional[str] = None,
        title: Optional[str] = None,
        payload: Optional[dict[str, Any]] = None,
        time_zone_offset: str = "-0400",
    ) -> Any:
        """
        Create a new conversation.

        .. deprecated:: Use `conversations.create()` instead.

        Args:
            assistant_id (Optional[str]): The ID of the assistant to associate with the conversation. If None, creates a generic conversation.
            model (Optional[str]): The model to use for the conversation. If None, uses the default model.
            title (Optional[str]): Title of the conversation. If None, no title is set.
            time_zone_offset (str, optional): Time zone offset for the conversation. Defaults to "-0400".
            payload (Optional[dict[str, Any]]): Additional payload data for the conversation.

        Returns:
            Any: The response from the Scout API after creating the conversation.
        """
        converted_payload: list[ConversationMessage] = []
        if payload is not None:
            converted_payload = [ConversationMessage.model_validate(payload)]

        conversation_response: ConversationResponse = self.conversations.create(
            messages=converted_payload,
            assistant_id=assistant_id,
            model=model,
            title=title,
            time_zone_offset=time_zone_offset,
        )
        return conversation_response.model_dump()

    @deprecated(
        version="0.1.42",
        reason="Use assistants.search_data() instead",
        removal_version="0.2.0",
    )
    def search_assistant_data(
        self,
        assistant_id: str,
        query: str,
        strategy: Optional[dict] = None,
        where: Optional[dict] = None,
    ) -> list:
        """
        Search the assistant's data with a given query.

        .. deprecated:: Use `assistants.search_data()` instead.

        Args:
            assistant_id (str): The ID of the assistant whose data is to be searched.
            query (str): The search query string.
            strategy (Optional[dict], optional): The search strategy to use. Defaults to None.
            where (Optional[dict], optional): Additional filtering criteria. Defaults to None. Ex: {"field": "value"}

        Returns:
            list: A list of search results from the assistant's data.
        """
        return self.assistants.search_data(
            assistant_id=assistant_id,
            query=query,
            strategy=strategy,
            where=where,
        )

    @deprecated(
        version="0.1.42",
        reason="Use assistants.create_data() instead",
        removal_version="0.2.0",
    )
    def create_assistant_data(
        self, assistant_id: str, data: AssistantData | AssistantDataList
    ) -> Any:
        """Create new data entries for a specific assistant.

        .. deprecated:: Use `assistants.create_data()` instead.

        Args:
            assistant_id (str): The ID of the assistant to which the data will be added.
            data (AssistantData | AssistantDataList): A single AssistantData instance or an AssistantDataList containing multiple entries.

        Returns:
            Any: The response from the API after creating the data.
        """
        converted_data: AssistantDataType | AssistantDataListType
        if isinstance(data, AssistantData):
            converted_data = AssistantDataType(
                metadata=data.metadata, content=data.content, embedding=data.embedding
            )
        else:
            data_list = [
                AssistantDataType(
                    metadata=item.metadata,
                    content=item.content,
                    embedding=item.embedding,
                )
                for item in data.list
            ]
            converted_data = AssistantDataListType(list=data_list)

        self.assistants.create_data(
            assistant_id=assistant_id,
            data=converted_data,
        )
        return AssistantResponse(
            message="data created successfully",
            assistant_id=assistant_id,
        )

    @deprecated(
        version="0.1.42",
        reason="Use assistants.update_data() instead",
        removal_version="0.2.0",
    )
    def update_assistant_data(
        self,
        assistant_id: str,
        data_id: str,
        metadata: dict,
        content: str,
        embedding: Optional[list] = None,
    ) -> Any:
        """Update an existing data entry for a specific assistant.

        .. deprecated:: Use `assistants.update_data()` instead.

        Args:
            assistant_id (str): The ID of the assistant.
            data_id (str): The ID of the data entry to update.
            metadata (dict): Updated metadata for the data entry.
            content (str): Updated content for the data entry.
            embedding (Optional[list], optional): Updated embedding for the data entry. Defaults to None.

        Returns:
            Any: The response from the API after updating the data.
        """
        return self.assistants.update_data(
            assistant_id=assistant_id,
            data_id=data_id,
            metadata=metadata,
            content=content,
            embedding=embedding,
        )

    @deprecated(
        version="0.1.42",
        reason="Use assistants.query_data() instead",
        removal_version="0.2.0",
    )
    def query_assistant_data(self, assistant_id: str, where: dict) -> list:
        """
        Query assistant data matching specific criteria.

        .. deprecated:: Use `assistants.query_data()` instead.

        Args:
            assistant_id (str): The ID of the assistant whose data will be queried.
            where (dict): Dictionary specifying query filters. Ex: {"field": "search_value"}

        Returns:
            list: A list of data entries matching the query.
        """
        return self.assistants.query_data(
            assistant_id=assistant_id,
            where=where,
        )

    @deprecated(
        version="0.1.42",
        reason="Use assistants.delete_data() instead",
        removal_version="0.2.0",
    )
    def delete_assistant_data(
        self, assistant_id: str, id: Optional[str] = None, where: Optional[dict] = None
    ) -> Any:
        """Delete assistant data by ID or matching criteria.

        .. deprecated:: Use `assistants.delete_data()` instead.

        Args:
            assistant_id (str): The ID of the assistant.
            id (Optional[str], optional): The ID of the data entry to delete. Defaults to None.
            where (Optional[dict], optional): Criteria to match data entries for deletion. Defaults to None.

        Raises:
            ValueError: If neither 'id' nor 'where' is provided.

        Returns:
            Any: The response from the API after deleting the data.
        """
        return self.assistants.delete_data(
            assistant_id=assistant_id,
            id=id,
            where=where,
        )

    @deprecated(
        version="0.1.42",
        reason="Use conversations.get_signed_upload_url() instead",
        removal_version="0.2.0",
    )
    def get_conversation_signed_upload_url(
        self,
        conversation_id: str,
        file_path: str,
    ) -> SignedUploadUrlResponse:
        """Generate a signed upload URL for uploading a file to a specific conversation.

        .. deprecated:: Use `conversations.get_signed_upload_url()` instead.

        Args:
            conversation_id (str): The ID of the conversation to associate the file with.
            file_path (str): The local file path of the file to be uploaded.

        Returns:
            SignedUploadUrlResponse: The response object containing the signed upload URL.

        Raises:
            ValueError: If the response is invalid or cannot be validated.
        """
        signed_upload_url_response: SignedUploadUrlResponseType = (
            self.conversations.get_signed_upload_url(
                conversation_id=conversation_id,
                file_path=file_path,
            )
        )
        return SignedUploadUrlResponse(
            url=signed_upload_url_response.url,
            fields=signed_upload_url_response.fields,
            prefix=signed_upload_url_response.prefix,
            protected_url=signed_upload_url_response.protected_url,
            upload_mode=cast(
                UploadMode,
                signed_upload_url_response.upload_mode,
            ),
            content_type=signed_upload_url_response.content_type,
        )

    @deprecated(
        version="0.1.42",
        reason="Use utils.get_signed_url() instead",
        removal_version="0.2.0",
    )
    def get_signed_url(
        self,
        path: str,
    ) -> SignedUrlResponse:
        """
        Generate a signed URL for accessing a protected resource.

        .. deprecated:: Use `utils.get_signed_url()` instead.

        Args:
            path (str): The relative path to the protected resource.

        Returns:
            SignedUrlResponse: The response object containing the signed URL for the resource.
        """
        response, status_code = RequestUtils.get(
            url=f"{self._base_url}/api/protected/{path}",
            headers=self._headers,
            retry_strategy=self._retry_strategy,
        )

        return SignedUrlResponse.model_validate(response)

    @deprecated(
        version="0.1.42",
        reason="Use conversations.get_signed_url() instead",
        removal_version="0.2.0",
    )
    def get_conversation_signed_url(
        self,
        conversation_id: str,
        file_path: str,
    ) -> SignedUrlResponse:
        """Generate a signed URL for accessing a file associated with a specific conversation.

        .. deprecated:: Use `conversations.get_signed_url()` instead.

        Args:
            conversation_id (str): The ID of the conversation.
            file_path (str): The relative path of the file within the conversation.

        Returns:
            SignedUrlResponse: The response object containing the signed URL for the file.
        """
        signed_url_response: SignedUrlResponseType = self.conversations.get_signed_url(
            conversation_id=conversation_id,
            file_path=file_path,
        )
        return SignedUrlResponse(
            url=signed_url_response.url,
        )

    @deprecated(
        version="0.1.42",
        reason="Use utils.chunk_document() instead",
        removal_version="0.2.0",
    )
    def chunk_document(self, file_path: str) -> dict:
        """
        Chunk a document into smaller parts for embedding using default Scout chunk algorythm.

        .. deprecated:: Use `utils.chunk_document()` instead.

        Args:
            file_path (str): The local file path of the document to be chunked.

        Returns:
            dict: The response from the API after chunking the document. {"file": {"chunks": [{chunk_to_embed}]}}
        """
        return self.utils.chunk_document(
            file_path=file_path,
        )

    @deprecated(
        version="0.1.42",
        reason="Use utils.get_document_text() instead",
        removal_version="0.2.0",
    )
    def get_document_text(self, file_path: str, args: Optional[dict] = None) -> dict:
        """Extract text content from a file.

        .. deprecated:: Use `utils.get_document_text()` instead.

        Args:
            file_path (str): The local file path of the file to extract text from.
            args (Optional[dict], optional): Additional arguments for text extraction. Defaults to None.

        Returns:
            dict: The response from the API after extracting text from the file.
        """
        return self.utils.get_document_text(
            file_path=file_path,
            args=args,
        )

    @deprecated(
        version="0.1.42",
        reason="Use utils.llm_filter_documents() instead",
        removal_version="0.2.0",
    )
    def llm_filter_documents(
        self,
        query: str,
        context: str,
        documents: dict[str, str],
        batch_size: int = 10,
        model_id: Optional[str] = None,
    ) -> list:
        """
        Filter a set of documents using an LLM based on a query and context.

        .. deprecated:: Use `utils.llm_filter_documents()` instead.

        Args:
            query (str): The query string to use for filtering documents. Ex: What is the capital of France?
            context (str): Additional context to provide to the LLM during filtering. Ex: You are an expert in selecting content to answer geographical questions.
            documents (dict[str, str]): A dictionary mapping document IDs to document texts. EX: {"my_id": "Capital of france is paris", "my_id_2": "Irrelevant content"}
            batch_size (int, optional): Number of documents to process in each batch. Defaults to 10.
            model_id (Optional[str], optional): The ID of the LLM model to use for filtering. When not provided, use default model.

        Returns:
            list: List of ids that are relevant result to answer the question
        """
        return self.utils.llm_filter_documents(
            query=query,
            context=context,
            documents=documents,
            batch_size=batch_size,
            model_id=model_id,
        )

    @deprecated(
        version="0.1.42",
        reason="Use audio.text_to_speech() instead",
        removal_version="0.2.0",
    )
    def text_to_speech(
        self,
        text: str,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        api_args: Optional[dict] = None,
    ) -> bytes:
        """Convert input text to speech audio using a specified model and voice.

        .. deprecated:: Use `audio.text_to_speech()` instead.

        Args:
            text (str): The text to be converted to speech.
            model (Optional[str], optional): The speech synthesis model to use. Defaults to None.
            voice (Optional[str], optional): The voice profile to use for speech. Defaults to None.
            api_args (Optional[dict], optional): Additional API arguments for customization. Defaults to None.

        Returns:
            bytes: The audio content generated from the text.
        """
        return self.audio.text_to_speech(
            text=text,
            model=model,
            voice=voice,
            api_args=api_args,
        )

    @deprecated(
        version="0.1.42",
        reason="Use assistants.execute_function() instead",
        removal_version="0.2.0",
    )
    def execute_assistant_function(
        self,
        assistant_id: str,
        function_name: str,
        payload: dict,
        response_model: Type[ResponseType],
    ) -> Response[ResponseType]:
        """Execute a specific function for an assistant and return the response.

         .. deprecated:: Use `assistants.execute_function()` instead.

        Args:
            assistant_id (str): The ID of the assistant.
            function_name (str): The name of the function to execute.
            payload (dict): The payload (parameters) to send to the function.
            response_model (Type[ResponseType]): The expected response model type for validation.

        Returns:
            Response[ResponseType]: The response from the API, validated against the provided response model.
        """
        actual_response = self.assistants.execute_function(
            assistant_id=assistant_id,
            function_name=function_name,
            payload=payload,
            response_model=response_model,
        )

        return Response(status_code=200, data=actual_response)
