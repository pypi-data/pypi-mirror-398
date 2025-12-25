import json
import requests
from pathlib import Path
from typing import Callable, List, Optional
from .request_utils import RequestUtils


class SkillsAPI:
    def __init__(self, base_url: str, headers: dict, retry_strategy: Callable) -> None:
        self._base_url = base_url
        self._headers = headers
        self._retry_strategy = retry_strategy

    def list_all(
        self, search: Optional[str] = None, order_by: Optional[str] = None
    ) -> list[dict]:
        """
        List all global skills from the Scout API.

        Args:
            search (Optional[str]): Optional search query to filter skills
            order_by (Optional[str]): Optional ordering parameter

        Returns:
            list[dict]: List of skill dictionaries containing id, name, description, type, functions_status, etc.

        Raises:
            Exception: If there is an error during the API request.
        """
        params = {}
        if search:
            params["search"] = search
        if order_by:
            params["orderBy"] = order_by

        response, status_code = RequestUtils.get(
            url=f"{self._base_url}/api/skills/global",
            headers=self._headers,
            params=params if params else None,
            retry_strategy=self._retry_strategy,
        )

        if status_code >= 200 and status_code < 300:
            return response if isinstance(response, list) else []
        else:
            error_msg = f"Failed to list skills (status {status_code})"
            if isinstance(response, dict):
                error_detail = response.get("message", "")
                if error_detail:
                    error_msg += f": {error_detail}"
            raise Exception(error_msg)

    def get(self, skill_id: str) -> dict:
        """
        Get a specific global skill by ID.

        Args:
            skill_id (str): The ID of the skill to retrieve

        Returns:
            dict: Skill dictionary containing id, name, description, type, functions_status, etc.

        Raises:
            Exception: If there is an error during the API request or skill not found.
        """
        response, status_code = RequestUtils.get(
            url=f"{self._base_url}/api/skills/global/{skill_id}",
            headers=self._headers,
            retry_strategy=self._retry_strategy,
        )

        if status_code >= 200 and status_code < 300:
            return response
        else:
            error_msg = f"Failed to get skill (status {status_code})"
            if isinstance(response, dict):
                error_detail = response.get("message", "")
                if error_detail:
                    error_msg += f": {error_detail}"
            raise Exception(error_msg)

    def create(
        self,
        name: str,
        description: str,
        package_path: str,
        skill_type: str = "FUNCTIONS",
        usable_in: Optional[List[str]] = None,
    ) -> str:
        """
        Create a new global skill on the Scout API.

        Args:
            name (str): The name of the skill
            description (str): A description of what the skill does
            package_path (str): Local file path to the package zip file
            skill_type (str): The type of skill (default: "FUNCTIONS")
            usable_in (Optional[List[str]]): Where the skill can be used (ASSISTANTS, CONVERSATIONS)

        Returns:
            str: The skill_id of the newly created skill

        Raises:
            Exception: If there is an error during the API request or file upload.
        """
        package_file = Path(package_path)
        if not package_file.exists():
            raise FileNotFoundError(f"Package file not found: {package_path}")

        # Prepare skill metadata
        skill_data: dict = {
            "name": name,
            "description": description,
            "type": skill_type,
        }
        if usable_in is not None:
            skill_data["usable_in"] = usable_in

        with open(package_file, "rb") as f:
            files = {"file": (package_file.name, f, "application/zip")}
            data = {"skill_data": json.dumps(skill_data)}

            # Remove Content-Type header to let requests handle multipart encoding
            local_headers = self._headers.copy()
            local_headers.pop("Content-Type", None)

            response, status_code = RequestUtils.post(
                url=f"{self._base_url}/api/skills/global",
                headers=local_headers,
                data=data,
                files=files,
                retry_strategy=self._retry_strategy,
            )

        if status_code >= 200 and status_code < 300:
            skill_id = response.get("skill_id", "")
            if not skill_id:
                raise Exception("Server did not return a skill_id")
            return skill_id
        else:
            error_msg = f"Failed to create skill (status {status_code})"
            if isinstance(response, dict):
                error_detail = response.get("message", "")
                if error_detail:
                    error_msg += f": {error_detail}"
            raise Exception(error_msg)

    def update(
        self,
        skill_id: str,
        name: str,
        description: str,
        package_path: str,
        skill_type: str = "FUNCTIONS",
        usable_in: Optional[List[str]] = None,
    ) -> None:
        """
        Update an existing global skill on the Scout API.

        Args:
            skill_id (str): The ID of the skill to update
            name (str): The name of the skill
            description (str): A description of what the skill does
            package_path (str): Local file path to the package zip file
            skill_type (str): The type of skill (default: "FUNCTIONS")
            usable_in (Optional[List[str]]): Where the skill can be used (ASSISTANTS, CONVERSATIONS)

        Raises:
            Exception: If there is an error during the API request or file upload.
        """
        package_file = Path(package_path)
        if not package_file.exists():
            raise FileNotFoundError(f"Package file not found: {package_path}")

        # Prepare skill metadata
        skill_data: dict = {
            "name": name,
            "description": description,
            "type": skill_type,
        }
        if usable_in is not None:
            skill_data["usable_in"] = usable_in

        with open(package_file, "rb") as f:
            files = {"file": (package_file.name, f, "application/zip")}
            data = {"skill_data": json.dumps(skill_data)}

            # Remove Content-Type header to let requests handle multipart encoding
            local_headers = self._headers.copy()
            local_headers.pop("Content-Type", None)

            # RequestUtils.put doesn't support files parameter, so use requests directly
            response = requests.put(
                url=f"{self._base_url}/api/skills/global/{skill_id}",
                headers=local_headers,
                data=data,
                files=files,
            )

        if response.status_code < 200 or response.status_code >= 300:
            error_msg = f"Failed to update skill (status {response.status_code})"
            try:
                error_detail = response.json().get("message", "")
                if error_detail:
                    error_msg += f": {error_detail}"
            except Exception:
                pass
            raise Exception(error_msg)
