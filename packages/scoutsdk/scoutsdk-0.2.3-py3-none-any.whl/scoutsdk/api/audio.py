from typing import Optional, Union, overload, Literal, Callable
import os
import base64

import requests
from scouttypes.audio import (
    AudioTranscriptionResponse,
    AudioTranscriptionRequest,
    AudioObject,
)
from scouttypes.api import AsyncJobResponse


class AudioAPI:
    def __init__(self, base_url: str, headers: dict, retry_strategy: Callable) -> None:
        self._base_url = base_url
        self._headers = headers
        self._retry_strategy = retry_strategy

    def text_to_speech(
        self,
        text: str,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        api_args: Optional[dict] = None,
    ) -> bytes:
        """
        Convert input text to speech audio using a specified model and voice.

        Args:
            text (str): The text to be converted to speech.
            model (Optional[str], optional): The speech synthesis model to use. Defaults to None.
            voice (Optional[str], optional): The voice profile to use for speech. Defaults to None.
            api_args (Optional[dict], optional): Additional API arguments for customization. Defaults to None.

        Returns:
            bytes: The audio content generated from the text.
        """
        json_payload = {
            "text": text,
            **({"model": model} if model is not None else {}),
            **({"voice": voice} if voice is not None else {}),
            **({"api_args": api_args} if api_args is not None else {}),
        }

        response = requests.post(
            url=f"{self._base_url}/api/audio/speech",
            headers=self._headers,
            json=json_payload,
        )
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error_message = "HTTP Error occurred"
            if e.response is not None:
                try:
                    error_details = e.response.json()
                    error_message = f"Error: {error_details}"
                except (ValueError, AttributeError):
                    # Handle cases where response is not valid JSON
                    error_message = f"Error: HTTP {e.response.status_code} - {e.response.text or 'No response text'}"
            else:
                # Handle cases where e.response is None
                error_message = f"Error: {str(e)}"

            raise Exception(error_message) from e

        return response.content

    @overload
    def transcribe_file(
        self,
        file_path: str,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
        execute_async: Literal[True] = True,
        model_args: Optional[dict] = None,
    ) -> AsyncJobResponse: ...

    @overload
    def transcribe_file(
        self,
        file_path: str,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
        execute_async: Literal[False] = False,
        model_args: Optional[dict] = None,
    ) -> AudioTranscriptionResponse: ...

    def transcribe_file(
        self,
        file_path: str,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
        execute_async: bool = True,
        model_args: Optional[dict] = None,
    ) -> Union[AudioTranscriptionResponse, AsyncJobResponse]:
        """
        Transcribe an audio file using the Scout API.

        Args:
            file_path (str): The local path to the audio file to transcribe.
            conversation_id (Optional[str]): The conversation ID to associate with the transcription.
            model (Optional[str]): The transcription model to use.
            execute_async (bool): Whether to execute the transcription asynchronously. Defaults to True.
            model_args (Optional[dict]): Additional model arguments.

        Returns:
            Union[AudioTranscriptionResponse, AsyncJobResponse]: The transcription response from the API.
            Returns AsyncJobResponse when execute_async=True, AudioTranscriptionResponse when execute_async=False.

        Raises:
            FileNotFoundError: If the specified audio file doesn't exist.
            Exception: If there's an error during the transcription process.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        filename = os.path.basename(file_path)

        # Read file and encode to base64
        with open(file_path, "rb") as f:
            file_bytes = f.read()
            base64_encoded = base64.b64encode(file_bytes).decode("utf-8")

        # Create the request data with base64 encoded audio
        audio_object = AudioObject(filename=filename, base64=base64_encoded)

        return self._send_transcription_request(
            audio_object=audio_object,
            conversation_id=conversation_id,
            model=model,
            execute_async=execute_async,
            model_args=model_args,
        )

    @overload
    def transcribe_url(
        self,
        protected_url: str,
        filename: Optional[str] = None,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
        execute_async: Literal[True] = True,
        model_args: Optional[dict] = None,
    ) -> AsyncJobResponse: ...

    @overload
    def transcribe_url(
        self,
        protected_url: str,
        filename: Optional[str] = None,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
        execute_async: Literal[False] = False,
        model_args: Optional[dict] = None,
    ) -> AudioTranscriptionResponse: ...

    def transcribe_url(
        self,
        protected_url: str,
        filename: Optional[str] = None,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
        execute_async: bool = True,
        model_args: Optional[dict] = None,
    ) -> Union[AudioTranscriptionResponse, AsyncJobResponse]:
        """
        Transcribe an audio file from a protected URL using the Scout API.

        Args:
            protected_url (str): The protected URL path to the audio file.
            filename (Optional[str]): The filename to use. If None, extracted from URL.
            conversation_id (Optional[str]): The conversation ID to associate with the transcription.
            model (Optional[str]): The transcription model to use.
            execute_async (bool): Whether to execute the transcription asynchronously. Defaults to True.
            model_args (Optional[dict]): Additional model arguments.

        Returns:
            Union[AudioTranscriptionResponse, AsyncJobResponse]: The transcription response from the API.
            Returns AsyncJobResponse when execute_async=True, AudioTranscriptionResponse when execute_async=False.

        Raises:
            Exception: If there's an error during the transcription process.
        """
        # Extract filename from URL if not provided
        if filename is None:
            filename = protected_url.split("/")[-1] if "/" in protected_url else "audio"

        # Create the request data with protected URL
        audio_object = AudioObject(filename=filename, protected_url=protected_url)

        return self._send_transcription_request(
            audio_object=audio_object,
            conversation_id=conversation_id,
            model=model,
            execute_async=execute_async,
            model_args=model_args,
        )

    def _send_transcription_request(
        self,
        audio_object: AudioObject,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
        execute_async: bool = True,
        model_args: Optional[dict] = None,
    ) -> Union[AudioTranscriptionResponse, AsyncJobResponse]:
        """
        Internal method to send transcription request to the API.
        """
        request_data = AudioTranscriptionRequest(
            conversation_id=conversation_id,
            audio=audio_object,
            model=model,
            execute_async=execute_async,
            model_args=model_args,
        )

        # Send as JSON
        json_payload = request_data.model_dump(exclude_none=True)

        response = requests.post(
            url=f"{self._base_url}/api/audio/transcription",
            headers=self._headers,
            json=json_payload,
        )

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error_message = "HTTP Error occurred"
            if e.response is not None:
                try:
                    error_details = e.response.json()
                    error_message = f"Error: {error_details}"
                except (ValueError, AttributeError):
                    error_message = f"Error: HTTP {e.response.status_code} - {e.response.text or 'No response text'}"
            else:
                error_message = f"Error: {str(e)}"
            raise Exception(error_message) from e

        response_data = response.json()

        if execute_async:
            return AsyncJobResponse.model_validate(response_data)
        else:
            return AudioTranscriptionResponse.model_validate(response_data)
