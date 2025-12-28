from boto3_assist.environment_services.environment_loader import EnvironmentLoader
from typing import Optional, IO, Union
from pathlib import Path
import os

StrPath = Union[str, "os.PathLike[str]"]


def load_environment(*, environment_file: str | None = None) -> None:
    """Load environment variables from a file."""
    loader = EnvironmentLoader()
    
    if environment_file is None:
        print("No environment file specified, skipping load.")
        return
    
    start_path = os.path.dirname(os.path.abspath(__file__))
    file_name = os.path.basename(environment_file)
    loader.load_environment_file(
        starting_path=start_path,
        file_name=file_name,
        path=environment_file,
        raise_error_if_not_found=True,
    )
