from typing import Optional, Type, TypeVar, Callable
from pydantic import BaseModel

from .request_utils import RequestUtils
from scouttypes.conversations import (
    SignedUploadUrlResponse,
    CreateConversationRequest,
    ConversationResponse,
    DeleteConversationResponse,
)
from scouttypes.protected import SignedUrlResponse
from scouttypes.conversations import ConversationMessage

T = TypeVar("T", bound=BaseModel)


class ConversationsAPI:
    def __init__(self, base_url: str, headers: dict, retry_strategy: Callable) -> None:
        self._base_url = base_url
        self._headers = headers
        self._retry_strategy = retry_strategy

    def create(
        self,
        messages: Optional[list[ConversationMessage]] = None,
        assistant_id: Optional[str] = None,
        model: Optional[str] = None,
        title: Optional[str] = None,
        time_zone_offset: str = "-0400",
        user_data: Optional[dict] = None,
    ) -> ConversationResponse:
        """
        Create a new conversation.

        Args:
            messages (Optional[list[ConversationMessage]]): The list of messages to start the conversation with.
            time_zone_offset (str, optional): Time zone offset for the conversation. Defaults to "-0400".
            assistant_id (Optional[str]): The ID of the assistant to associate with the conversation. If None, creates a generic conversation.
            title (Optional[str]): Title of the conversation. If None, no title is set.
            model (Optional[str]): The model to use for the conversation. If None, uses the default model.
            user_data (Optional[dict]): Additional user data for the conversation.

        Returns:
            ConversationResponse: The response from the Scout API after creating the conversation.

        Raises:
            ValueError: If the response is invalid or cannot be validated.
        """

        request_payload = CreateConversationRequest(
            payload=messages or [],
            time_zone_offset=time_zone_offset,
            assistant_id=assistant_id,
            title=title,
            model=model,
            user_data=user_data,
        )

        response, status_code = RequestUtils.post(
            url=f"{self._base_url}/api/conversations/",
            headers=self._headers,
            json_payload=request_payload.model_dump(exclude_none=True),
            retry_strategy=self._retry_strategy,
        )
        return ConversationResponse.model_validate(response)

    def delete(self, conversation_id: str) -> DeleteConversationResponse:
        """
        Delete a conversation.

        Args:
            conversation_id (str): The ID of the conversation to delete.

        Returns:
            DeleteConversationResponse: The response containing the ID of the deleted conversation.

        Raises:
            ValueError: If the response is invalid or cannot be validated.
        """
        response, status_code = RequestUtils.delete(
            url=f"{self._base_url}/api/conversations/{conversation_id}",
            headers=self._headers,
            retry_strategy=self._retry_strategy,
        )
        return DeleteConversationResponse(id=response)

    def get_signed_upload_url(
        self,
        conversation_id: str,
        file_path: str,
    ) -> SignedUploadUrlResponse:
        """
        Generate a signed upload URL for uploading a file to a specific conversation.

        Args:
            conversation_id (str): The ID of the conversation to associate the file with.
            file_path (str): The local file path of the file to be uploaded.

        Returns:
            SignedUploadUrlResponse: The response object containing the signed upload URL.

        Raises:
            ValueError: If the response is invalid or cannot be validated.
        """
        payload = {"file_path": file_path}

        response, status_code = RequestUtils.post(
            url=f"{self._base_url}/api/conversations/{conversation_id}/signed-upload-url",
            headers=self._headers,
            json_payload=payload,
            retry_strategy=self._retry_strategy,
        )
        try:
            return SignedUploadUrlResponse.model_validate(response)
        except Exception as e:
            raise ValueError(f"Invalid response: {response}") from e

    def get_signed_url(
        self,
        conversation_id: str,
        file_path: str,
    ) -> SignedUrlResponse:
        """
        Generate a signed URL for accessing a file associated with a specific conversation.

        Args:
            conversation_id (str): The ID of the conversation.
            file_path (str): The relative path of the file within the conversation.

        Returns:
            SignedUrlResponse: The response object containing the signed URL for the file.

        Raises:
            ValueError: If the response is invalid or cannot be validated.
        """
        response, status_code = RequestUtils.get(
            url=f"{self._base_url}/api/protected/conversations/{conversation_id}/{file_path}",
            headers=self._headers,
            retry_strategy=self._retry_strategy,
        )

        return SignedUrlResponse.model_validate(response)

    def get_user_data(
        self,
        conversation_id: str,
        model_class: Optional[Type[T]] = None,
    ) -> T | dict:
        """
        Get user data for a specific conversation.

        Args:
            conversation_id (str): The ID of the conversation.
            model_class (Optional[Type[T]]): Pydantic model class to validate the user data.
                If None, returns raw dict.

        Returns:
            T | dict: The user data, optionally validated with the provided model class.

        Raises:
            ValueError: If the response is invalid or cannot be validated.
        """
        response, status_code = RequestUtils.get(
            url=f"{self._base_url}/api/conversations/{conversation_id}",
            headers=self._headers,
            retry_strategy=self._retry_strategy,
        )

        conversation_response = ConversationResponse.model_validate(response)
        user_data = conversation_response.user_data or {}

        if model_class:
            return model_class.model_validate(user_data)
        return user_data

    def update_user_data(
        self,
        conversation_id: str,
        user_data: BaseModel | dict,
    ) -> ConversationResponse:
        """
        Update user data for a specific conversation.

        Args:
            conversation_id (str): The ID of the conversation.
            user_data (BaseModel | dict): The user data to update.

        Returns:
            ConversationResponse: The updated conversation response from the API.

        Raises:
            ValueError: If the response is invalid or cannot be validated.
        """
        request_data = (
            user_data.model_dump() if isinstance(user_data, BaseModel) else user_data
        )

        response, status_code = RequestUtils.post(
            url=f"{self._base_url}/api/conversations/{conversation_id}/user_data",
            headers=self._headers,
            json_payload=request_data,
            retry_strategy=self._retry_strategy,
        )

        return ConversationResponse.model_validate(response)
