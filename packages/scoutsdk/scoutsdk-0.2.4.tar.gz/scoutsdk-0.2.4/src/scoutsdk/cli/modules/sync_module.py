import argparse
import json
import os
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional, Union
from pydantic import BaseModel


from .base_module import BaseModule
from .pkg_module import PkgModule
from ..config import Config
from ..error_handler import FileSystemError, ModuleError, logger
from ..types import GenericResponse, EmptyRequest
from ..utils import extract_tenant_id_from_token
from scoutsdk.api import ScoutAPI
from scoutsdk import scout
from scouttypes.constants import VariableNames


# Pydantic models for the config file
class ConfigAssistantFile(BaseModel):
    filepath: str
    description: Optional[str] = None


class ConfigPackage(BaseModel):
    package_path: str
    package_file_name: str


class ConfigUI(BaseModel):
    ui_path: str
    ui_package_file_name: str
    ui_build_cmd: Optional[str] = None


class ConfigAssistant(BaseModel):
    name: str
    id: str
    description: str
    instructions_text: Optional[str] = None
    instructions_path: Optional[str] = None
    allowed_functions: Optional[List[str]] = None
    allowed_external_services: Optional[List[str]] = None
    use_system_prompt: bool = False
    prompt_starters_text: Optional[List[str]] = None
    prompt_starters_path: Optional[List[str]] = None
    assistant_files: List[Union[str, ConfigAssistantFile]] = []
    avatar_path: Optional[str] = None
    visibility_type: Optional[str] = None
    variables: Optional[dict] = None
    secrets: Optional[dict] = None
    secrets_path: Optional[str] = None
    package_info: Optional[ConfigPackage] = None
    ui_url: Optional[str] = None
    ui_info: Optional[ConfigUI] = None
    global_skills: Optional[List[str]] = None

    model_config = {"extra": "forbid"}


class SyncConfig(BaseModel):
    assistants: List[ConfigAssistant]


class AssistantIds(BaseModel):
    id: str
    assistant_id: str


class DeployedTenantIds(BaseModel):
    tenant_id: str
    ids: list[AssistantIds]


class DeployedUrlIds(BaseModel):
    url: str
    ids_by_tenant: list[DeployedTenantIds]


class DeployedIds(BaseModel):
    ids_by_url: list[DeployedUrlIds]


DEV_IDS_URLS = ["localhost", "127.0.0.1"]
DEV_ASSISTANT_IDS_FILENAME = ".dev.assistant_ids.json"
ASSISTANT_IDS_FILENAME = "assistant_ids.json"


