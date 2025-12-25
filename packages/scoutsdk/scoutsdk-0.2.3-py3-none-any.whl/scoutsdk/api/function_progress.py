from enum import Enum
import json
import tempfile
from typing import Any, Optional
import typing
from pydantic import BaseModel
from .project_helpers import scout
from scouttypes import upload_file, SignedUploadUrlResponse
from threading import Timer
from contextlib import contextmanager
from typing import Generator


class StepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ProgressStep(BaseModel):
    status: StepStatus
    description: str
    error_data: Optional[str] = None

    def __init__(self, description: str) -> None:
        super().__init__(
            status=StepStatus.PENDING, description=description, error_data=None
        )


UPLOAD_DEBOUNCE_TIME = 0.3


class FunctionProgress:
    _debounce_timer: Optional[Timer] = None

    def upload_progress(self, value: dict) -> None:
        if self._debounce_timer:
            self._debounce_timer.cancel()
        self._debounce_timer = Timer(
            UPLOAD_DEBOUNCE_TIME, self._update_progress_debounced, [value]
        )
        self._debounce_timer.start()

    def _update_progress_debounced(self, progress_value: dict) -> None:
        signed_upload_dictionary = scout.context.get(
            "SCOUT_FUNCTION_PROGRESS_UPLOAD_URL"
        )
        if not signed_upload_dictionary:
            print("Dev mode: Updating progress")
            print(json.dumps(progress_value, indent=2))
            return

        progress_json = json.dumps(progress_value)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=True
        ) as temp_file:
            temp_file.write(progress_json)
            temp_file.flush()
            signed_upload_response = SignedUploadUrlResponse.model_validate(
                signed_upload_dictionary
            )
            upload_file(signed_upload_response, temp_file.name, "not_used.json")


class StepsFunctionProgress(FunctionProgress):
    _progress_items: dict[str, ProgressStep]

    def __init__(self) -> None:
        super().__init__()
        self._progress_items = {}

    def __enter__(self) -> "StepsFunctionProgress":
        return self

    def __exit__(
        self, exc_type: Any, exc_val: Any, exc_tb: Any
    ) -> typing.Literal[False]:
        return False  # Don't suppress exceptions

    def add_step(self, step_id: str, description: str) -> "StepsFunctionProgress":
        """Add a step to the progress tracker. Returns self for chaining."""
        self._progress_items[step_id] = ProgressStep(description=description)
        self._upload_all_items()
        return self

    @contextmanager
    def step(self, step_id: str) -> Generator[ProgressStep, None, None]:
        """
        Context manager for executing a step.
        Automatically marks as IN_PROGRESS on enter, COMPLETED on exit,
        and FAILED if an exception occurs.
        """
        if step_id not in self._progress_items:
            raise ValueError(
                f"Step '{step_id}' not found. Did you forget to add_step()?"
            )

        progress_step = self._progress_items[step_id]

        # Mark as IN_PROGRESS
        progress_step.status = StepStatus.IN_PROGRESS
        self._upload_all_items()

        try:
            yield progress_step
            # If no exception, mark as COMPLETED
            progress_step.status = StepStatus.COMPLETED
            self._upload_all_items()
        except Exception as e:
            # If exception, mark as FAILED
            progress_step.status = StepStatus.FAILED
            progress_step.error_data = str(e)
            self._upload_all_items()
            raise  # Re-raise the exception

    def _upload_all_items(self) -> None:
        """Upload progress to server"""
        items_data = [item.model_dump() for item in self._progress_items.values()]
        self.upload_progress({"items": items_data})


class HtmlFunctionProgress(FunctionProgress):
    _html: str

    def __init__(self, initial_value: str) -> None:
        self._html = initial_value
        self.upload_progress({"html": self._html})

    def append(self, html_str: str) -> None:
        self._html += html_str
        self.upload_progress({"html": self._html})
