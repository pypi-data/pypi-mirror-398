from typing import Optional, Union, overload, Literal, Callable
from scouttypes.images import (
    ImageRequest,
    ImageResponse,
    ImageAspectRatio,
    ImageQuality,
    ImageBackground,
)
from scouttypes.api import AsyncJobResponse
from .request_utils import RequestUtils


class ImageAPI:
    def __init__(self, base_url: str, headers: dict, retry_strategy: Callable) -> None:
        self._base_url = base_url
        self._headers = headers
        self._retry_strategy = retry_strategy

    def get_models(self, tags: Optional[list[str]] = None) -> list[dict]:
        """
        Get available image generation models that support specified tags.

        Args:
            tags (Optional[list[str]]): List of model tags to filter by. Defaults to None.

        Returns:
            list[dict]: List of available image models.
        """
        params = {}
        if tags:
            params["tags"] = tags

        response, _ = RequestUtils.get(
            url=f"{self._base_url}/api/image/models",
            headers=self._headers,
            params=params,
            retry_strategy=self._retry_strategy,
        )

        return response

    @overload
    def generate(
        self,
        prompt: str,
        aspect_ratio: Optional[ImageAspectRatio] = None,
        model: Optional[str] = None,
        quality: Optional[ImageQuality] = None,
        background: Optional[ImageBackground] = None,
        nb_outputs: Optional[int] = None,
        conversation_id: Optional[str] = None,
        async_job: Literal[True] = True,
    ) -> AsyncJobResponse: ...

    @overload
    def generate(
        self,
        prompt: str,
        aspect_ratio: Optional[ImageAspectRatio] = None,
        model: Optional[str] = None,
        quality: Optional[ImageQuality] = None,
        background: Optional[ImageBackground] = None,
        nb_outputs: Optional[int] = None,
        conversation_id: Optional[str] = None,
        async_job: Literal[False] = False,
    ) -> ImageResponse: ...

    def generate(
        self,
        prompt: str,
        aspect_ratio: Optional[ImageAspectRatio] = None,
        model: Optional[str] = None,
        quality: Optional[ImageQuality] = None,
        background: Optional[ImageBackground] = None,
        nb_outputs: Optional[int] = None,
        conversation_id: Optional[str] = None,
        async_job: bool = True,
    ) -> Union[ImageResponse, AsyncJobResponse]:
        """
        Generate image(s) using the Scout API.

        Args:
            prompt (str): The text prompt describing the image to generate.
            aspect_ratio (Optional[ImageAspectRatio]): Image aspect ratio ('square', 'landscape', 'portrait').
            model (Optional[str]): The image generation model to use.
            quality (Optional[ImageQuality]): Image quality ('low', 'medium', 'high', 'default').
            background (Optional[ImageBackground]): Background type ('opaque', 'transparent').
            nb_outputs (Optional[int]): Number of images to generate.
            conversation_id (Optional[str]): Conversation ID to associate with the generation.
            async_job (bool): Whether to execute asynchronously. Defaults to True.

        Returns:
            Union[ImageResponse, AsyncJobResponse]: The generation response from the API.
            Returns AsyncJobResponse when async_job=True, ImageResponse when async_job=False.

        Raises:
            Exception: If there's an error during the generation process.
        """
        request_data = ImageRequest(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            model=model,
            quality=quality,
            background=background,
            nb_outputs=nb_outputs,
        )

        json_payload = request_data.model_dump(exclude_none=True)
        json_payload["async_job"] = async_job
        if conversation_id:
            json_payload["conversation_id"] = conversation_id

        response, _ = RequestUtils.post(
            url=f"{self._base_url}/api/image/generate",
            headers=self._headers,
            json_payload=json_payload,
            retry_strategy=self._retry_strategy,
        )

        try:
            if async_job:
                return AsyncJobResponse.model_validate(response)
            else:
                return ImageResponse.model_validate(response)
        except Exception as e:
            raise Exception(
                f"Error processing image generation {e}. response: {response}"
            ) from e

    @overload
    def edit(
        self,
        prompt: str,
        images: list[dict],
        mask: Optional[dict] = None,
        aspect_ratio: Optional[ImageAspectRatio] = None,
        model: Optional[str] = None,
        quality: Optional[ImageQuality] = None,
        background: Optional[ImageBackground] = None,
        nb_outputs: Optional[int] = None,
        conversation_id: Optional[str] = None,
        async_job: Literal[True] = True,
    ) -> AsyncJobResponse: ...

    @overload
    def edit(
        self,
        prompt: str,
        images: list[dict],
        mask: Optional[dict] = None,
        aspect_ratio: Optional[ImageAspectRatio] = None,
        model: Optional[str] = None,
        quality: Optional[ImageQuality] = None,
        background: Optional[ImageBackground] = None,
        nb_outputs: Optional[int] = None,
        conversation_id: Optional[str] = None,
        async_job: Literal[False] = False,
    ) -> ImageResponse: ...

    def edit(
        self,
        prompt: str,
        images: list[dict],
        mask: Optional[dict] = None,
        aspect_ratio: Optional[ImageAspectRatio] = None,
        model: Optional[str] = None,
        quality: Optional[ImageQuality] = None,
        background: Optional[ImageBackground] = None,
        nb_outputs: Optional[int] = None,
        conversation_id: Optional[str] = None,
        async_job: bool = True,
    ) -> Union[ImageResponse, AsyncJobResponse]:
        """
        Edit existing image(s) using the Scout API.

        Args:
            prompt (str): The text prompt describing the desired edits.
            images (list[dict]): List of image objects with filename, content_type, and base64/protected_url.
            mask (Optional[dict]): Optional mask image object for targeted editing.
            aspect_ratio (Optional[ImageAspectRatio]): Image aspect ratio ('square', 'landscape', 'portrait').
            model (Optional[str]): The image generation model to use.
            quality (Optional[ImageQuality]): Image quality ('low', 'medium', 'high', 'default').
            background (Optional[ImageBackground]): Background type ('opaque', 'transparent').
            nb_outputs (Optional[int]): Number of images to generate.
            conversation_id (Optional[str]): Conversation ID to associate with the edit.
            async_job (bool): Whether to execute asynchronously. Defaults to True.

        Returns:
            Union[ImageResponse, AsyncJobResponse]: The edit response from the API.
            Returns AsyncJobResponse when async_job=True, ImageResponse when async_job=False.

        Raises:
            Exception: If there's an error during the editing process.
        """
        request_data = ImageRequest(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            model=model,
            quality=quality,
            background=background,
            nb_outputs=nb_outputs,
        )

        json_payload = request_data.model_dump(exclude_none=True)
        json_payload["async_job"] = async_job
        json_payload["images"] = images
        if mask:
            json_payload["mask"] = mask
        if conversation_id:
            json_payload["conversation_id"] = conversation_id

        response, _ = RequestUtils.post(
            url=f"{self._base_url}/api/image/edit",
            headers=self._headers,
            json_payload=json_payload,
            retry_strategy=self._retry_strategy,
        )

        try:
            if async_job:
                return AsyncJobResponse.model_validate(response)
            else:
                return ImageResponse.model_validate(response)
        except Exception as e:
            raise Exception(
                f"Error processing image edit {e}. response: {response}"
            ) from e