class SyncModule(BaseModule):
    def __init__(self, config: Config, pkg_module: PkgModule):
        self.config = config
        self._pkg_module = pkg_module
        self._deployed_ids_file: Path = Path(ASSISTANT_IDS_FILENAME)
        self._deployed_ids: DeployedIds = DeployedIds(ids_by_url=[])
        self._api_url = self._get_api_url()
        self._tenant_id = self._get_tenant_id()

    def _get_api_url(self) -> str:
        try:
            api_url = scout.context.get("SCOUT_API_URL", "")
            if api_url:
                return api_url
        except Exception as e:
            logger.warning(f"Error parsing SCOUT_CONTEXT: {str(e)}")
        return ""

    def _get_tenant_id(self) -> str:
        try:
            token = scout.context.get(VariableNames.SCOUT_API_ACCESS_TOKEN, "")
            if token:
                tenant_id = extract_tenant_id_from_token(token)
                if tenant_id:
                    return tenant_id
        except Exception as e:
            logger.warning(f"Error extracting tenant_id from token: {str(e)}")
        return "unknown"

    def get_command(self) -> str:
        return "synchronize-assistants"

    def add_parser(self, subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            self.get_command(), help="Synchronize assistants command"
        )

        parser.add_argument(
            "-c", "--config", type=str, help="Path to config.json file", required=True
        )
        parser.add_argument(
            "-f", "--force", action="store_true", help="Force overwrite assistant files"
        )

        # Set the default function to be called
        parser.set_defaults(func=self.execute)

    def execute(self, args: argparse.Namespace) -> None:
        self.sync_config = self._load_config(args.config)
        try:
            original_working_dir = os.getcwd()
            os.chdir(Path(args.config).parent)
            self._load_assistant_ids()

            scout_api = ScoutAPI()

            for assistant in self.sync_config.assistants:
                self._sync_assistant(assistant, args.force, scout_api)

            self._save_deployed_ids()

        finally:
            os.chdir(original_working_dir)

    def _load_config(self, config_path: str) -> SyncConfig:
        self.config_file = Path(config_path)
        if not self.config_file.exists():
            raise FileSystemError(f"Config file not found: {config_path}")

        with open(self.config_file, "r") as f:
            try:
                config_data = json.load(f)
            except Exception as e:
                raise ModuleError(f"Error reading config file: {str(e)}")
        # Start with assistants from the config, or an empty list
        assistants = config_data.get("assistants", [])

        # Handle assistants_ref if present
        assistants_ref = config_data.pop("assistants_ref", [])
        config_dir = Path(config_path).parent
        for ref_path in assistants_ref:
            # Make ref_path relative to the config file directory
            assistant_json_ref_file_path = config_dir / Path(ref_path)
            if not assistant_json_ref_file_path.exists():
                logger.warning(
                    f"Assistant ref file not found: {assistant_json_ref_file_path}"
                )
                continue
            try:
                with open(assistant_json_ref_file_path, "r") as af:
                    assistant_data = json.load(af)
                    assistants_refs = assistant_data.get("assistants", [])
                    for a_ref in assistants_refs:
                        self._fix_assistant_paths_with_ref_path(
                            a_ref, Path(ref_path).parent
                        )
                        assistants.append(a_ref)
            except Exception as e:
                raise ModuleError(
                    f"Error loading assistant ref {assistant_json_ref_file_path}: {str(e)}"
                )

        if len(assistants) == 0:
            raise ModuleError("No assistants found in config file")

        # Replace the assistants in config_data with the merged list
        config_data["assistants"] = assistants

        try:
            return SyncConfig.model_validate(config_data, strict=True)
        except Exception as e:
            raise ModuleError(f"Error validating config data: {str(e)}")

    def _fix_assistant_paths_with_ref_path(
        self, assistant: dict, ref_path: Path
    ) -> None:
        def join_path(p: str) -> str:
            return str(ref_path / p)

        # Single path fields
        for key in ["instructions_path", "avatar_path", "secrets_path"]:
            if key in assistant and assistant[key]:
                assistant[key] = join_path(assistant[key])

        # List of paths (prompt_starters_path)
        if "prompt_starters_path" in assistant and assistant["prompt_starters_path"]:
            assistant["prompt_starters_path"] = [
                join_path(p) for p in assistant["prompt_starters_path"]
            ]

        # assistant_files: list of dicts or strings
        if "assistant_files" in assistant and assistant["assistant_files"]:
            new_files = []
            for f in assistant["assistant_files"]:
                if isinstance(f, dict) and "filepath" in f:
                    f["filepath"] = join_path(f["filepath"])
                    new_files.append(f)
                elif isinstance(f, ConfigAssistantFile) and f.filepath:
                    f.filepath = join_path(f.filepath)
                    new_files.append(f.model_dump())
            assistant["assistant_files"] = new_files

        # package_info
        if "package_info" in assistant and assistant["package_info"]:
            pkg = assistant["package_info"]
            if "package_path" in pkg and pkg["package_path"]:
                pkg["package_path"] = join_path(pkg["package_path"])

        # ui_info
        if "ui_info" in assistant and assistant["ui_info"]:
            ui = assistant["ui_info"]
            if "ui_path" in ui and ui["ui_path"]:
                ui["ui_path"] = join_path(ui["ui_path"])

    def _save_config(self, sync_config: SyncConfig) -> None:
        with open(self.config_file, "w") as f:
            json.dump(sync_config.model_dump(), f, indent=2)

    def _sync_assistant(
        self, assistant: ConfigAssistant, force: bool, scout_api: ScoutAPI
    ) -> None:
        # Check if this assistant exists
        assistant_exists, deployed_id = self._assistant_exists(assistant, scout_api)

        instructions = self._load_instructions(assistant)
        prompt_starters = self._load_prompt_starters(assistant)
        allowed_functions = self._load_allowed_functions(assistant)
        secrets = self._load_secrets(assistant)
        package_file_name = self._load_package(assistant)
        ui_package_file_name = self._load_ui_package(assistant)

        if not assistant_exists and not deployed_id:
            # Create new assistant
            logger.debug(f"Creating assistant: {assistant.name}")
            response = scout_api.assistants.create(
                name=assistant.name,
                description=assistant.description,
                instructions=instructions,
                use_system_prompt=assistant.use_system_prompt,
                prompt_starters=prompt_starters,
                allowed_functions=allowed_functions,
                variables=assistant.variables,
                secrets=secrets,
                allowed_external_services=assistant.allowed_external_services,
                **(
                    {"visibility_type": assistant.visibility_type}
                    if assistant.visibility_type
                    else {}
                ),
                **({"ui_url": assistant.ui_url} if assistant.ui_url else {}),
            )

            # Store the new assistant ID
            deployed_id = response.id
            if not deployed_id:
                raise ModuleError("Failed to get ID for newly created assistant")

            self._store_deployed_assistant_id(assistant, deployed_id)

        avatar_url = None
        if assistant.avatar_path:
            logger.debug(
                f"Uploading avatar for assistant: {assistant.name}, id: {deployed_id}"
            )
            upload_avatar_response = scout_api.assistants.upload_avatar(
                deployed_id, assistant.avatar_path
            )
            avatar_url = upload_avatar_response.protected_url

        # update the assistant if it exists or if the avatar url is not None this will update the avatar url for newly created assistants
        if assistant_exists or avatar_url is not None:
            # Update existing assistant
            logger.debug(f"Updating assistant: {assistant.name}, id: {deployed_id}")

            scout_api.assistants.update(
                assistant_id=deployed_id,
                name=assistant.name,
                description=assistant.description,
                instructions=instructions,
                use_system_prompt=assistant.use_system_prompt,
                prompt_starters=prompt_starters,
                allowed_functions=allowed_functions,
                avatar_url=avatar_url,
                variables=assistant.variables,
                secrets=secrets,
                ui_url=assistant.ui_url,
                allowed_external_services=assistant.allowed_external_services,
                visibility_type=assistant.visibility_type,
            )

        # Sync assistant files
        self._sync_assistant_files(
            assistant, deployed_id, package_file_name, force, scout_api
        )
        self._sync_assistant_ui(assistant, deployed_id, ui_package_file_name, scout_api)

        # Sync ASSISTANT-scoped skill (package_info)
        self._sync_assistant_skill(deployed_id, package_file_name, scout_api)

        # Sync global skills
        self._sync_global_skills(assistant, deployed_id, scout_api)

    def _load_instructions(self, assistant: ConfigAssistant) -> str:
        if assistant.instructions_text:
            return assistant.instructions_text
        elif assistant.instructions_path:
            try:
                with open(assistant.instructions_path, "r") as f:
                    return f.read()
            except FileNotFoundError:
                raise FileSystemError(
                    f"Instructions file not found: {assistant.instructions_path}"
                )
            except Exception as e:
                raise FileSystemError(f"Error reading instructions file: {str(e)}")
        return ""

    def _load_secrets(self, assistant: ConfigAssistant) -> Optional[dict]:
        if assistant.secrets:
            return assistant.secrets
        elif assistant.secrets_path:
            try:
                with open(assistant.secrets_path, "r") as f:
                    secrets = json.load(f)
                    if not isinstance(secrets, dict):
                        raise ValueError("Secrets files must be a json dictionary")
                    return secrets
            except FileNotFoundError:
                raise FileSystemError(
                    f"Secrets file not found: {assistant.secrets_path}"
                )
            except json.JSONDecodeError:
                raise ValueError(
                    f"Secrets files {assistant.secrets_path} must be a json dictionary"
                )
            except Exception as e:
                raise FileSystemError(f"Error reading secrets file: {str(e)}")
        return None

    def _load_prompt_starters(self, assistant: ConfigAssistant) -> List[str]:
        prompt_starters = []
        if assistant.prompt_starters_text:
            prompt_starters.extend(assistant.prompt_starters_text)
        if assistant.prompt_starters_path:
            for path in assistant.prompt_starters_path:
                if Path(path).exists():
                    with open(path, "r") as f:
                        prompt_starters.append(f.read())
                else:
                    logger.warning(f"Prompt starter file not found: {path}")

        return prompt_starters

    def _load_allowed_functions(self, assistant: ConfigAssistant) -> List[str] | None:
        if assistant.allowed_functions is not None:
            if len(assistant.allowed_functions) == 0:
                return []
            if (
                len(assistant.allowed_functions) == 1
                and assistant.allowed_functions[0].lower() == "all"
            ):
                return None

            return assistant.allowed_functions

        return None

    def _load_package(self, assistant: ConfigAssistant) -> Optional[str]:
        if not assistant.package_info:
            return None

        try:
            self._pkg_module.generate_package(
                assistant.package_info.package_path,
                assistant.package_info.package_file_name,
            )
        except Exception as e:
            raise ModuleError(
                f"Error generating package while synchronizing assistants package_info {assistant.package_info} : {str(e)}"
            )

        return assistant.package_info.package_file_name

    def _load_ui_package(self, assistant: ConfigAssistant) -> Optional[str]:
        if assistant.ui_url or not assistant.ui_info:
            return None

        try:
            # Run build command if specified
            if assistant.ui_info.ui_build_cmd:
                logger.debug(
                    f"Running UI build command: {assistant.ui_info.ui_build_cmd}"
                )

                subprocess.run(assistant.ui_info.ui_build_cmd, shell=True, check=True)

            ui_path = Path(assistant.ui_info.ui_path)
            if not ui_path.exists():
                raise FileSystemError(f"UI path not found: {ui_path}")

            output_zip = Path(assistant.ui_info.ui_package_file_name)
            if output_zip.exists():
                output_zip.unlink()  # Remove existing zip if present
            # Ensure ui_path is a directory
            if not ui_path.is_dir():
                raise FileSystemError(f"UI path must be a directory: {ui_path}")

            # Create zip archive from directory
            shutil.make_archive(
                str(
                    output_zip.with_suffix("")
                ),  # Remove .zip extension for make_archive
                "zip",
                ui_path,
            )

            logger.debug(
                f"UI package file name: {assistant.ui_info.ui_package_file_name}"
            )
            return assistant.ui_info.ui_package_file_name

        except subprocess.CalledProcessError as e:
            raise ModuleError(f"Error running UI build command: {str(e)}")
        except Exception as e:
            raise ModuleError(f"Error generating UI package: {str(e)}")

    def _update_deployed_assistant_id(
        self, assistant_id: str, deployed_id: str
    ) -> None:
        if not self._api_url:
            return

        url_entry = None
        for url_ids in self._deployed_ids.ids_by_url:
            if url_ids.url == self._api_url:
                url_entry = url_ids
                break

        if not url_entry:
            url_entry = DeployedUrlIds(url=self._api_url, ids_by_tenant=[])
            self._deployed_ids.ids_by_url.append(url_entry)

        tenant_entry = None
        for tenant_ids in url_entry.ids_by_tenant:
            if tenant_ids.tenant_id == self._tenant_id:
                tenant_entry = tenant_ids
                break

        if not tenant_entry:
            tenant_entry = DeployedTenantIds(tenant_id=self._tenant_id, ids=[])
            url_entry.ids_by_tenant.append(tenant_entry)

        existing_entry = None
        for assistant_id_entry in tenant_entry.ids:
            if assistant_id_entry.id == assistant_id:
                existing_entry = assistant_id_entry
                break

        if existing_entry:
            existing_entry.assistant_id = deployed_id
        else:
            tenant_entry.ids.append(
                AssistantIds(id=assistant_id, assistant_id=deployed_id)
            )

    def _assistant_exists(
        self, assistant: ConfigAssistant, scout_api: ScoutAPI
    ) -> tuple[bool, str]:
        # Get all existing assistants
        existing_assistants = scout_api.assistants.list_all()

        # Check if this assistant exists by ID (if ID is provided)
        assistant_id = self._find_assistant_id(assistant)
        if assistant_id:
            for existing in existing_assistants:
                if existing.id == assistant_id:
                    return True, assistant_id

        return False, ""

    def _sync_assistant_files(
        self,
        assistant: ConfigAssistant,
        deployed_id: str,
        package_file_name: Optional[str],
        force: bool,
        scout_api: ScoutAPI,
    ) -> None:
        if not assistant.assistant_files and not package_file_name:
            return

        # Upload knowledge files
        self._upload_assistant_knowledge_files(assistant, deployed_id, force, scout_api)

        # Edit knowledge file metadata (descriptions, etc.)
        self._edit_assistant_files(assistant, deployed_id, scout_api)

    def _upload_assistant_knowledge_files(
        self,
        assistant: ConfigAssistant,
        deployed_id: str,
        force_overwrite: bool,
        scout_api: ScoutAPI,
    ) -> None:
        if not assistant.assistant_files:
            return

        # Get existing files
        existing_files = scout_api.assistants.list_files(deployed_id)
        existing_filenames = {file.filename: file for file in existing_files}

        # Handle regular assistant files (knowledge/documents)
        for file_item in assistant.assistant_files:
            if isinstance(file_item, str):
                filepath = file_item
            else:
                filepath = file_item.filepath

            file_path = Path(filepath)
            if not file_path.exists():
                logger.warning(f"Assistant file not found: {filepath}")
                continue

            filename = file_path.name
            existing_file = existing_filenames.get(filename)

            if existing_file:
                if force_overwrite:
                    self._overwrite_assistant_file(
                        deployed_id, file_path, existing_file.id, scout_api
                    )
            else:
                self._upload_new_assistant_file(deployed_id, file_path, scout_api)

    def _overwrite_assistant_file(
        self, assistant_id: str, file_path: Path, file_uid: str, scout_api: ScoutAPI
    ) -> None:
        logger.debug(f"Force replacing file: {file_path.name}")
        scout_api.assistants.delete_file(assistant_id=assistant_id, file_uid=file_uid)
        scout_api.assistants.upload_file(
            assistant_id=assistant_id,
            file_path=str(file_path),
        )

    def _upload_new_assistant_file(
        self, assistant_id: str, file_path: Path, scout_api: ScoutAPI
    ) -> None:
        logger.debug(f"Uploading file: {file_path.name}")
        scout_api.assistants.upload_file(
            assistant_id=assistant_id, file_path=str(file_path)
        )

    def _edit_assistant_files(
        self, assistant: ConfigAssistant, deployed_id: str, scout_api: ScoutAPI
    ) -> None:
        existing_files = scout_api.assistants.list_files(deployed_id)
        existing_filenames = {file.filename for file in existing_files}

        # Process each file in the config
        for file_item in assistant.assistant_files:
            # if the file name match existing files, update the file

            if isinstance(file_item, str):
                filepath = file_item
                description = None
            else:
                filepath = file_item.filepath
                description = file_item.description

            filename = Path(filepath).name
            if filename in existing_filenames:
                for file in existing_files:
                    if file.filename == filename:
                        scout_api.assistants.edit_file(
                            assistant_id=deployed_id,
                            file_uid=file.id,
                            filename=filename,
                            description=description,
                        )

    def _sync_assistant_ui(
        self,
        assistant: ConfigAssistant,
        deployed_id: str,
        ui_package_file_name: Optional[str],
        scout_api: ScoutAPI,
    ) -> None:
        if not ui_package_file_name:
            return

        logger.debug(f"Deploying UI for assistant: {deployed_id}")
        with open(ui_package_file_name, "rb") as f:
            response = scout_api.post(
                url=f"/api/assistants/{deployed_id}/ui/deploy",
                data=EmptyRequest(),
                response_model=GenericResponse,
                files={"ui": f},
            )

        if response.status_code < 200 or response.status_code >= 300:
            raise ModuleError(f"Error deploying UI: {response.status_code}")

    def _sync_global_skills(
        self,
        assistant: ConfigAssistant,
        deployed_id: str,
        scout_api: ScoutAPI,
    ) -> None:
        # If no global_skills field or empty list, ensure no global skills are attached
        desired_skill_ids = set(assistant.global_skills or [])

        # Get current skills for this assistant
        try:
            current_skills = scout_api.assistants.list_skills(deployed_id)
        except Exception as e:
            logger.warning(
                f"Error listing skills for assistant {assistant.name}: {str(e)}"
            )
            return

        # Filter to only GLOBAL-scoped skills (ignore ASSISTANT-scoped)
        current_global_skills = [s for s in current_skills if s.scope == "GLOBAL"]
        current_global_skill_ids = set(s.id for s in current_global_skills)

        # Calculate skills to add and remove
        skills_to_add = desired_skill_ids - current_global_skill_ids
        skills_to_remove = current_global_skill_ids - desired_skill_ids

        # Remove extra skills
        for skill_id in skills_to_remove:
            try:
                logger.debug(
                    f"Removing global skill {skill_id} from assistant {assistant.name}"
                )
                scout_api.assistants.remove_skill(deployed_id, skill_id)
            except Exception as e:
                logger.warning(
                    f"Error removing skill {skill_id} from assistant {assistant.name}: {str(e)}"
                )

        # Add missing skills
        for skill_id in skills_to_add:
            try:
                logger.debug(
                    f"Adding global skill {skill_id} to assistant {assistant.name}"
                )
                scout_api.assistants.add_skill(deployed_id, skill_id)
            except Exception as e:
                raise ModuleError(
                    f"Error adding skill {skill_id} to assistant {assistant.name}: {str(e)}. "
                    f"Make sure the skill exists and is GLOBAL-scoped."
                )

        if skills_to_add or skills_to_remove:
            logger.info(
                f"Synced global skills for assistant {assistant.name}: "
                f"added {len(skills_to_add)}, removed {len(skills_to_remove)}"
            )

    def _sync_assistant_skill(
        self,
        deployed_id: str,
        package_file_name: Optional[str],
        scout_api: ScoutAPI,
    ) -> None:
        if not package_file_name:
            return

        package_path = Path(package_file_name)
        if not package_path.exists():
            logger.warning(f"Package file not found: {package_file_name}")
            return

        # Get current skills for this assistant
        try:
            current_skills = scout_api.assistants.list_skills(deployed_id)
        except Exception as e:
            logger.warning(f"Error listing skills for assistant: {str(e)}")
            return

        # Filter to only ASSISTANT-scoped skills
        current_assistant_skills = [s for s in current_skills if s.scope == "ASSISTANT"]

        # Match by filename (without extension)
        # When a package like "assistant_functions.zip" is uploaded, the skill's name
        # is set to the filename base (e.g., "assistant_functions")
        package_filename_base = package_path.stem

        existing_skill = None
        for skill in current_assistant_skills:
            if skill.type == "FUNCTIONS" and skill.name == package_filename_base:
                existing_skill = skill
                break

        # Remove existing ASSISTANT skill if found
        if existing_skill:
            try:
                logger.debug(
                    f"Removing existing assistant skill {existing_skill.id} to replace with new package"
                )
                scout_api.assistants.remove_skill(deployed_id, existing_skill.id)
            except Exception as e:
                logger.warning(f"Error removing existing assistant skill: {str(e)}")

        # Upload new package as CUSTOM_FUNCTIONS (creates ASSISTANT skill)
        try:
            logger.debug(
                f"Uploading package file as assistant skill: {package_path.name}"
            )
            scout_api.assistants.upload_file(
                assistant_id=deployed_id,
                file_path=str(package_path),
            )
        except Exception as e:
            raise ModuleError(f"Error uploading assistant skill package: {str(e)}")

    def _load_assistant_ids(self) -> None:
        is_dev_environment = (
            any(dev_url in self._api_url for dev_url in DEV_IDS_URLS)
            if self._api_url
            else False
        )
        logger.debug(
            f"Detected environment from SCOUT_CONTEXT: {'dev' if is_dev_environment else 'prod'}"
        )

        file = (
            Path(DEV_ASSISTANT_IDS_FILENAME)
            if is_dev_environment
            else Path(ASSISTANT_IDS_FILENAME)
        )
        self._deployed_ids_file = file
        if file.exists():
            with open(file, "r") as f:
                try:
                    data = json.load(f)
                    data = self._migrate_old_format(data)
                    self._deployed_ids = DeployedIds.model_validate(data)
                except Exception as e:
                    raise ModuleError(f"Error reading {file}: {str(e)}")
        else:
            logger.warning("No assistant_ids file found.")
            self._deployed_ids = DeployedIds(ids_by_url=[])

    def _migrate_old_format(self, data: dict) -> dict:
        """Migrate old format (url -> ids) to new format (url -> tenant_id -> ids)."""
        for url_entry in data.get("ids_by_url", []):
            if "ids" in url_entry and "ids_by_tenant" not in url_entry:
                logger.info(
                    f"Migrating old assistant ID format for {url_entry['url']} to tenant-aware format"
                )
                url_entry["ids_by_tenant"] = [
                    {"tenant_id": "unknown", "ids": url_entry.pop("ids")}
                ]
        return data

    def _find_assistant_id(self, assistant: ConfigAssistant) -> str | None:
        if not self._api_url:
            return None

        for url_ids in self._deployed_ids.ids_by_url:
            if url_ids.url == self._api_url:
                for tenant_ids in url_ids.ids_by_tenant:
                    if tenant_ids.tenant_id == self._tenant_id:
                        for assistant_id in tenant_ids.ids:
                            if assistant_id.id == assistant.id:
                                return assistant_id.assistant_id
        return None

    def _save_deployed_ids(self) -> None:
        with open(self._deployed_ids_file, "w") as f:
            json.dump(self._deployed_ids.model_dump(), f, indent=2)

    def _store_deployed_assistant_id(
        self, assistant: ConfigAssistant, deployed_id: str
    ) -> None:
        self._update_deployed_assistant_id(assistant.id, deployed_id)
