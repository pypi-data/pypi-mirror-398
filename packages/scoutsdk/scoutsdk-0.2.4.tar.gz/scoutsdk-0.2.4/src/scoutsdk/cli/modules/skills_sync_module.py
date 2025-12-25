import argparse
import json
import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel

from .pkg_module import PkgModule
from ..config import Config
from ..error_handler import FileSystemError, ModuleError, logger
from ..utils import extract_tenant_id_from_token
from scoutsdk.api import ScoutAPI
from scoutsdk import scout
from scouttypes.constants import VariableNames


# Pydantic models for the config file
class ConfigSkillPackage(BaseModel):
    package_path: str
    package_file_name: str


class ConfigSkill(BaseModel):
    id: str
    name: str
    description: str
    package_info: ConfigSkillPackage
    usable_in: Optional[List[str]] = None

    model_config = {"extra": "forbid"}


class SkillsSyncConfig(BaseModel):
    skills: List[ConfigSkill]


# Pydantic models for ID tracking
class SkillIds(BaseModel):
    id: str  # Local config ID
    skill_id: str  # Remote server ID


class DeployedSkillTenantIds(BaseModel):
    tenant_id: str
    ids: List[SkillIds]


class DeployedSkillUrlIds(BaseModel):
    url: str  # API URL
    ids_by_tenant: List[DeployedSkillTenantIds]


class DeployedSkillIds(BaseModel):
    ids_by_url: List[DeployedSkillUrlIds]


DEV_IDS_URLS = ["localhost", "127.0.0.1"]
DEV_SKILL_IDS_FILENAME = ".dev.skill_ids.json"
SKILL_IDS_FILENAME = "skill_ids.json"


