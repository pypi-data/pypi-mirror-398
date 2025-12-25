from pydantic import Field
from scoutsdk.api import ScoutAPI
from scouttypes.assistants import AssistantPublicResponse
from scoutsdk import scout


@scout.function(description="Description of the function usage (Seen by the LLM)")
def this_is_a_test_function(
    # Parameter must be typed
    my_parameter: str = Field(description="Description of the field (Seen by the LLM)"),
):
    # For development, set SCOUT_API_URL and SCOUT_API_ACCESS_TOKEN in your environment variables or scout_context.json
    # When used by an assistant, URL and ACCESS_TOKEN are provided
    scout_api = ScoutAPI()
    assistants: list[AssistantPublicResponse] = (
        scout_api.assistants.list_all()
    )

    # To access configured assistant variables or secrets, use:
    # scout.context["VARIABLE_NAME"]

    return {"first_assistant": assistants[0].model_dump(), "parameter": my_parameter}
