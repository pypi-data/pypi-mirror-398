import mimetypes
from typing import Optional, Type, Any, overload, List, TypeVar, Callable
from pydantic import BaseModel
from .request_utils import RequestUtils
from scouttypes.assistants import (
    AssistantInfoResponse,
    AssistantPublicResponse,
    AssistantResponse,
    AssistantFileEditResponse,
    AssistantFile,
    AssistantFileUploadResponse,
    AssistantUploadImageResponse,
    AssistantSearchDataResponse,
    AssistantData,
    AssistantDataList,
    UpdateAssistantRequest,
    LinkRequest,
    AssistantDeleteResponse,
    DeleteAssistantDataResponse,
    AssistantDataResponseItem,
    QueryAssistantDataResponse,
    AssistantDataUpdateResponse,
    CreateAssistantDataResponse,
    AssistantCustomFunctionsResponse,
    FileType,
    SkillResponse,
    AssistantSkillResponse,
)
from .utils import get_validated_data
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .current_assistant import CurrentAssistant


class AssistantsAPI:
    def __init__(self, base_url: str, headers: dict, retry_strategy: Callable) -> None:
        self._base_url = base_url
        self._headers = headers
        self._retry_strategy = retry_strategy

    def create(
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
    ) -> AssistantInfoResponse:
        """
        Create a new assistant in the Scout API.

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
            AssistantResponse: The response from the Scout API after creating the assistant.
        """
        payload = {
            "name": name,
            "description": description,
            "instructions": instructions,
            "use_system_prompt": use_system_prompt,
            "prompt_starters": prompt_starters or [],
            "visibility": {"type": visibility_type},
            "avatar_url": avatar_url,
            **({"variables": variables} if variables is not None else {}),
            **({"secrets": secrets} if secrets is not None else {}),
            **(
                {"allowed_functions": allowed_functions}
                if allowed_functions is not None
                else {}
            ),
            **(
                {"allowed_external_services": allowed_external_services}
                if allowed_external_services is not None
                else {}
            ),
            **({"ui_url": ui_url} if ui_url is not None else {}),
        }

        response, status_code = RequestUtils.post(
            url=f"{self._base_url}/api/assistants/",
            headers=self._headers,
            json_payload=payload,
            retry_strategy=self._retry_strategy,
        )

        return AssistantInfoResponse.model_validate(response)

    def update(
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
        content_retrieving_strategy: Optional[dict] = None,
    ) -> AssistantInfoResponse:
        # Create the update request model

        links_request = [LinkRequest(url=link) for link in links] if links else None
        update_request = UpdateAssistantRequest(
            name=name,
            description=description,
            instructions=instructions,
            use_system_prompt=use_system_prompt,
            prompt_starters=prompt_starters,
            visibility={"type": visibility_type}
            if visibility_type is not None
            else None,
            avatar_url=avatar_url,
            ui_url=ui_url,
            links=links_request,
            allowed_functions=allowed_functions,
            variables=variables,
            secrets=secrets,
            allowed_external_services=allowed_external_services,
            content_retrieving_strategy=content_retrieving_strategy,
        )

        response, status_code = RequestUtils.patch(
            url=f"{self._base_url}/api/assistants/{assistant_id}",
            headers=self._headers,
            json_payload=update_request.model_dump(exclude_none=True),
            retry_strategy=self._retry_strategy,
        )

        return AssistantInfoResponse.model_validate(response)

    def get(self, assistant_id: str) -> AssistantInfoResponse:
        """
        Retrieve a specific assistant by its ID.

        Args:
            assistant_id (str): The ID of the assistant to retrieve.

        Returns:
            AssistantInfoResponse: The assistant object retrieved from the API.
        """
        response, status_code = RequestUtils.get(
            url=f"{self._base_url}/api/assistants/{assistant_id}",
            headers=self._headers,
            retry_strategy=self._retry_strategy,
        )

        return AssistantInfoResponse.model_validate(response)

    def get_public(self, assistant_id: str) -> AssistantPublicResponse:
        """
        Retrieve a public assistant by its ID.

        Args:
            assistant_id (str): The ID of the assistant to retrieve.

        Returns:
            AssistantPublicResponse: The public assistant object retrieved from the API.
        """
        response, status_code = RequestUtils.get(
            url=f"{self._base_url}/api/assistants/{assistant_id}/public",
            headers=self._headers,
            retry_strategy=self._retry_strategy,
        )

        return AssistantPublicResponse.model_validate(response)

    def list_all(self) -> List[AssistantPublicResponse]:
        """
        Retrieve a list of all assistants the token has access to.

        Returns:
            List[AssistantPublicResponse]: A list of assistant objects retrieved from the API.
        """
        response, status_code = RequestUtils.get(
            url=f"{self._base_url}/api/assistants",
            headers=self._headers,
            retry_strategy=self._retry_strategy,
        )

        return [
            AssistantPublicResponse.model_validate(assistant) for assistant in response
        ]

    def delete(self, assistant_id: str) -> AssistantDeleteResponse:
        """
        Delete an assistant.

        Args:
            assistant_id (str): The ID of the assistant to delete.

        Returns:
            AssistantDeleteResponse: The response from the Scout API after deleting the assistant.
        """
        response, status_code = RequestUtils.delete(
            url=f"{self._base_url}/api/assistants/{assistant_id}",
            headers=self._headers,
            retry_strategy=self._retry_strategy,
        )
        return AssistantDeleteResponse.model_validate(response)

    def upload_avatar(
        self,
        assistant_id: str,
        file_path: str,
    ) -> AssistantUploadImageResponse:
        """
        Upload an avatar image for a specific assistant.

        Args:
            assistant_id (str): The ID of the assistant to upload the avatar for.
            file_path (str): The local file path to the avatar image.

        Returns:
            AssistantUploadImageResponse: The response object containing information about the uploaded avatar.

        Raises:
            Exception: If there is an error during the file upload process.
        """
        with open(file_path, "rb") as f:
            content_type = mimetypes.guess_type(file_path)[0]
            files = {"file": (file_path, f, content_type)}
            local_headers = self._headers.copy()
            local_headers.pop("Content-Type")

            response, status_code = RequestUtils.post(
                url=f"{self._base_url}/api/assistants/{assistant_id}/avatar/upload",
                headers=local_headers,
                files=files,
                retry_strategy=self._retry_strategy,
            )
        return AssistantUploadImageResponse.model_validate(response)

    def upload_file(
        self,
        assistant_id: str,
        file_path: str,
        file_type: Optional[FileType] = None,
    ) -> AssistantFileUploadResponse:
        """
        Upload a file to a specific assistant.

        Args:
            assistant_id (str): The ID of the assistant to upload the file for.
            file_path (str): The local file path to the file to upload.
            file_type (Optional[FileType]): The type of file to upload. Defaults to FileType.KNOWLEDGE.
                Valid values: FileType.KNOWLEDGE, FileType.CUSTOM_FUNCTIONS, FileType.ASSISTANT_TEMPLATES, FileType.SHARED_CUSTOM_FUNCTIONS

        Returns:
            AssistantFileUploadResponse: The response object containing information about the uploaded file.

        Raises:
            Exception: If there is an error during the file upload process.
        """
        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {}
            if file_type is not None:
                data["file_type"] = file_type.value

            local_headers = self._headers.copy()
            local_headers.pop("Content-Type")

            response, status_code = RequestUtils.post(
                url=f"{self._base_url}/api/assistants/{assistant_id}/files",
                headers=local_headers,
                files=files,
                data=data,
                retry_strategy=self._retry_strategy,
            )
        return AssistantFileUploadResponse.model_validate(response)

    def list_files(
        self,
        assistant_id: str,
    ) -> list[AssistantFile]:
        """
        Retrieve a list of files associated with a specific assistant.

        Args:
            assistant_id (str): The ID of the assistant whose files are to be listed.

        Returns:
            list[AssistantFile]: A list of AssistantFile objects representing the files associated with the assistant.
        """
        response, status_code = RequestUtils.get(
            url=f"{self._base_url}/api/assistants/{assistant_id}/files",
            headers=self._headers,
            retry_strategy=self._retry_strategy,
        )
        return [AssistantFile.model_validate(file) for file in response]

    def edit_file(
        self,
        assistant_id: str,
        file_uid: str,
        filename: str = "Default",
        description: Optional[str] = None,
    ) -> AssistantFileEditResponse:
        """
        Edit the metadata of a file associated with a specific assistant.

        Args:
            assistant_id (str): The ID of the assistant.
            file_uid (str): The unique identifier of the file to edit.
            filename (str, optional): The new name for the file. Defaults to "Default".
            description (Optional[str], optional): The new description for the file. Defaults to None.

        Returns:
            AssistantFileEditResponse: The response from the Scout API after updating the file information.
        """
        data = {}
        data.update({"file_name": filename})
        data.update({"file_description": description}) if description else None
        response, status_code = RequestUtils.put(
            url=f"{self._base_url}/api/assistants/{assistant_id}/files/{file_uid}",
            headers=self._headers,
            payload=data,
            retry_strategy=self._retry_strategy,
        )
        return AssistantFileEditResponse.model_validate(response)

    def delete_file(
        self,
        assistant_id: str,
        file_uid: str,
    ) -> AssistantResponse:
        """
        Delete a file associated with a specific assistant.

        Args:
            assistant_id (str): The ID of the assistant.
            file_uid (str): The unique identifier of the file to delete.

        Returns:
            AssistantResponse: The response object after deleting the assistant's file.
        """
        response, status_code = RequestUtils.delete(
            url=f"{self._base_url}/api/assistants/{assistant_id}/files/{file_uid}",
            headers=self._headers,
            retry_strategy=self._retry_strategy,
        )
        return AssistantResponse.model_validate(response)

    def search_data(
        self,
        assistant_id: str,
        query: str,
        strategy: Optional[dict] = None,
        where: Optional[dict] = None,
    ) -> list[AssistantSearchDataResponse]:
        """
        Search the assistant's data with a given query.

        Args:
            assistant_id (str): The ID of the assistant whose data is to be searched.
            query (str): The search query string.
            strategy (Optional[dict], optional): The search strategy to use. Defaults to None.
            where (Optional[dict], optional): Additional filtering criteria. Defaults to None. Ex: {"field": "value"}

        Returns:
            list: A list of search results from the assistant's data.
        """
        response, status_code = RequestUtils.post(
            url=f"{self._base_url}/api/assistants/{assistant_id}/search",
            headers=self._headers,
            json_payload={"query": query, "strategy": strategy, "where": where},
            retry_strategy=self._retry_strategy,
        )
        return [AssistantSearchDataResponse.model_validate(item) for item in response]

    def create_data(
        self, assistant_id: str, data: AssistantData | AssistantDataList
    ) -> CreateAssistantDataResponse:
        """
        Create new data entries for a specific assistant.

        Args:
            assistant_id (str): The ID of the assistant to which the data will be added.
            data (AssistantData | AssistantDataList): A single AssistantData instance or an AssistantDataList containing multiple entries.

        Returns:
            CreateAssistantDataResponse: Response containing created item IDs.
        """
        data_list = (
            data.model_dump().get("list")
            if isinstance(data, AssistantDataList)
            else [data.model_dump()]
        )

        response, status_code = RequestUtils.post(
            url=f"{self._base_url}/api/assistants/{assistant_id}/data",
            headers=self._headers,
            json_payload={"data": data_list},
            retry_strategy=self._retry_strategy,
        )
        return CreateAssistantDataResponse.model_validate(response)

    def update_data(
        self,
        assistant_id: str,
        data_id: str,
        metadata: dict,
        content: str,
        embedding: Optional[list] = None,
    ) -> AssistantDataUpdateResponse:
        """
        Update an existing data entry for a specific assistant.

        Args:
            assistant_id (str): The ID of the assistant.
            data_id (str): The ID of the data entry to update.
            metadata (dict): Updated metadata for the data entry.
            content (str): Updated content for the data entry.
            embedding (Optional[list], optional): Updated embedding for the data entry. Defaults to None.

        Returns:
            AssistantDataMessageResponse: The response from the API after updating the data.
        """
        response, status_code = RequestUtils.put(
            url=f"{self._base_url}/api/assistants/{assistant_id}/data/{data_id}",
            headers=self._headers,
            payload={"metadata": metadata, "content": content, "embedding": embedding},
            retry_strategy=self._retry_strategy,
        )
        return AssistantDataUpdateResponse.model_validate(response)

    def query_data(
        self, assistant_id: str, where: dict
    ) -> List[AssistantDataResponseItem]:
        """
        Query assistant data matching specific criteria.

        Args:
            assistant_id (str): The ID of the assistant whose data will be queried.
            where (dict): Dictionary specifying query filters. Ex: {"field": "search_value"}

        Returns:
            List[AssistantDataQueryItem]: A list of data entries matching the query.
        """
        response, status_code = RequestUtils.get(
            url=f"{self._base_url}/api/assistants/{assistant_id}/data",
            headers=self._headers,
            params=where,
            retry_strategy=self._retry_strategy,
        )
        return QueryAssistantDataResponse.model_validate(response).root

    def delete_data(
        self, assistant_id: str, id: Optional[str] = None, where: Optional[dict] = None
    ) -> DeleteAssistantDataResponse:
        """
        Delete assistant data by ID or matching criteria.

        Args:
            assistant_id (str): The ID of the assistant.
            id (Optional[str], optional): The ID of the data entry to delete. Defaults to None.
            where (Optional[dict], optional): Criteria to match data entries for deletion. Defaults to None.

        Raises:
            ValueError: If neither 'id' nor 'where' is provided.

        Returns:
            AssistantDataMessageResponse: The response from the API after deleting the data.
        """
        if id is None and where is None:
            raise ValueError("Either 'id' or 'where' must be provided.")

        response, status_code = RequestUtils.delete(
            url=f"{self._base_url}/api/assistants/{assistant_id}/data",
            headers=self._headers,
            json_payload={"where": where, "id": id},
            retry_strategy=self._retry_strategy,
        )
        return DeleteAssistantDataResponse.model_validate(response)

    ExecuteFunctionResponseType = TypeVar(
        "ExecuteFunctionResponseType", bound=BaseModel
    )

    @overload
    def execute_function(
        self,
        assistant_id: str,
        function_name: str,
        payload: dict,
        response_model: Type[ExecuteFunctionResponseType],
        conversation_id: Optional[str] = None,
        delay_in_seconds: Optional[int] = None,
    ) -> ExecuteFunctionResponseType:
        """When response_model is provided, returns the validated model instance."""
        ...

    @overload
    def execute_function(
        self,
        assistant_id: str,
        function_name: str,
        payload: dict,
        response_model: None = None,
        conversation_id: Optional[str] = None,
        delay_in_seconds: Optional[int] = None,
    ) -> dict[str, Any] | str:
        """When no response_model is provided, returns the raw response data."""
        ...

    def execute_function(
        self,
        assistant_id: str,
        function_name: str,
        payload: dict,
        response_model: Optional[Type[ExecuteFunctionResponseType]] = None,
        conversation_id: Optional[str] = None,
        delay_in_seconds: Optional[int] = None,
    ) -> ExecuteFunctionResponseType | dict[str, Any] | str:
        """
        Execute a specific function for an assistant and return the response.

        Args:
            assistant_id (str): The ID of the assistant.
            function_name (str): The name of the function to execute.
            payload (dict): The payload (paramet    ers) to send to the function.
            response_model (Optional[Type[ExecuteFunctionResponseType]], optional): The expected response model type for validation. Defaults to None.
            conversation_id (Optional[str], optional): The ID of the conversation to execute the function in. Defaults to None.
            delay_in_seconds (Optional[int], optional): The delay in seconds to wait before running the function. Defaults to None.

        Returns:
            ResponseType | dict[str, Any]: The response from the API. If response_model is provided, returns the validated model instance.

        Raises:
            ValidationError: If the response is not valid according to the response_model.

        Examples:
            # Direct response with model validation and type checking:
            result: MyModel = api.execute_function("assistant_id", "function_name", {}, MyModel)

            # Raw response without model validation:
            raw_data: dict[str, Any] = api.execute_function("assistant_id", "function_name", {})
        """

        request_data = payload
        params: dict[str, Any] = {}
        if delay_in_seconds is not None:
            params["delay"] = delay_in_seconds
        if conversation_id is not None:
            params["conversation_id"] = conversation_id

        response, status_code = RequestUtils.post(
            url=f"{self._base_url}/api/assistants/{assistant_id}/functions/{function_name}",
            headers=self._headers,
            json_payload=request_data,
            params=params,
            retry_strategy=self._retry_strategy,
        )

        return get_validated_data(response.get("result", response), response_model)

    def get_functions(self, assistant_id: str) -> AssistantCustomFunctionsResponse:
        """
        Retrieve custom functions for a specific assistant.

        Args:
            assistant_id (str): The ID of the assistant whose functions are to be retrieved.

        Returns:
            AssistantCustomFunctionsResponse: The custom functions for the assistant.
        """
        response, status_code = RequestUtils.get(
            url=f"{self._base_url}/api/assistants/{assistant_id}/functions",
            headers=self._headers,
            retry_strategy=self._retry_strategy,
        )
        return AssistantCustomFunctionsResponse.model_validate(response)

    def list_skills(self, assistant_id: str) -> list[SkillResponse]:
        """
        Retrieve all skills associated with a specific assistant.

        This includes both ASSISTANT-scoped skills (owned by the assistant) and
        GLOBAL-scoped skills (shared across assistants).

        Args:
            assistant_id (str): The ID of the assistant whose skills are to be listed.

        Returns:
            list[SkillResponse]: A list of skills associated with the assistant.
        """
        response, status_code = RequestUtils.get(
            url=f"{self._base_url}/api/assistants/{assistant_id}/skills",
            headers=self._headers,
            retry_strategy=self._retry_strategy,
        )
        return [SkillResponse.model_validate(skill) for skill in response]

    def add_skill(self, assistant_id: str, skill_id: str) -> AssistantSkillResponse:
        """
        Add a GLOBAL skill to a specific assistant.

        The skill must be GLOBAL-scoped and already exist. Only the assistant owner
        or collaborators can add skills.

        Args:
            assistant_id (str): The ID of the assistant.
            skill_id (str): The ID of the GLOBAL skill to add.

        Returns:
            AssistantSkillResponse: The response from the API after adding the skill.

        Raises:
            Exception: If the skill doesn't exist, is not GLOBAL-scoped, or the user
                      doesn't have permission.
        """
        response, status_code = RequestUtils.post(
            url=f"{self._base_url}/api/assistants/{assistant_id}/skills/{skill_id}",
            headers=self._headers,
            json_payload={},
            retry_strategy=self._retry_strategy,
        )
        return AssistantSkillResponse.model_validate(response)

    def remove_skill(self, assistant_id: str, skill_id: str) -> AssistantSkillResponse:
        """
        Remove a skill from a specific assistant.

        The behavior depends on the skill's scope:
        - GLOBAL skills: Only the association is removed (skill remains available for other assistants)
        - ASSISTANT skills: The skill is deleted entirely (it's owned by this assistant)

        Only the assistant owner or collaborators can remove skills.

        Args:
            assistant_id (str): The ID of the assistant.
            skill_id (str): The ID of the skill to remove.

        Returns:
            AssistantSkillResponse: The response from the API after removing the skill.

        Raises:
            Exception: If the skill doesn't exist or the user doesn't have permission.
        """
        response, status_code = RequestUtils.delete(
            url=f"{self._base_url}/api/assistants/{assistant_id}/skills/{skill_id}",
            headers=self._headers,
            retry_strategy=self._retry_strategy,
        )
        return AssistantSkillResponse.model_validate(response)

    @property
    def current(self) -> "CurrentAssistant":
        from .current_assistant import CurrentAssistant

        return CurrentAssistant(self)
