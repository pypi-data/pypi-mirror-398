import json
import requests
from typing import Any, Optional, Tuple, Callable

from .retry_config import retry_on_api_errors


class RequestUtils:
    @staticmethod
    def post(
        url: str,
        headers: dict,
        json_payload: Optional[dict] = None,
        data: Optional[dict] = None,
        files: Optional[dict] = None,
        stream: bool = False,
        params: Optional[dict] = None,
        retry_strategy: Callable = retry_on_api_errors,
    ) -> Tuple[Any, int]:
        if files is not None and json_payload is not None:
            data = {"json_payload": json.dumps(json_payload)}
            json_payload = None

        @retry_strategy
        def _make_request() -> requests.Response:
            response = requests.post(
                url=url,
                headers=headers,
                files=files,
                json=json_payload,
                data=data,
                params=params,
            )
            response.raise_for_status()
            return response

        return RequestUtils._process_request(_make_request, stream=stream)

    @staticmethod
    def put(
        url: str,
        headers: dict,
        payload: Optional[dict] = None,
        retry_strategy: Callable = retry_on_api_errors,
    ) -> Tuple[Any, int]:
        @retry_strategy
        def _make_request() -> requests.Response:
            response = requests.put(url=url, headers=headers, json=payload)
            response.raise_for_status()
            return response

        return RequestUtils._process_request(_make_request)

    @staticmethod
    def get(
        url: str,
        headers: dict,
        stream: bool = False,
        params: Optional[dict] = None,
        retry_strategy: Callable = retry_on_api_errors,
    ) -> Tuple[Any, int]:
        @retry_strategy
        def _make_request() -> requests.Response:
            response = requests.get(url=url, headers=headers, params=params)
            response.raise_for_status()
            return response

        return RequestUtils._process_request(_make_request, stream=stream)

    @staticmethod
    def delete(
        url: str,
        headers: dict,
        json_payload: Optional[dict] = None,
        retry_strategy: Callable = retry_on_api_errors,
    ) -> Tuple[Any, int]:
        @retry_strategy
        def _make_request() -> requests.Response:
            response = requests.delete(url=url, headers=headers, json=json_payload)
            response.raise_for_status()
            return response

        return RequestUtils._process_request(_make_request)

    @staticmethod
    def patch(
        url: str,
        headers: dict,
        json_payload: Optional[dict] = None,
        retry_strategy: Callable = retry_on_api_errors,
    ) -> Tuple[Any, int]:
        @retry_strategy
        def _make_request() -> requests.Response:
            response = requests.patch(url=url, headers=headers, json=json_payload)
            response.raise_for_status()
            return response

        return RequestUtils._process_request(_make_request)

    @staticmethod
    def _process_request(
        make_request_fn: Callable[[], requests.Response],
        stream: bool = False,
    ) -> Tuple[Any, int]:
        try:
            response = make_request_fn()

            RequestUtils._check_for_error_response(response)
            if stream:
                return (
                    RequestUtils._handle_stream_response(response=response),
                    response.status_code,
                )
            else:
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return (response.json(), response.status_code)
                elif "text/" in content_type:
                    return (response.text, response.status_code)
                else:
                    return (response.content, response.status_code)
        except requests.exceptions.HTTPError as e:
            response_content = e.response.content.decode("utf-8")
            error_message = f"{str(e)}\n{response_content}"
            new_error = type(e)(error_message)
            new_error.response = e.response
            raise new_error from e
        except Exception as e:
            error_message = f"{str(e)}"
            raise type(e)(error_message) from e

    @staticmethod
    def _handle_stream_response(
        response: requests.Response,
    ) -> Any:
        accumulated_current_data = ""
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

                received_stream_chunks = [
                    json.loads(f"{chunk}")
                    for chunk in chunks
                    if chunk and chunk.strip() != ":"
                ]

                # only return the last chunk if the stream is finished
                for received_chunk in received_stream_chunks:
                    if received_chunk.get("finish_reason"):
                        return received_chunk

        return {}

    @staticmethod
    def consume_stream_generator(stream_generator: Any) -> Any:
        """
        Consume a generator of parsed stream chunks and return the final chunk with finish_reason.

        This follows the same pattern as _handle_stream_response but works with
        already-parsed chunks (e.g., from tool streaming).

        Args:
            stream_generator: Generator yielding parsed dict chunks

        Returns:
            The last chunk with a finish_reason, or empty dict if none found
        """
        final_chunk = None
        for chunk in stream_generator:
            if chunk.get("finish_reason"):
                final_chunk = chunk

        return final_chunk if final_chunk is not None else {}

    @staticmethod
    def _check_for_error_response(response: requests.Response) -> None:
        response.raise_for_status()
        # look for the error in the response
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type or "text/event-stream" in content_type:
            try:
                response_json = response.json()
                if isinstance(response_json, dict):
                    # Check for an 'error' key with a truthy value
                    error_content = response_json.get("error")
                    if error_content:
                        raise Exception(f"API error in JSON response: {error_content}")
            except requests.exceptions.JSONDecodeError:
                if "application/json" in content_type:
                    raise Exception(f"API error in JSON response: {response}")
