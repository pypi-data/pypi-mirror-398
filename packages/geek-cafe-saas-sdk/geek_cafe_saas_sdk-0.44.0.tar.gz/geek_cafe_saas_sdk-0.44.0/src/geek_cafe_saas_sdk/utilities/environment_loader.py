"""
Geek Cafe SaaS Services Environment Services.

This module provides utilities for loading and accessing environment variables
used throughout the Geek Cafe SaaS Services application. It includes classes for
loading environment files and accessing specific environment variables in a
consistent manner.
"""

import os
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
from aws_lambda_powertools import Logger


logger = Logger(__name__)

DEBUGGING = os.getenv("DEBUGGING", "false").lower() == "true"


class EnvironmentLoader:
    """Utility class for loading environment variables from files.
    
    This class provides methods to load environment variables from .env files,
    load event files for testing, and search for files in the project directory structure.
    """

    def load_environment(
        self,
        *,
        starting_path: Optional[str] = None,
        file_name: str = ".env.dev",
        override_vars: bool = True,
        raise_error_if_not_found: bool = True,
    ) -> None:
        """Load environment variables from a .env file.
        
        Searches for the specified environment file starting from the given path
        and loads the environment variables from it.
        
        Args:
            starting_path: Path to start searching from. If None, uses the current file's location.
            file_name: Name of the environment file to load (default: ".env.dev").
            override_vars: Whether to override existing environment variables (default: True).
            raise_error_if_not_found: Whether to raise an error if the file is not found (default: True).
            
        Raises:
            RuntimeError: If the environment file is not found and raise_error_if_not_found is True.
        """

        if not starting_path:
            starting_path = __file__

        environment_file: str | None = self.find_file(
            starting_path=starting_path,
            file_name=file_name,
            raise_error_if_not_found=raise_error_if_not_found,
        )

        if environment_file:
            load_dotenv(dotenv_path=environment_file, override=override_vars)

        if DEBUGGING:
            env_vars = os.environ
            logger.debug(f"Loaded environment file: {environment_file}")
            # print(env_vars)

    def load_event_file(self, full_path: str) -> Dict[str, Any]:
        """Load and parse a JSON event file.
        
        Loads a JSON event file and handles common event structures by extracting
        the actual event data from nested 'message' or 'event' fields if present.
        
        Args:
            full_path: The full path to the JSON event file.
            
        Returns:
            The parsed event data as a dictionary.
            
        Raises:
            RuntimeError: If the event file does not exist.
        """
        if not os.path.exists(full_path):
            raise RuntimeError(f"Failed to locate event file: {full_path}")

        event: Dict = {}
        with open(full_path, mode="r", encoding="utf-8") as json_file:
            event = json.load(json_file)

        if "message" in event:
            tmp = event.get("message")
            if isinstance(tmp, Dict):
                event = tmp

        if "event" in event:
            tmp = event.get("event")
            if isinstance(tmp, Dict):
                event = tmp

        return event

    def find_file(
        self, starting_path: str, file_name: str, raise_error_if_not_found: bool = True, max_parent_directories: int = 25
    ) -> Optional[str]:
        """Search for a file in the project directory structure.
        
        Searches for the specified file by traversing up the directory tree
        starting from the given path, up to a maximum number of parent directories.
        
        Args:
            starting_path: Path to start searching from.
            file_name: Name of the file to search for.
            raise_error_if_not_found: Whether to raise an error if the file is not found (default: True).
            max_parent_directories: Maximum number of parent directories to search (default: 25).
            
        Returns:
            The full path to the found file, or None if not found and raise_error_if_not_found is False.
            
        Raises:
            RuntimeError: If the file is not found and raise_error_if_not_found is True.
        """
        parents = max_parent_directories
        starting_path = starting_path or __file__

        paths: List[str] = []
        for parent in range(parents):
            # Check if we have enough parent directories available
            current_path = Path(starting_path)
            if parent >= len(current_path.parents):
                break
            
            path = current_path.parents[parent].absolute()
            print(f"searching: {path}")
            tmp = os.path.join(path, file_name)
            paths.append(tmp)
            if os.path.exists(tmp):
                return tmp

        if raise_error_if_not_found:
            searched_paths = "\n".join(paths)
            raise RuntimeError(
                f"Failed to locate environment file: {file_name} in: \n {searched_paths}"
            )

        return None


