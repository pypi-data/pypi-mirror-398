from typing import Optional, Type, Any, overload, TypeVar, Callable
from pydantic import BaseModel
import json
import requests

from .request_utils import RequestUtils
from scouttypes.conversations import SignedUploadUrlResponse
from scouttypes.protected import SignedUrlResponse
from scouttypes.upload_files import upload_file


class UtilsAPI:
    def __init__(self, base_url: str, headers: dict, retry_strategy: Callable) -> None:
        self._base_url = base_url
        self._headers = headers
        self._retry_strategy = retry_strategy

    def chunk_document(self, file_path: str) -> dict:
        """
        Chunk a document into smaller parts for embedding using default Scout chunk algorythm.

        Args:
            file_path (str): The local file path of the document to be chunked.

        Returns:
            dict: The response from the API after chunking the document. {"file": {"chunks": [{chunk_to_embed}]}}
        """
        with open(file_path, "rb") as f:
            files = {"file": f}
            local_headers = self._headers.copy()
            local_headers.pop("Content-Type")

            response, status_code = RequestUtils.post(
                url=f"{self._base_url}/api/utils/chunk-document",
                headers=local_headers,
                files=files,
                retry_strategy=self._retry_strategy,
            )
        return response

    def get_document_text(self, file_path: str, args: Optional[dict] = None) -> dict:
        """
        Extract text content from a file.

        Args:
            file_path (str): The local file path of the file to extract text from.
            args (Optional[dict], optional): Additional arguments for text extraction. Defaults to None.

        Returns:
            dict: The response from the API after extracting text from the file.
        """
        with open(file_path, "rb") as f:
            files = {"file": f}
            local_headers = self._headers.copy()
            local_headers.pop("Content-Type")

            response, status_code = RequestUtils.post(
                url=f"{self._base_url}/api/utils/get-file-text-content",
                headers=local_headers,
                files=files,
                json_payload=args,
                retry_strategy=self._retry_strategy,
            )
        return response

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

        Args:
            query (str): The query string to use for filtering documents. Ex: What is the capital of France?
            context (str): Additional context to provide to the LLM during filtering. Ex: You are an expert in selecting content to answer geographical questions.
            documents (dict[str, str]): A dictionary mapping document IDs to document texts. EX: {"my_id": "Capital of france is paris", "my_id_2": "Irrelevant content"}
            batch_size (int, optional): Number of documents to process in each batch. Defaults to 10.
            model_id (Optional[str], optional): The ID of the LLM model to use for filtering. When not provided, use default model.

        Returns:
            list: List of ids that are relevant result to answer the question
        """
        response, status_code = RequestUtils.post(
            url=f"{self._base_url}/api/utils/llm-filter-documents",
            headers=self._headers,
            json_payload={
                "query": query,
                "context": context,
                "documents": documents,
                "batch_size": batch_size,
                "model_id": model_id,
            },
            retry_strategy=self._retry_strategy,
        )
        return response

    def create_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Create embeddings for a list of text strings.

        Args:
            texts (list[str]): List of text strings to create embeddings for.

        Returns:
            list[list[float]]: List of embedding vectors, where each vector is a list of floats.
        """
        response, status_code = RequestUtils.post(
            url=f"{self._base_url}/api/embeddings/",
            headers=self._headers,
            json_payload={"texts": texts},
            retry_strategy=self._retry_strategy,
        )

        return response

    def download_protected_file(self, protected_url: str) -> bytes:
        """
        Download a file from a protected URL by first getting a signed URL and then downloading.

        Args:
            protected_url (str): The protected URL path (e.g., "/protected/conversations/123/audio.mp3").

        Returns:
            bytes: The file content as bytes.

        Raises:
            Exception: If there's an error getting the signed URL or downloading the file.
        """

        response, status_code = RequestUtils.get(
            url=f"{self._base_url}/api{protected_url}",
            headers=self._headers,
            retry_strategy=self._retry_strategy,
        )

        signed_url_response = SignedUrlResponse.model_validate(response)

        download_response = requests.get(signed_url_response.url)

        try:
            download_response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error_message = "HTTP Error occurred while downloading file"
            if e.response is not None:
                try:
                    error_details = e.response.json()
                    error_message = f"Download Error: {error_details}"
                except (ValueError, AttributeError):
                    error_message = f"Download Error: HTTP {e.response.status_code} - {e.response.text or 'No response text'}"
            else:
                error_message = f"Download Error: {str(e)}"
            raise Exception(error_message) from e

        return download_response.content


def upload_file_to_signed_url(
    signed_url_response: SignedUploadUrlResponse,
    file_path: str,
    file_key: str | None = None,
) -> int:
    """
    Upload a file to a signed URL provided by the Scout API.

    Args:
        signed_url_response (SignedUploadUrlResponse): The response object containing the signed URL and upload details.
        file_path (str): The local path to the file to be uploaded.
        file_key (str | None, optional): The key/name to use for the file in the upload. If None, uses the filename from file_path.

    Returns:
        int: The HTTP status code of the upload response.
    """
    if file_key is None:
        file_key = file_path.split("/")[-1]

    return upload_file(signed_url_response, file_path, file_key)


DataValidationResponseType = TypeVar("DataValidationResponseType", bound=BaseModel)


@overload
def get_validated_data(
    response: str | dict[str, Any], response_model: Type[DataValidationResponseType]
) -> DataValidationResponseType: ...


@overload
def get_validated_data(
    response: str | dict[str, Any], response_model: None = None
) -> dict[str, Any] | str: ...


def get_validated_data(
    response: str | dict[str, Any],
    response_model: Optional[Type[DataValidationResponseType]] = None,
) -> DataValidationResponseType | dict[str, Any] | str:
    if isinstance(response, str):
        try:
            validated_response = json.loads(response)
        except json.JSONDecodeError:
            validated_response = response
    else:
        validated_response = response

    if response_model:
        return response_model.model_validate(validated_response)
    return validated_response
