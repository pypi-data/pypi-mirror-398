from bosa_server_plugins.code_interpreter.constant import DATA_FILE_PATH as DATA_FILE_PATH, DEFAULT_TIMEOUT as DEFAULT_TIMEOUT
from pydantic import BaseModel
from typing import Any

class ExecuteCodeRequest(BaseModel):
    """Request model for code execution."""
    code: str
    data_source: list[dict[str, Any]] | None
    timeout: int | None
    additional_packages: list[str] | None
    output_dirs: list[str] | None
    def validate_output_dirs(self) -> ExecuteCodeRequest:
        """Validate output_dirs."""
