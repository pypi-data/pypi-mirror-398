import json
import os
import fnmatch
import functools
import inspect
from typing import Callable, Optional, Any
from pydantic import create_model, Field, BaseModel
from jsonschema import validate
from scouttypes.document_chunker import AbstractDocumentChunker
import sys
import importlib


class ScoutFunctionDecorator:
    _context: dict
    registered_functions: dict[str, Any]
    registered_document_chunker: dict[str, Any]
    registered_webhooks: dict[str, Any]

    def __init__(self, description: Optional[str] = None):
        self.description = description
        self._context = {}
        self.registered_functions = {}
        self.registered_document_chunker = {}
        self.registered_webhooks = {}

    def create_pydantic(self, func: Callable) -> BaseModel:
        func_name = func.__name__
        signature = inspect.signature(func)
        annotations = {}

        for param_name, param in signature.parameters.items():
            if param_name == "self":
                continue
            # Check if description exists for param

            # If the default is already a Field object, use it directly
            if (
                param.default is not None
                and hasattr(param.default, "__class__")
                and param.default.__class__.__name__ == "FieldInfo"
            ):
                annotations[param_name] = (param.annotation, param.default)
            else:
                # Extract description if it exists
                desc = (
                    param.default.description
                    if (
                        param.default is not None
                        and hasattr(param.default, "description")
                    )
                    else None
                )
                annotations[param_name] = (param.annotation, Field(description=desc))

        # Create pydantic model for parameter
        params_model = create_model(f"{func_name}Parameters", **annotations)  # type: ignore
        return params_model

    @property
    def project_json_definition(self) -> dict:
        return {
            "functions": [
                {
                    "file_masks": func.file_masks,
                    "description": func.description,
                    "parameters": func.parameters,
                    "external_services": func.external_services,
                    "function_name": key,
                    "is_async": func.is_async if hasattr(func, "is_async") else False,
                    "is_handoff": func.is_handoff
                    if hasattr(func, "is_handoff")
                    else False,
                    "supports_progress": func.supports_progress,
                }
                for key, func in scout.registered_functions.items()
            ],
            "document_chunkers": [
                {"class_name": key, "priority": value.priority}
                for key, value in scout.registered_document_chunker.items()
            ],
            "webhooks": [
                {
                    "function_name": key,
                    "path": func.path,
                    "verification_signature_header_key": func.verification_signature_header_key,
                    "assistant_secret_variable_key": func.assistant_secret_variable_key,
                }
                for key, func in scout.registered_webhooks.items()
            ],
        }

    def _create_function_wrapper(
        self,
        func: Callable,
        description: Optional[str],
        file_masks: Optional[list[str]],
        external_services: Optional[list[str]],
        is_async: bool = False,
        is_handoff: bool = False,
        supports_progress: bool = False,
    ) -> Callable:
        func_name = func.__name__

        # Create pydantic model for parameter
        params_model = self.create_pydantic(func)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        # Write metadata
        wrapper.function_name = func_name  # type: ignore
        wrapper.description = description or func.__doc__  # type: ignore
        wrapper.parameters = params_model.model_json_schema()  # type: ignore
        wrapper.file_masks = file_masks  # type: ignore
        wrapper.external_services = external_services  # type: ignore
        wrapper.is_async = is_async  # type: ignore
        wrapper.is_handoff = is_handoff  # type: ignore
        wrapper.supports_progress = supports_progress  # type: ignore

        self.registered_functions[func_name] = wrapper
        return wrapper

    def function(
        self,
        description: Optional[str] = None,
        file_masks: Optional[list[str]] = None,
        external_services: Optional[list[str]] = None,
        is_handoff: bool = False,
        supports_progress: bool = False,
    ) -> Callable[[Callable], Callable]:
        def decorator(func: Callable) -> Callable:
            return self._create_function_wrapper(
                func=func,
                description=description,
                file_masks=file_masks,
                external_services=external_services,
                is_handoff=is_handoff,
                supports_progress=supports_progress,
            )

        return decorator

    def async_function(
        self,
        description: Optional[str] = None,
        file_masks: Optional[list[str]] = None,
        external_services: Optional[list[str]] = None,
        is_handoff: bool = False,
        supports_progress: bool = False,
    ) -> Callable[[Callable], Callable]:
        def decorator(func: Callable) -> Callable:
            return self._create_function_wrapper(
                func,
                description,
                file_masks,
                external_services,
                is_async=True,
                is_handoff=is_handoff,
                supports_progress=supports_progress,
            )

        return decorator

    def document_chunker(self, priority: int = 100) -> Callable[[type], type]:
        def decorator(cls: type) -> type:
            if not issubclass(cls, AbstractDocumentChunker):
                raise TypeError(
                    f"Document chunker class {cls.__name__} must inherit AbstractDocumentChunker"
                )

            for method_name in ["supports_document", "process_document"]:
                method = getattr(cls, method_name, None)
                if method is None or getattr(method, "__isabstractmethod__", False):
                    raise TypeError(
                        f"Class {cls.__name__} must implement {method_name}"
                    )

            @functools.wraps(cls)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                return cls(*args, **kwargs)

            wrapper.priority = priority  # type: ignore

            self.registered_document_chunker[cls.__name__] = wrapper

            return cls

        return decorator

    def webhook(
        self,
        verification_signature_header_key: str,
        assistant_secret_variable_key: Optional[str] = None,
        path: Optional[str] = None,
    ) -> Callable[[Callable], Callable]:
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                return func(*args, **kwargs)

            webhook_path = path or func.__name__
            if webhook_path.startswith("/"):
                webhook_path = webhook_path[1:]
            params_model = self.create_pydantic(func)

            signature = inspect.signature(func)
            if (
                len(signature.parameters) != 2
                or signature.parameters.get("headers") is None
                or signature.parameters.get("payload") is None
                or signature.parameters["headers"].annotation is not dict
                or signature.parameters["payload"].annotation is not str
            ):
                raise TypeError(
                    f"The function {func.__name__} must have exactly `headers: dict` and `payload: str` parameters."
                )

            wrapper.path = webhook_path  # type: ignore
            wrapper.verification_signature_header_key = (  # type: ignore
                verification_signature_header_key
            )
            wrapper.parameters = params_model.model_json_schema()  # type: ignore
            wrapper.assistant_secret_variable_key = (  # type: ignore
                assistant_secret_variable_key or f"{func.__name__}_secret"
            )
            self.registered_webhooks[func.__name__] = wrapper

            return func

        return decorator

    def _call_custom_function_with_registry(
        self,
        function_to_call_or_string: str | Callable,
        parameters_input: dict,
        registry: dict[str, Any],
    ) -> Any:
        if isinstance(function_to_call_or_string, str):
            function_to_call = registry[function_to_call_or_string]
        else:
            function_to_call = function_to_call_or_string

        validate(instance=parameters_input, schema=function_to_call.parameters)

        model_pydantic = self.create_pydantic(function_to_call)

        validated_parameters = model_pydantic.model_validate(parameters_input)

        parameters = {k: v for k, v in validated_parameters.__dict__.items()}

        return function_to_call(**parameters)

    def call_custom_function(
        self, function_to_call_or_string: str | Callable, parameters_input: dict
    ) -> Any:
        return self._call_custom_function_with_registry(
            function_to_call_or_string, parameters_input, self.registered_functions
        )

    def call_custom_webhook(
        self, function_to_call_or_string: str | Callable, parameters_input: dict
    ) -> Any:
        return self._call_custom_function_with_registry(
            function_to_call_or_string, parameters_input, self.registered_webhooks
        )

    def file_match_ignore_pattern(
        self, path: str, base_path: str, ignore_patterns: list[str]
    ) -> bool:
        # Get relative path for pattern matching
        rel_path = os.path.relpath(path, base_path)

        for pattern in ignore_patterns:
            if fnmatch.fnmatch(rel_path, pattern):
                return True
            # Handle directory wildcards (pattern ending with /)
            if pattern.endswith("/") and os.path.isdir(path):
                dir_pattern = pattern.rstrip("/")
                if fnmatch.fnmatch(os.path.basename(path), dir_pattern):
                    return True

        return False

    def list_project_files(
        self, project_directory: str, ignore_patterns: Optional[list[str]] = None
    ) -> list[str]:
        if ignore_patterns is None:
            ignore_patterns = [".venv", "__pycache__"]

        all_non_ignored_files = []
        for root, dirs, files in os.walk(project_directory, followlinks=True):
            dirs[:] = [
                d
                for d in dirs
                if not scout.file_match_ignore_pattern(
                    os.path.join(root, d), project_directory, ignore_patterns
                )
            ]

            for file in files:
                file_path = os.path.join(root, file)
                if (
                    scout.file_match_ignore_pattern(
                        file_path, project_directory, ignore_patterns
                    )
                    or file == ".pkgignore"
                ):
                    continue

                all_non_ignored_files.append(file_path)

        return all_non_ignored_files

    def load_python_project(self, project_directory: str) -> None:
        self.load_python_files(self.list_project_files(project_directory))

    def load_python_files(self, file_paths: list[str]) -> None:
        for file_path in file_paths:
            if file_path.endswith(".py"):
                module_name = os.path.basename(file_path).rsplit(".", 1)[0]
                module_path = file_path

                project_dir = os.path.dirname(os.path.abspath(file_path))
                sys.path.insert(0, project_dir)

                try:
                    spec = importlib.util.spec_from_file_location(
                        module_name, module_path
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                except SyntaxError as e:
                    error_msg = (
                        f"❌ Syntax Error in '{os.path.basename(file_path)}'\n"
                        f"   File: {file_path}\n"
                        f"   Line: {e.lineno}\n"
                        f"   Error: {e.msg}\n"
                    )
                    if e.text:
                        error_msg += f"   Code: {e.text.strip()}\n"
                    error_msg += (
                        f"\n💡 Fix the syntax error on line {e.lineno} and try again."
                    )
                    raise SyntaxError(error_msg) from e
                except ModuleNotFoundError as e:
                    missing_module = str(e).split("'")[1] if "'" in str(e) else str(e)
                    error_msg = (
                        f"❌ Module Not Found in '{os.path.basename(file_path)}'\n"
                        f"   File: {file_path}\n"
                        f"   Missing module: {missing_module}\n"
                        f"\n💡 Install the required package with: pip install {missing_module}\n"
                        f"   Or add it to your requirements.txt file."
                    )
                    raise ModuleNotFoundError(error_msg) from e
                except ImportError as e:
                    error_msg = (
                        f"❌ Import Error in '{os.path.basename(file_path)}'\n"
                        f"   File: {file_path}\n"
                        f"   Error: {str(e)}\n"
                        f"\n💡 Check your import statements and ensure all dependencies are installed."
                    )
                    raise ImportError(error_msg) from e
                except AttributeError as e:
                    error_msg = (
                        f"❌ Attribute Error in '{os.path.basename(file_path)}'\n"
                        f"   File: {file_path}\n"
                        f"   Error: {str(e)}\n"
                        f"\n💡 Check that all referenced attributes and methods exist."
                    )
                    raise AttributeError(error_msg) from e
                except Exception as e:
                    error_msg = (
                        f"❌ Error loading '{os.path.basename(file_path)}'\n"
                        f"   File: {file_path}\n"
                        f"   Error type: {e.__class__.__name__}\n"
                        f"   Error: {str(e)}\n"
                        f"\n💡 Review the error message above and fix the issue in your code."
                    )
                    raise type(e)(error_msg) from e
                finally:
                    if project_dir in sys.path:
                        sys.path.remove(project_dir)

    def _set_context(self, context: dict) -> None:
        self._context = context

    @property
    def context(self) -> dict:
        if len(self._context.keys()) == 0:
            # First check for SCOUT_PROFILE environment variable
            scout_profile = os.environ.get("SCOUT_PROFILE")
            if scout_profile is not None:
                # Look for profile file in ~/.scoutprofiles/ directory
                home_dir = os.path.expanduser("~")
                profiles_dir = os.path.join(home_dir, ".scoutprofiles")
                profile_file_path = os.path.join(profiles_dir, f"{scout_profile}.json")

                if os.path.exists(profile_file_path):
                    try:
                        print(
                            f"Loading context from profile {scout_profile} ({profile_file_path})"
                        )
                        with open(profile_file_path, "r") as f:
                            self._context = json.load(f)
                        self._add_env_overrides()
                        return self._context
                    except Exception as e:
                        raise Exception(
                            f"Unable to load scout context from profile {scout_profile} at {profile_file_path}: {e}"
                        )
                else:
                    raise Exception(
                        f"Scout profile '{scout_profile}' not found at {profile_file_path}"
                    )

            # Try to load from scout_context.json file in current directory
            context_file_path = os.path.join(os.getcwd(), "scout_context.json")
            if os.path.exists(context_file_path):
                try:
                    with open(context_file_path, "r") as f:
                        self._context = json.load(f)
                    self._add_env_overrides()
                    return self._context
                except Exception as e:
                    print(
                        f"Unable to load scout context from file {context_file_path}",
                        e,
                    )

            # Try environment variable
            scout_context_from_env = os.environ.get("SCOUT_CONTEXT")
            if scout_context_from_env is not None:
                try:
                    self._context = json.loads(scout_context_from_env)
                    self._add_env_overrides()
                    return self._context
                except Exception as e:
                    print("Unable to load scout context from environment", e)

            # Default empty context
            print("SCOUT_CONTEXT is empty")
            self._context = {}
            self._add_env_overrides()

        return self._context

    def _add_env_overrides(self) -> None:
        if os.environ.get("SCOUT_API_URL") is not None:
            self._context["SCOUT_API_URL"] = os.environ.get("SCOUT_API_URL")
        if os.environ.get("SCOUT_API_ACCESS_TOKEN") is not None:
            self._context["SCOUT_API_ACCESS_TOKEN"] = os.environ.get(
                "SCOUT_API_ACCESS_TOKEN"
            )
        if os.environ.get("SCOUT_ASSISTANT_ID") is not None:
            self._context["SCOUT_ASSISTANT_ID"] = os.environ.get("SCOUT_ASSISTANT_ID")


scout = ScoutFunctionDecorator()
