import ast
import json
import os
import re
import zipfile
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from konic.cli.client.api_client import KonicAPIClient

from konic.common.errors import KonicAgentNotFoundError


def find_entrypoint_file(directory: Path) -> Path | None:
    """
    Scans Python files in the directory to find which one calls 'register_agent'.
    Uses AST (Abstract Syntax Tree) to avoid false positives in comments/strings.
    """
    for file_path in directory.glob("*.py"):
        if file_path.name.startswith("__") or file_path.name.startswith("."):
            continue

        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()

            if "register_agent" not in source:
                continue

            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == "register_agent":
                        return file_path
                    elif (
                        isinstance(node.func, ast.Attribute) and node.func.attr == "register_agent"
                    ):
                        return file_path

        except (SyntaxError, UnicodeDecodeError):
            continue

    return None


def extract_agent_name_from_entrypoint(entrypoint_file: Path) -> str | None:
    """
    Extracts the agent name from the register_agent call in the entrypoint file.
    Looks for the 'name' keyword argument in the register_agent function call.
    """
    try:
        with open(entrypoint_file, encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                is_register_agent = (
                    isinstance(func, ast.Name) and func.id == "register_agent"
                ) or (isinstance(func, ast.Attribute) and func.attr == "register_agent")

                if is_register_agent:
                    for keyword in node.keywords:
                        if (
                            keyword.arg == "name"
                            and isinstance(keyword.value, ast.Constant)
                            and isinstance(keyword.value.value, str)
                        ):
                            return cast(str, keyword.value.value)

    except (SyntaxError, UnicodeDecodeError):
        pass

    return None


IGNORE_PATTERNS: set[str] = {
    "__pycache__",
    ".git",
    ".env",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
    "*.pyc",
    "*.zip",
    ".DS_Store",
}


def is_ignored(path: Path) -> bool:
    """Checks if a path should be ignored based on IGNORE_PATTERNS."""
    for part in path.parts:
        for pattern in IGNORE_PATTERNS:
            if part == pattern or (pattern.startswith("*") and part.endswith(pattern[1:])):
                return True
    return False


def create_artifact_zip(
    directory: Path,
    entrypoint_file: str,
    agent_name: str | None = None,
    agent_version: str = "v1",
) -> Path:
    """
    Creates a zip archive of the project and injects the manifest.

    Args:
        directory: The project directory to zip
        entrypoint_file: The path to the entrypoint file that contains register_agent (relative to directory)
        agent_name: Optional agent name to include in metadata. If not provided, will be extracted from entrypoint.
        agent_version: The version string for this agent (default: "v1")
    """
    zip_filename = directory / Path(f"{directory.name}.zip")

    if not agent_name and entrypoint_file:
        full_entrypoint_path = directory / entrypoint_file
        agent_name = extract_agent_name_from_entrypoint(full_entrypoint_path)

    try:
        konic_version = version("konic")
    except Exception:
        konic_version = "unknown"

    manifest = {
        "konic_version": konic_version,
        "entrypoint": entrypoint_file,
        "agent_version": agent_version,
    }

    if agent_name:
        manifest["agent-name"] = agent_name.replace(" ", "-").lower()

    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not is_ignored(Path(d))]

            for file in files:
                file_path = Path(root) / file

                if is_ignored(file_path) or file == zip_filename.name:
                    continue

                arcname = file_path.relative_to(directory)
                zipf.write(file_path, arcname)

        zipf.writestr(".konic-manifest.json", json.dumps(manifest, indent=2))

    return zip_filename


def compile_artifact(filepath: str) -> None:
    directory = Path(filepath)
    entrypoint = find_entrypoint_file(directory)
    if entrypoint:
        relative_entrypoint = str(entrypoint.relative_to(directory))
    else:
        relative_entrypoint = ""
    create_artifact_zip(directory, relative_entrypoint)


UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(-\d+)?$",
    re.IGNORECASE,
)

KONIC_ID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-\d+$",
    re.IGNORECASE,
)


def is_uuid(value: str) -> bool:
    """
    Check if a string looks like a UUID (agent ID).

    Supports both standard UUID format and Konic's uuid-timestamp format.

    Args:
        value: The string to check

    Returns:
        bool: True if the string matches UUID pattern
    """
    return UUID_PATTERN.match(value) is not None or KONIC_ID_PATTERN.match(value) is not None


def resolve_agent_identifier(client: "KonicAPIClient", name_or_id: str) -> str:
    """
    Resolve an agent name or ID to an agent ID.

    Uses the backend's /agents/resolve/{identifier} endpoint which:
    - First tries to find by ID
    - Then tries exact name match

    Args:
        client: The API client to use for queries
        name_or_id: Either an agent name or agent ID

    Returns:
        str: The agent ID

    Raises:
        KonicAgentNotFoundError: If no agent matches the given identifier
        KonicAgentResolutionError: If multiple agents match the given name
    """
    from konic.common.errors import KonicHTTPError

    try:
        result = client.get_json(f"/agents/resolve/{name_or_id}")
        return result["id"]
    except KonicHTTPError as e:
        if e.status_code == 404:
            raise KonicAgentNotFoundError(name_or_id)
        raise


def get_agent_by_id(client: "KonicAPIClient", agent_id: str) -> dict:
    """
    Get an agent by ID.

    Args:
        client: The API client to use
        agent_id: The agent ID

    Returns:
        dict: The agent metadata

    Raises:
        KonicAgentNotFoundError: If the agent is not found
    """
    from konic.common.errors import KonicHTTPError

    try:
        return client.get_json(f"/agents/{agent_id}")
    except KonicHTTPError as e:
        if e.status_code == 404:
            raise KonicAgentNotFoundError(agent_id)
        raise


def bump_version(current_version: str) -> str:
    """
    Bump a version string to the next version.

    Supports formats like "v1", "v2", "v10", "1", "2", "1.0", "1.0.0".

    Args:
        current_version: The current version string

    Returns:
        str: The next version string

    Examples:
        "v1" -> "v2"
        "v10" -> "v11"
        "1" -> "2"
        "1.0" -> "1.1"
        "1.0.0" -> "1.0.1"
    """
    if not current_version:
        return "v1"

    if current_version.lower().startswith("v"):
        try:
            num = int(current_version[1:])
            return f"v{num + 1}"
        except ValueError:
            pass

    try:
        num = int(current_version)
        return str(num + 1)
    except ValueError:
        pass

    parts = current_version.split(".")
    if parts:
        try:
            parts[-1] = str(int(parts[-1]) + 1)
            return ".".join(parts)
        except ValueError:
            pass

    if "-v" in current_version:
        base, ver = current_version.rsplit("-v", 1)
        try:
            return f"{base}-v{int(ver) + 1}"
        except ValueError:
            pass

    return f"{current_version}-v2"
