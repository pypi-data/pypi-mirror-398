import argparse
import shutil
from pathlib import Path
from typing import List, Optional

from .sync_module import SyncModule

from .base_module import BaseModule
from ..config import Config
from ..error_handler import ValidationError, logger
from ..utils import get_data_path
from ...api import ScoutAPI


class AssistantsModule(BaseModule):
    def __init__(self, config: Config) -> None:
        self.config = config

    def get_command(self) -> str:
        return "assistants"

    def add_parser(self, subparsers: argparse._SubParsersAction) -> None:
        assistants_parser = subparsers.add_parser(
            self.get_command(), help="Manage assistants"
        )

        # Create subparsers for assistants commands
        assistants_subparsers = assistants_parser.add_subparsers(
            dest="assistants_command", required=True
        )

        # assistants init
        init_parser = assistants_subparsers.add_parser(
            "init", help="Create an assistant.json from template"
        )
        init_parser.add_argument(
            "-d",
            "--directory",
            type=str,
            default=".",
            help="Directory to create the assistant files in (default: current directory)",
        )
        init_parser.add_argument(
            "-t",
            "--template",
            type=str,
            choices=[
                "basic",
                "with-function",
                "with-micro-app",
                "with-micro-app-and-function",
            ],
            help="Template type - skips interactive prompt",
        )
        init_parser.add_argument(
            "-n",
            "--name",
            type=str,
            help="Assistant name - skips interactive prompt",
        )
        init_parser.add_argument(
            "--function-template",
            type=str,
            choices=["function", "chunker", "webhook"],
            help="Template for function (required with with-function or with-micro-app-and-function)",
        )
        init_parser.add_argument(
            "--function-name",
            type=str,
            help="Name for the function (required with with-function or with-micro-app-and-function)",
        )
        init_parser.add_argument(
            "--micro-app-template",
            type=str,
            choices=["basic", "advanced"],
            help="Template for micro-app (required with with-micro-app or with-micro-app-and-function)",
        )
        init_parser.set_defaults(func=self._init_assistant)

        # assistants list
        list_parser = assistants_subparsers.add_parser(
            "list", help="List all assistants"
        )
        list_parser.set_defaults(func=self._list_assistants)

        # assistants synchronize
        sync_parser = assistants_subparsers.add_parser(
            "synchronize", help="Synchronize assistants from config file"
        )
        sync_parser.add_argument(
            "-f", "--file", type=str, required=True, help="Path to assistants.json file"
        )
        sync_parser.add_argument(
            "--force", action="store_true", help="Force overwrite assistant files"
        )
        sync_parser.add_argument(
            "-o",
            "--overwrite",
            action="store_true",
            help="Overwrite the config file with new assistant IDs (useful for first-time creation)",
        )
        sync_parser.set_defaults(func=self._synchronize_assistants)

    def execute(self, args: argparse.Namespace) -> None:
        """Execute the assistants command."""
        # This will be called by the specific subcommand
        args.func(args)

    def _init_assistant(self, args: argparse.Namespace) -> None:
        """Initialize a new assistant.json from template."""
        template = getattr(args, "template", None)
        name = getattr(args, "name", None)
        function_template = getattr(args, "function_template", None)
        function_name = getattr(args, "function_name", None)
        micro_app_template = getattr(args, "micro_app_template", None)

        is_non_interactive = template and name

        if is_non_interactive:
            assert template is not None and name is not None
            template_to_choice = {
                "basic": "1",
                "with-function": "2",
                "with-micro-app": "3",
                "with-micro-app-and-function": "4",
            }
            choice: str = template_to_choice[template]
            assistant_name: str = name

            if template in ["with-function", "with-micro-app-and-function"]:
                if not function_template or not function_name:
                    raise ValidationError(
                        f"--function-template and --function-name are required for template '{template}'"
                    )
            if template in ["with-micro-app", "with-micro-app-and-function"]:
                if not micro_app_template:
                    raise ValidationError(
                        f"--micro-app-template is required for template '{template}'"
                    )
        elif template or name:
            raise ValidationError(
                "Both --template and --name must be provided for non-interactive mode"
            )
        else:
            print("\nChoose an assistant template:")
            print("1. basic - Basic assistant template")
            print(
                "2. assistant with function - Assistant template with custom function"
            )
            print("3. assistant with micro-app - Assistant template with micro-app")
            print(
                "4. assistant with micro-app and function - Assistant with both micro-app and custom function"
            )

            choice = input("Enter your choice (1-4): ").strip()

            if choice not in ["1", "2", "3", "4", ""]:
                raise ValidationError("Invalid choice. Please select 1, 2, 3, or 4.")

            if not choice:
                choice = "1"

            assistant_name = input("\nEnter assistant name: ").strip()
            if not assistant_name:
                raise ValidationError("Assistant name cannot be empty")

        # Create target directory if it doesn't exist
        target_dir = Path(args.directory)
        target_dir.mkdir(exist_ok=True)

        if choice == "1":
            self._create_basic_assistant(assistant_name, target_dir)
        elif choice == "2":
            self._create_assistant_with_functions(
                assistant_name,
                target_dir,
                function_template=function_template,
                function_name=function_name,
            )
        elif choice == "3":
            self._create_assistant_with_micro_app(
                assistant_name, target_dir, micro_app_template=micro_app_template
            )
        else:  # choice == "4"
            self._create_assistant_with_micro_app_and_function(
                assistant_name,
                target_dir,
                function_template=function_template,
                function_name=function_name,
                micro_app_template=micro_app_template,
            )

    def _create_basic_assistant(self, assistant_name: str, target_dir: Path) -> None:
        """Create a basic assistant template."""
        # Load template
        template_path = get_data_path("assistants", "basic", "assistants_template.json")
        if not template_path.exists():
            raise ValidationError("Basic assistant template file not found")

        with open(template_path, "r") as f:
            content = f.read()

        # Replace placeholders in the template
        assistant_id = assistant_name.lower().replace(" ", "_").replace("-", "_")
        content = content.replace("{ASSISTANT_NAME}", assistant_name)
        content = content.replace("{ASSISTANT_IDENTIFIER}", assistant_id)

        # Write to target directory as assistants.json
        output_file = target_dir / "assistants.json"
        with open(output_file, "w") as f:
            f.write(content)

        # Copy supporting template files to target directory
        self._copy_assistant_template_files(target_dir)

        print(
            f"Created basic assistant '{assistant_name}' with config file '{output_file}'"
        )

    def _create_assistant_with_micro_app(
        self,
        assistant_name: str,
        target_dir: Path,
        micro_app_template: Optional[str] = None,
    ) -> None:
        """Create an assistant template with micro-app."""
        from .apps_module import AppsModule

        apps_module = AppsModule(self.config)
        micro_app_type = apps_module.create_micro_app_for_assistant(
            target_dir, template=micro_app_template
        )

        self._create_micro_app_assistant_template(assistant_name, target_dir)

        print(
            f"Created assistant '{assistant_name}' with {micro_app_type} micro-app in '{target_dir}'"
        )

    def _create_assistant_with_functions(
        self,
        assistant_name: str,
        target_dir: Path,
        function_template: Optional[str] = None,
        function_name: Optional[str] = None,
    ) -> None:
        """Create an assistant template with functions."""
        functions_dir = target_dir / "functions"
        functions_dir.mkdir(exist_ok=True)

        created_function_name = self._create_function_for_assistant(
            functions_dir,
            function_template=function_template,
            function_name=function_name,
        )

        self._create_assistant_template_with_functions(
            assistant_name, target_dir, created_function_name
        )

        print(
            f"Created assistant '{assistant_name}' with function '{created_function_name}' in '{target_dir}'"
        )

    def _create_function_for_assistant(
        self,
        functions_dir: Path,
        function_template: Optional[str] = None,
        function_name: Optional[str] = None,
    ) -> str:
        """Create a function for the assistant (reusing function creation logic)."""
        from .functions_module import FunctionsModule

        functions_module = FunctionsModule(self.config)

        if function_template and function_name:
            return functions_module.init_function_non_interactive(
                directory=str(functions_dir),
                template=function_template,
                name=function_name,
            )

        import argparse
        import builtins

        mock_args = argparse.Namespace()
        mock_args.directory = str(functions_dir)

        created_function_name: List[Optional[str]] = [None]
        original_input = builtins.input

        def capture_input(prompt: str) -> str:
            result = original_input(prompt)
            if any(
                keyword in prompt.lower()
                for keyword in [
                    "function name",
                    "document chunker name",
                    "webhook name",
                ]
            ):
                created_function_name[0] = functions_module._normalize_function_name(
                    result
                )
            return result

        try:
            builtins.input = capture_input  # type: ignore[assignment]
            functions_module._init_function(mock_args)
        finally:
            builtins.input = original_input

        return created_function_name[0] or "unknown_function"

    def _create_assistant_with_micro_app_and_function(
        self,
        assistant_name: str,
        target_dir: Path,
        function_template: Optional[str] = None,
        function_name: Optional[str] = None,
        micro_app_template: Optional[str] = None,
    ) -> None:
        """Create an assistant template with both micro-app and custom function."""
        functions_dir = target_dir / "functions"
        functions_dir.mkdir(exist_ok=True)

        created_function_name = self._create_function_for_assistant(
            functions_dir,
            function_template=function_template,
            function_name=function_name,
        )

        from .apps_module import AppsModule

        apps_module = AppsModule(self.config)
        micro_app_type = apps_module.create_micro_app_for_assistant(
            target_dir, template=micro_app_template
        )

        self._create_assistant_template_with_micro_app_and_function(
            assistant_name, target_dir, created_function_name
        )

        print(
            f"Created assistant '{assistant_name}' with function '{created_function_name}' and {micro_app_type} micro-app in '{target_dir}'"
        )

    def _create_assistant_template_with_functions(
        self, assistant_name: str, target_dir: Path, function_name: str
    ) -> None:
        """Create assistant template that includes function configuration."""
        assistant_id = assistant_name.lower().replace(" ", "_").replace("-", "_")

        template_path = get_data_path(
            "assistants", "with-function", "assistants_template.json"
        )
        if not template_path.exists():
            raise ValidationError("Advanced assistant template file not found")

        with open(template_path, "r") as f:
            template_content = f.read()

        # Replace placeholders in the template
        assistant_id = assistant_name.lower().replace(" ", "_").replace("-", "_")
        template_content = template_content.replace("{ASSISTANT_NAME}", assistant_name)
        template_content = template_content.replace(
            "{ASSISTANT_IDENTIFIER}", assistant_id
        )
        template_content = template_content.replace("{FUNCTION_NAME}", function_name)

        # Write to target directory as assistants.json
        output_file = target_dir / "assistants.json"
        with open(output_file, "w") as f:
            f.write(template_content)

        # Copy avatar file
        self._copy_assistant_template_files(target_dir)

    def _normalize_function_name(self, name: str) -> str:
        """Normalize function name to lowercase with underscores."""
        from ..utils import normalize_snake_case_name

        return normalize_snake_case_name(name, default="custom_function")

    def _copy_assistant_template_files(self, target_dir: Path) -> None:
        """Copy supporting template files to target directory."""
        # Define source and destination paths
        assistants_data_path = get_data_path("assistants", "with-function")

        # For basic template, only copy avatar.jpeg
        avatar_src = assistants_data_path / "avatar.jpeg"
        avatar_dest = target_dir / "avatar.jpeg"

        if avatar_src.exists() and not avatar_dest.exists():
            shutil.copy2(avatar_src, avatar_dest)
        else:
            logger.warning(f"Avatar template file not found: {avatar_src}")

    def _list_assistants(self, args: argparse.Namespace) -> None:
        """List all assistants."""
        try:
            scout_api = ScoutAPI()
            assistants = scout_api.assistants.list_all()

            if not assistants:
                print("No assistants found")
                return

            print(f"Found {len(assistants)} assistants:")
            for assistant in assistants:
                print(f"  - {assistant.name} (ID: {assistant.id})")

        except Exception as e:
            raise ValidationError(f"Failed to list assistants: {str(e)}")

    def _synchronize_assistants(self, args: argparse.Namespace) -> None:
        """Synchronize assistants from config file."""
        # Import and use existing sync functionality
        from .pkg_module import PkgModule

        pkg_module = PkgModule(config=self.config)
        sync_module = SyncModule(config=self.config, pkg_module=pkg_module)

        # Create args compatible with existing sync module
        sync_args = argparse.Namespace()
        sync_args.config = args.file
        sync_args.force = getattr(args, "force", False)

        sync_module.execute(sync_args)

    def _create_micro_app_assistant_template(
        self, assistant_name: str, target_dir: Path
    ) -> None:
        """Create assistant template with micro-app configuration."""
        # Load micro-app assistant template
        template_path = get_data_path(
            "assistants", "with-micro-app", "assistants_template.json"
        )
        if not template_path.exists():
            raise ValidationError("Micro-app assistant template file not found")

        with open(template_path, "r") as f:
            content = f.read()

        # Replace placeholders in the template
        assistant_id = assistant_name.lower().replace(" ", "_").replace("-", "_")
        content = content.replace("{ASSISTANT_NAME}", assistant_name)
        content = content.replace("{ASSISTANT_IDENTIFIER}", assistant_id)

        # Write to target directory as assistants.json
        output_file = target_dir / "assistants.json"
        with open(output_file, "w") as f:
            f.write(content)

        # Copy avatar and supporting files
        self._copy_assistant_template_files(target_dir)

    def _create_assistant_template_with_micro_app_and_function(
        self, assistant_name: str, target_dir: Path, function_name: str
    ) -> None:
        """Create assistant template with both micro-app and function."""
        # Load the with-micro-app-and-function template
        template_path = get_data_path(
            "assistants", "with-micro-app-and-function", "assistants_template.json"
        )
        if not template_path.exists():
            raise ValidationError(
                "Assistant template with micro-app and function not found"
            )

        with open(template_path, "r") as f:
            content = f.read()

        # Replace placeholders in the template
        assistant_id = assistant_name.lower().replace(" ", "_").replace("-", "_")
        content = content.replace("{ASSISTANT_NAME}", assistant_name)
        content = content.replace("{ASSISTANT_IDENTIFIER}", assistant_id)
        content = content.replace("{FUNCTION_NAME}", function_name)

        # Write to target directory as assistants.json
        output_file = target_dir / "assistants.json"
        with open(output_file, "w") as f:
            f.write(content)

        # Copy avatar and supporting files
        self._copy_assistant_template_files(target_dir)
