import argparse
import json
import os
import zipfile
from typing import List
import fnmatch
from .base_module import BaseModule
from scoutsdk import scout
from ..config import Config, CONFIG_ASSISTANT_ID
from ..error_handler import (
    ValidationError,
    APIError,
    FileSystemError,
    logger,
)
from scoutsdk.api import ScoutAPI
from scouttypes.constants import SCOUT_CUSTOM_FUNCTION_CONTENT_TYPE

# Variables to extract from custom function classes
SCHEMA_VARIABLES = {"function_name", "description", "parameters", "file_masks"}
FILE_NAME_VARIABLE = "file_name"
CLASS_NAME_VARIABLE = "class_name"


class PkgModule(BaseModule):
    def __init__(self, config: Config) -> None:
        self.config = config

    def get_command(self) -> str:
        return "create-project-package"

    def add_parser(self, subparsers: argparse._SubParsersAction) -> None:
        pkg_parser = subparsers.add_parser(
            self.get_command(), help="Package management commands"
        )
        pkg_parser.add_argument(
            "-s", "--src-path", help="src folder to package", required=True
        )
        pkg_parser.add_argument(
            "-o",
            "--output-path",
            help="output path to save the package",
            required=False,
        )
        pkg_parser.add_argument(
            "-u",
            "--upload",
            action="store_true",
            help="Upload package to Scout assistant after creation",
        )
        pkg_parser.add_argument(
            "-a",
            "--assistant-id",
            help="Assistant ID to upload package to (overrides .env version if set)",
            required=False,
        )
        # Set the default function to handle this command
        pkg_parser.set_defaults(func=self.execute)

    def execute(self, args: argparse.Namespace) -> None:
        pkg_src_path = args.src_path
        if pkg_src_path is None:
            raise ValidationError("src-path argument is required")
        if not os.path.exists(pkg_src_path):
            raise FileSystemError(f"Folder {pkg_src_path} does not exist")

        zip_path = self._get_package_path(pkg_src_path, args.output_path)
        self._generate_package_internal(pkg_src_path, zip_path)
        logger.debug("Package created successfully with functions.json")

        if args.upload:
            self._upload_package(zip_path, args.assistant_id)

    def _upload_package(self, zip_path: str, assistant_id: str | None) -> None:
        scout_api = ScoutAPI()
        assistant_id = assistant_id or self.config.get(CONFIG_ASSISTANT_ID, None)
        if assistant_id is None:
            raise ValidationError("Assistant ID is required when uploading package")

        # delete the file if it exists in the assistant
        try:
            assistant_files = scout_api.assistants.list_files(assistant_id=assistant_id)
        except Exception as e:
            raise APIError(f"Failed to list assistant files: {str(e)}")

        for assistant_file in assistant_files:
            if (
                assistant_file.content_type == SCOUT_CUSTOM_FUNCTION_CONTENT_TYPE
                and assistant_file.filename in zip_path
                and assistant_file.id
            ):
                try:
                    scout_api.assistants.delete_file(
                        assistant_id=assistant_id, file_uid=assistant_file.id
                    )
                    logger.debug(
                        f"File deleted successfully from assistant: {assistant_id}"
                    )
                except Exception as e:
                    raise APIError(f"Error deleting file from assistant: {str(e)}")

        # upload the new file
        try:
            result = scout_api.assistants.upload_file(
                assistant_id=assistant_id, file_path=zip_path
            )
            print(f"File uploaded successfully to assistant: {result.file_id}")
        except Exception as e:
            raise APIError(f"Error uploading file to assistant: {str(e)}")

    def _get_package_path(self, src_path: str, output_path: str | None) -> str:
        """
        Determine the output path for the package zip file.

        Args:
            src_path (str): Source directory path to package
            output_path (str | None): Optional output path for the package

        Returns:
            str: Full path where the zip file should be created
        """
        pkg_folder = os.path.normpath(src_path)
        # Ensure we don't create a package with a dot folder name
        base_name = os.path.basename(pkg_folder)
        if base_name.startswith("."):
            # Remove the dot from the folder name
            base_name = base_name[1:]
            if not base_name:
                # Fallback to a default name if name is empty after removing dot
                base_name = "package"
        pkg_name = base_name + ".zip"

        if output_path:
            if not os.path.exists(output_path):
                raise FileSystemError(f"Output directory {output_path} does not exist")
            return os.path.join(output_path, pkg_name)

        return os.path.join(os.path.dirname(pkg_folder), pkg_name)

    def _read_pkgignore(self, pkg_src_path: str) -> List[str]:
        """
        Read the .pkgignore file if it exists and return the patterns.
        Each line in the file is treated as a pattern.

        Args:
            pkg_src_path (str): Source directory path

        Returns:
            List[str]: List of patterns to ignore
        """
        pkgignore_path = os.path.join(pkg_src_path, ".pkgignore")
        patterns = []

        if os.path.exists(pkgignore_path):
            with open(pkgignore_path, "r") as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith("#"):
                        patterns.append(line)
            logger.debug(f"Loaded {len(patterns)} patterns from .pkgignore")

        return patterns

    def _is_ignored(self, path: str, base_path: str, patterns: List[str]) -> bool:
        """
        Check if a path should be ignored based on the patterns.

        Args:
            path (str): Path to check
            base_path (str): Base directory path
            patterns (List[str]): List of patterns to check against

        Returns:
            bool: True if the path should be ignored, False otherwise
        """

        # Get relative path for pattern matching
        rel_path = os.path.relpath(path, base_path)

        for pattern in patterns:
            if fnmatch.fnmatch(rel_path, pattern):
                return True
            # Handle directory wildcards (pattern ending with /)
            if pattern.endswith("/") and os.path.isdir(path):
                dir_pattern = pattern.rstrip("/")
                if fnmatch.fnmatch(os.path.basename(path), dir_pattern):
                    return True

        return False

    def generate_package(self, pkg_src_path: str, zip_path: str) -> None:
        if not os.path.exists(pkg_src_path):
            raise FileSystemError(
                f"Source package folder {pkg_src_path} does not exist"
            )

        self._generate_package_internal(pkg_src_path, zip_path)

    def _generate_package_internal(self, pkg_src_path: str, zip_path: str) -> None:
        ignore_patterns = self._read_pkgignore(pkg_src_path)
        all_files = scout.list_project_files(pkg_src_path, ignore_patterns)

        zip_file_name = os.path.basename(zip_path)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in all_files:
                arcname = os.path.relpath(file_path, pkg_src_path)
                if os.path.basename(file_path) != zip_file_name:
                    zipf.write(file_path, arcname)

            scout._set_context(self._get_package_placeholder_context())
            scout.load_python_files(all_files)
            scout._set_context({})
            functions_json = scout.project_json_definition
            zipf.writestr("functions.json", json.dumps(functions_json, indent=2))

    def _get_package_placeholder_context(self) -> dict:
        return {
            "SCOUT_API_URL": "PACKAGE_PLACEHOLDER_SCOUT_API_URL",
            "SCOUT_API_ACCESS_TOKEN": "PACKAGE_PLACEHOLDER_SCOUT_API_ACCESS_TOKEN",
        }
