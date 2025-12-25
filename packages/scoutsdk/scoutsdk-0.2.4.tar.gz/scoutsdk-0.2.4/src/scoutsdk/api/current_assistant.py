from typing import Optional, Type, Any, overload, List
from pydantic import BaseModel
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
    AssistantDataResponseItem,
    AssistantDeleteResponse,
    DeleteAssistantDataResponse,
    AssistantDataUpdateResponse,
    CreateAssistantDataResponse,
    AssistantCustomFunctionsResponse,
    FileType,
    SkillResponse,
    AssistantSkillResponse,
)
from scouttypes.constants import VariableNames
from .assistants import AssistantsAPI
from .project_helpers import scout


class CurrentAssistant:
    def __init__(self, assistants_api: AssistantsAPI) -> None:
        self._assistants_api = assistants_api
        self._current_assistant_id = None

    def _get_current_assistant_id(self) -> str:
        if self._current_assistant_id is None:
            self._current_assistant_id = scout.context.get(
                VariableNames.SCOUT_ASSISTANT_ID
            )
            if self._current_assistant_id is None:
                raise ValueError(
                    "Current assistant ID not found in scout context. Make sure SCOUT_ASSISTANT_ID is set."
                )
        return self._current_assistant_id

    def update(
        self,
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
        return self._assistants_api.update(
            assistant_id=self._get_current_assistant_id(),
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
            content_retrieving_strategy=content_retrieving_strategy,
        )

    def get(self) -> AssistantInfoResponse:
        return self._assistants_api.get(assistant_id=self._get_current_assistant_id())

    def get_public(self) -> AssistantPublicResponse:
        return self._assistants_api.get_public(
            assistant_id=self._get_current_assistant_id()
        )

    def delete(self) -> AssistantDeleteResponse:
        return self._assistants_api.delete(
            assistant_id=self._get_current_assistant_id()
        )

    def upload_avatar(
        self,
        file_path: str,
    ) -> AssistantUploadImageResponse:
        return self._assistants_api.upload_avatar(
            assistant_id=self._get_current_assistant_id(),
            file_path=file_path,
        )

    def upload_file(
        self,
        file_path: str,
        file_type: Optional[FileType] = None,
    ) -> AssistantFileUploadResponse:
        return self._assistants_api.upload_file(
            assistant_id=self._get_current_assistant_id(),
            file_path=file_path,
            file_type=file_type,
        )

    def list_files(
        self,
    ) -> List[AssistantFile]:
        return self._assistants_api.list_files(
            assistant_id=self._get_current_assistant_id(),
        )

    def edit_file(
        self,
        file_uid: str,
        filename: str = "Default",
        description: Optional[str] = None,
    ) -> AssistantFileEditResponse:
        return self._assistants_api.edit_file(
            assistant_id=self._get_current_assistant_id(),
            file_uid=file_uid,
            filename=filename,
            description=description,
        )

    def delete_file(
        self,
        file_uid: str,
    ) -> AssistantResponse:
        return self._assistants_api.delete_file(
            assistant_id=self._get_current_assistant_id(),
            file_uid=file_uid,
        )

    def search_data(
        self,
        query: str,
        strategy: Optional[dict] = None,
        where: Optional[dict] = None,
    ) -> List[AssistantSearchDataResponse]:
        return self._assistants_api.search_data(
            assistant_id=self._get_current_assistant_id(),
            query=query,
            strategy=strategy,
            where=where,
        )

    def create_data(
        self,
        data: AssistantData | AssistantDataList,
    ) -> CreateAssistantDataResponse:
        return self._assistants_api.create_data(
            assistant_id=self._get_current_assistant_id(),
            data=data,
        )

    def update_data(
        self,
        data_id: str,
        content: str,
        metadata: dict,
    ) -> AssistantDataUpdateResponse:
        return self._assistants_api.update_data(
            assistant_id=self._get_current_assistant_id(),
            data_id=data_id,
            content=content,
            metadata=metadata,
        )

    def query_data(
        self,
        where: dict,
    ) -> List[AssistantDataResponseItem]:
        return self._assistants_api.query_data(
            assistant_id=self._get_current_assistant_id(),
            where=where,
        )

    def delete_data(
        self,
        id: Optional[str] = None,
        where: Optional[dict] = None,
    ) -> DeleteAssistantDataResponse:
        return self._assistants_api.delete_data(
            assistant_id=self._get_current_assistant_id(),
            id=id,
            where=where,
        )

    @overload
    def execute_function(
        self,
        function_name: str,
        payload: dict,
        response_model: Type[BaseModel],
        conversation_id: Optional[str] = None,
        delay_in_seconds: Optional[int] = None,
    ) -> BaseModel: ...

    @overload
    def execute_function(
        self,
        function_name: str,
        payload: dict,
        response_model: None = None,
        conversation_id: Optional[str] = None,
        delay_in_seconds: Optional[int] = None,
    ) -> dict[str, Any] | str: ...

    def execute_function(
        self,
        function_name: str,
        payload: dict,
        response_model: Optional[Type[BaseModel]] = None,
        conversation_id: Optional[str] = None,
        delay_in_seconds: Optional[int] = None,
    ) -> Any:
        return self._assistants_api.execute_function(
            assistant_id=self._get_current_assistant_id(),
            function_name=function_name,
            payload=payload,
            response_model=response_model,
            conversation_id=conversation_id,
            delay_in_seconds=delay_in_seconds,
        )

    def get_functions(self) -> AssistantCustomFunctionsResponse:
        return self._assistants_api.get_functions(
            assistant_id=self._get_current_assistant_id()
        )

    def list_skills(self) -> list[SkillResponse]:
        return self._assistants_api.list_skills(
            assistant_id=self._get_current_assistant_id()
        )

    def add_skill(self, skill_id: str) -> AssistantSkillResponse:
        return self._assistants_api.add_skill(
            assistant_id=self._get_current_assistant_id(),
            skill_id=skill_id,
        )

    def remove_skill(self, skill_id: str) -> AssistantSkillResponse:
        return self._assistants_api.remove_skill(
            assistant_id=self._get_current_assistant_id(),
            skill_id=skill_id,
        )
