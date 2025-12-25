# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
import os
from importlib.metadata import distributions
from pathlib import Path
from platform import python_version
from typing import Dict, List, Optional

# Core Source imports
from core_exceptions.core import ElementNotFoundException

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = [
    "retrieve_python_version",
    "retrieve_libraries",
    "retrieve_library_version",
    "read_requirements_file",
    "read_multiple_requirements_files",
    "get_requirements_from_dir",
]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                             Requirements file utilities                                              #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def retrieve_python_version() -> str:
    """
    Returns the Python version as string 'major.minor.patchlevel.
    """
    return python_version()


def retrieve_libraries() -> Dict[str, str]:
    """
    Mapping of the installed packages and their version.
    """
    return {req.name: req.version for req in distributions()}


def retrieve_library_version(name: str) -> Optional[str]:
    """Returns the installed version of the indicated dependency.

    Args:
        name (str): Name of the library from which you want to obtain the installed version

    Returns:
        version (Optional[str]): Installed version.

    """
    return retrieve_libraries().get(name)


def read_requirements_file(file_path: Path) -> List[str]:
    """Read a requirements file and return a list with the dependencies.

    Args:
        file_path (Path): Requirements file path.

    Returns:
        dependencies (List[str]): Dependencies list.

    """
    if not file_path.is_file():
        raise ElementNotFoundException(message="Requirement file not found", details=f"file: {file_path}")
    return [line for line in (line.strip() for line in file_path.open()) if line and not line.startswith("#")]


def read_multiple_requirements_files(file_paths: List[Path]) -> List[str]:
    """Read a list of requirements files and return a list with the dependencies of all of them.

    Args:
        file_paths (List[Path]): List of requirements file paths.

    Returns:
        dependencies (List[str]): Dependencies list.

    """
    dependencies = []
    for file_path in file_paths:
        dependencies.extend(read_requirements_file(file_path=file_path))
    return dependencies


def get_requirements_from_dir(
    directory: Path, encoding: Optional[str] = None, exclude: Optional[List[str]] = None
) -> List[str]:
    """Get a list with all the libraries + versions from all requirements files of a directory (not in subdirectories of
    it). A file is considered a requirements file if it contains "requirements" in the name and has .txt extension.

    Args:
        directory: Root path where to look for req files
        encoding: Encoding used for the req files
        exclude: List of requirement files to exclude from the parsing

    Returns:
        requirements: List of strings with all the libraries plus versions found in req files of directory

    """
    requirements = []
    exclude = exclude or []
    for filename in os.listdir(directory):
        # Check if the file name contains 'requirements' and ends with '.txt'
        if "requirements" in filename and filename.endswith(".txt") and filename not in exclude:
            filepath = directory / filename
            with open(filepath, "r", encoding=encoding) as f_obj:
                for line in f_obj:
                    stripped_line = line.strip()
                    # Skip comments and lines starting with '─'
                    if stripped_line and not stripped_line.startswith("#") and not stripped_line.startswith("─"):
                        # Append the requirement to the list
                        requirements.append(stripped_line)
    return requirements
