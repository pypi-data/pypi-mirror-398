import requests
import mimetypes
from scouttypes.conversations import SignedUploadUrlResponse, UploadMode

__all__ = [
    "upload_file",
    "default_upload_file",
    "get_content_type",
    "azure_upload_file_from_signed_url",
]


def upload_file(
    signed_url_response: SignedUploadUrlResponse,
    file_path: str,
    file_key: str,
) -> int:
    if signed_url_response.upload_mode == UploadMode.AZURE:
        return azure_upload_file_from_signed_url(file_path, signed_url_response)

    return default_upload_file(file_path, file_key, signed_url_response.model_dump())


def default_upload_file(
    file: str, uploaded_file_key: str, signed_upload_dictionary: dict
) -> int:
    files_to_upload = [("file", (uploaded_file_key, open(file, "rb")))]
    data = signed_upload_dictionary["fields"]
    url = signed_upload_dictionary["url"]
    response = requests.post(url, files=files_to_upload, data=data)
    return response.status_code


# Note code mostly inspired by:
# https://github.com/rahulbagal/upload-file-azure-sas-url/blob/master/azure_sas_upload.py


def get_content_type(file_path: str, content_type: str = "") -> str:
    if content_type:
        return content_type

    file_content_type, _ = mimetypes.guess_type(file_path)
    return (
        file_content_type
        if file_content_type is not None
        else "application/octet-stream"
    )


def azure_upload_file_from_signed_url(
    file: str, signed_upload_url: SignedUploadUrlResponse
) -> int:
    return _put_blob(signed_upload_url.url, file, signed_upload_url.content_type)


def _put_blob(
    url: str,
    file_name_full_path: str,
    content_type: str,
) -> int:
    with open(file_name_full_path, "rb") as fh:
        response = requests.put(
            url,
            data=fh,
            headers={
                "content-type": content_type,
                "x-ms-blob-type": "BlockBlob",
            },
            params={"file": file_name_full_path},
        )
        return response.status_code
