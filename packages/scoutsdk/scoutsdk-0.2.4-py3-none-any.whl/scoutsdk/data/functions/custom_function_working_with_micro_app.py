import os
from typing import Literal, Optional
from pydantic import BaseModel, Field
import requests
from scoutsdk import scout, ScoutAPI
from scouttypes.conversations import SignedUploadUrlResponse
from scoutsdk.api import upload_file_to_signed_url


class MyExampleUserData(BaseModel):
    step: Literal[
        "idle",
        "preparing",
        "starting",
        "done",
    ]
    error_logs: Optional[str] = None
    input_filename: Optional[str] = None
    input_protected_file_path: Optional[str] = None
    output_filename: Optional[str] = None
    output_protected_file_path: Optional[str] = None


class DismissedResponse(BaseModel):
    pass


def update_user_data(
    scout_api: ScoutAPI, conversation_id: str, user_data: MyExampleUserData
):
    scout_api.post(
        url=f"/api/conversations/{conversation_id}/user_data",
        data=user_data.model_dump(),
        response_model=DismissedResponse,
    )


class SignedUrlResponse(BaseModel):
    url: str


@scout.async_function(description="Do something with the input file")
def custom_function_working_with_micro_app(
    input_protected_file_url: str = Field(
        description="The protected URL of the input file"
    ),
    input_original_filename: str = Field(description="The filename of the input file"),
):
    try:
        scout_api = ScoutAPI()

        conversation_id = scout.context.get("SCOUT_CONVERSATION_ID")
        last_step = "preparing"

        signed_file_url_response = scout_api.get(
            url=f"/api{input_protected_file_url}",
            params=None,
            response_model=SignedUrlResponse,
        )

        local_input_filename = os.path.basename(input_protected_file_url)
        with open(local_input_filename, "wb") as f:
            f.write(requests.get(signed_file_url_response.data.url).content)

        last_step = "starting"
        update_user_data(
            scout_api,
            conversation_id,
            MyExampleUserData(
                step=last_step,
                input_filename=input_original_filename,
                input_protected_file_path=input_protected_file_url,
            ),
        )

        output_signed_upload_url_response: SignedUploadUrlResponse = (
            scout_api.conversations.get_signed_upload_url(
                conversation_id=conversation_id,
                file_path="output.csv",
            )
        )

        with open("output.csv", "w") as f:
            f.write("Hello, World!")

        status_code = upload_file_to_signed_url(
            output_signed_upload_url_response,
            "output.csv",
        )

        if status_code >= 400:
            raise Exception(f"Upload failed with status code: {status_code}")

        last_step = "done"
        user_data = MyExampleUserData(
            step=last_step,
            input_protected_file_path=input_protected_file_url,
            input_filename=input_original_filename,
            output_protected_file_path=output_signed_upload_url_response.protected_url,
            output_filename="output.csv",
        )

        update_user_data(scout_api, conversation_id, user_data)

        return "success, check user_data"
    except Exception as e:
        update_user_data(
            scout_api,
            conversation_id,
            MyExampleUserData(
                step=last_step,
                error_logs=str(e),
                input_protected_file_path=input_protected_file_url,
                input_filename=input_original_filename,
            ),
        )
        raise e