class SkillsSyncModule:
    """Internal helper class for synchronizing skills.

    This is not a CLI command module - it's used internally by SkillsModule.
    The execute() method accepts a namespace with 'config' and 'force' attributes.
    """

    def __init__(self, config: Config, pkg_module: PkgModule):
        self.config = config
        self._pkg_module = pkg_module
        self._deployed_ids_file: Path = Path(SKILL_IDS_FILENAME)
        self._deployed_ids: DeployedSkillIds = DeployedSkillIds(ids_by_url=[])
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

    def execute(self, args: argparse.Namespace) -> None:
        """Execute skills synchronization.

        Args:
            args: Namespace with 'config' (path to skills.json) and 'force' (bool) attributes.
                  These are provided by the calling module (SkillsModule).
        """
        self.sync_config = self._load_config(args.config)
        try:
            original_working_dir = os.getcwd()
            os.chdir(Path(args.config).parent)
            self._load_skill_ids()

            scout_api = ScoutAPI()

            for skill in self.sync_config.skills:
                self._sync_skill(skill, args.force, scout_api)

            self._save_deployed_ids()

        finally:
            os.chdir(original_working_dir)

    def _load_config(self, config_path: str) -> SkillsSyncConfig:
        self.config_file = Path(config_path)
        if not self.config_file.exists():
            raise FileSystemError(f"Config file not found: {config_path}")

        with open(self.config_file, "r") as f:
            try:
                config_data = json.load(f)
            except Exception as e:
                raise ModuleError(f"Error reading config file: {str(e)}")

        # Get skills from config
        skills = config_data.get("skills", [])

        if len(skills) == 0:
            raise ModuleError("No skills found in config file")

        try:
            return SkillsSyncConfig.model_validate(config_data, strict=True)
        except Exception as e:
            raise ModuleError(f"Error validating config data: {str(e)}")

    def _sync_skill(self, skill: ConfigSkill, force: bool, scout_api: ScoutAPI) -> None:
        # Check if this skill exists
        skill_exists, deployed_id = self._skill_exists(skill, scout_api)

        # Always package the functions
        package_file_name = self._load_package(skill)

        if not skill_exists and not deployed_id:
            # Create new skill
            logger.info(f"Creating skill: {skill.name}")
            deployed_id = self._create_skill(skill, package_file_name, scout_api)

            if not deployed_id:
                raise ModuleError("Failed to get ID for newly created skill")

            self._store_deployed_skill_id(skill, deployed_id)
            logger.info(f"✓ Created skill: {skill.name} (ID: {deployed_id})")

        elif skill_exists and deployed_id:
            # Update existing skill if force is enabled
            if force:
                logger.info(f"Updating skill: {skill.name} (ID: {deployed_id})")
                self._update_skill(deployed_id, skill, package_file_name, scout_api)
                logger.info(f"✓ Updated skill: {skill.name}")
            else:
                logger.info(
                    f"Skipping existing skill: {skill.name} (use --force to update)"
                )

    def _load_package(self, skill: ConfigSkill) -> str:
        """Generate package from the functions directory."""
        try:
            self._pkg_module.generate_package(
                skill.package_info.package_path,
                skill.package_info.package_file_name,
            )
        except Exception as e:
            raise ModuleError(
                f"Error generating package for skill '{skill.name}': {str(e)}"
            )

        return skill.package_info.package_file_name

    def _create_skill(
        self, skill: ConfigSkill, package_file_name: str, scout_api: ScoutAPI
    ) -> str:
        """Create a new global skill on the server."""
        try:
            skill_id = scout_api.skills.create(
                name=skill.name,
                description=skill.description,
                package_path=package_file_name,
                skill_type="FUNCTIONS",
                usable_in=skill.usable_in,
            )
            return skill_id
        except Exception as e:
            raise ModuleError(f"Error creating skill '{skill.name}': {str(e)}")

    def _update_skill(
        self,
        skill_id: str,
        skill: ConfigSkill,
        package_file_name: str,
        scout_api: ScoutAPI,
    ) -> None:
        """Update an existing global skill on the server."""
        try:
            scout_api.skills.update(
                skill_id=skill_id,
                name=skill.name,
                description=skill.description,
                package_path=package_file_name,
                skill_type="FUNCTIONS",
                usable_in=skill.usable_in,
            )
        except Exception as e:
            raise ModuleError(f"Error updating skill '{skill.name}': {str(e)}")

    def _skill_exists(
        self, skill: ConfigSkill, scout_api: ScoutAPI
    ) -> tuple[bool, str]:
        """Check if skill exists by looking up its ID."""
        skill_id = self._find_skill_id(skill)
        if skill_id:
            # Verify it exists on the server
            try:
                scout_api.skills.get(skill_id)
                return True, skill_id
            except Exception:
                # If we can't verify, assume it doesn't exist
                pass

        return False, ""

    def _load_skill_ids(self) -> None:
        """Load skill IDs from file (dev or prod based on environment)."""
        is_dev_environment = (
            any(dev_url in self._api_url for dev_url in DEV_IDS_URLS)
            if self._api_url
            else False
        )
        logger.debug(
            f"Detected environment from SCOUT_CONTEXT: {'dev' if is_dev_environment else 'prod'}"
        )

        file = (
            Path(DEV_SKILL_IDS_FILENAME)
            if is_dev_environment
            else Path(SKILL_IDS_FILENAME)
        )
        self._deployed_ids_file = file
        if file.exists():
            with open(file, "r") as f:
                try:
                    data = json.load(f)
                    data = self._migrate_old_format(data)
                    self._deployed_ids = DeployedSkillIds.model_validate(data)
                except Exception as e:
                    raise ModuleError(f"Error reading {file}: {str(e)}")
        else:
            logger.debug("No skill_ids file found, will create new one.")
            self._deployed_ids = DeployedSkillIds(ids_by_url=[])

    def _migrate_old_format(self, data: dict) -> dict:
        """Migrate old format (url -> ids) to new format (url -> tenant_id -> ids)."""
        for url_entry in data.get("ids_by_url", []):
            if "ids" in url_entry and "ids_by_tenant" not in url_entry:
                logger.info(
                    f"Migrating old skill ID format for {url_entry['url']} to tenant-aware format"
                )
                url_entry["ids_by_tenant"] = [
                    {"tenant_id": "unknown", "ids": url_entry.pop("ids")}
                ]
        return data

    def _find_skill_id(self, skill: ConfigSkill) -> str | None:
        """Find the remote skill ID for a given local skill config."""
        if not self._api_url:
            return None

        for url_ids in self._deployed_ids.ids_by_url:
            if url_ids.url == self._api_url:
                for tenant_ids in url_ids.ids_by_tenant:
                    if tenant_ids.tenant_id == self._tenant_id:
                        for skill_id in tenant_ids.ids:
                            if skill_id.id == skill.id:
                                return skill_id.skill_id
        return None

    def _update_deployed_skill_id(self, skill_id: str, deployed_id: str) -> None:
        """Update the deployed skill ID mapping."""
        if not self._api_url:
            return

        url_entry = None
        for url_ids in self._deployed_ids.ids_by_url:
            if url_ids.url == self._api_url:
                url_entry = url_ids
                break

        if not url_entry:
            url_entry = DeployedSkillUrlIds(url=self._api_url, ids_by_tenant=[])
            self._deployed_ids.ids_by_url.append(url_entry)

        tenant_entry = None
        for tenant_ids in url_entry.ids_by_tenant:
            if tenant_ids.tenant_id == self._tenant_id:
                tenant_entry = tenant_ids
                break

        if not tenant_entry:
            tenant_entry = DeployedSkillTenantIds(tenant_id=self._tenant_id, ids=[])
            url_entry.ids_by_tenant.append(tenant_entry)

        existing_entry = None
        for skill_id_entry in tenant_entry.ids:
            if skill_id_entry.id == skill_id:
                existing_entry = skill_id_entry
                break

        if existing_entry:
            existing_entry.skill_id = deployed_id
        else:
            tenant_entry.ids.append(SkillIds(id=skill_id, skill_id=deployed_id))

    def _store_deployed_skill_id(self, skill: ConfigSkill, deployed_id: str) -> None:
        """Store the deployed skill ID for tracking."""
        self._update_deployed_skill_id(skill.id, deployed_id)

    def _save_deployed_ids(self) -> None:
        """Save the deployed IDs to file."""
        with open(self._deployed_ids_file, "w") as f:
            json.dump(self._deployed_ids.model_dump(), f, indent=2)
