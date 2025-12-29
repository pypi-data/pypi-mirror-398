"""Code packaging for tup - prepares code for upload to Cloudflare."""

import base64
import io
import os
import zipfile
from pathlib import Path

import cloudpickle

from .types import JobConfig, JobSpec


# Patterns to exclude from packaging
EXCLUDE_PATTERNS = {
    ".git",
    ".gitignore",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".env",
    ".env.*",
    "*.egg-info",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    ".venv",
    "venv",
    ".tup",
    "*.log",
}


def should_exclude(path: Path, base_path: Path) -> bool:
    """Check if a path should be excluded from packaging."""
    rel_path = path.relative_to(base_path)

    for part in rel_path.parts:
        # Check exact matches
        if part in EXCLUDE_PATTERNS:
            return True
        # Check glob patterns
        for pattern in EXCLUDE_PATTERNS:
            if "*" in pattern:
                import fnmatch

                if fnmatch.fnmatch(part, pattern):
                    return True

    return False


def get_symbol_path(fn: object) -> str:
    """Get the importable path for a function.

    Returns a string like "module.submodule:function_name" that can be
    used to import and call the function.
    """
    module = getattr(fn, "__module__", None)
    name = getattr(fn, "__qualname__", None) or getattr(fn, "__name__", None)

    if not module or not name:
        raise ValueError(f"Cannot determine symbol path for {fn}")

    return f"{module}:{name}"


def create_job_config(job_spec: JobSpec) -> JobConfig:
    """Create a JobConfig from a JobSpec."""
    return JobConfig(
        log_relpath=job_spec.log_relpath,
        entrypoint=get_symbol_path(job_spec.main_fn),
        entrypoint_config=job_spec.entrypoint_config,
    )


def serialize_job_config(job_config: JobConfig) -> bytes:
    """Serialize a JobConfig using cloudpickle."""
    return cloudpickle.dumps(job_config)


def package_directory(
    directory: Path | str,
    include_requirements: bool = True,
) -> bytes:
    """Package a directory into a zip file.

    Args:
        directory: Path to the directory to package
        include_requirements: Whether to include requirements.txt/pyproject.toml

    Returns:
        Bytes of the zip file
    """
    directory = Path(directory).resolve()

    if not directory.is_dir():
        raise ValueError(f"Not a directory: {directory}")

    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(directory):
            root_path = Path(root)

            # Filter out excluded directories
            dirs[:] = [
                d for d in dirs if not should_exclude(root_path / d, directory)
            ]

            for file in files:
                file_path = root_path / file

                if should_exclude(file_path, directory):
                    continue

                # Get the relative path for the archive
                arcname = file_path.relative_to(directory)
                zf.write(file_path, arcname)

    return buffer.getvalue()


def package_single_file(file_path: Path | str) -> bytes:
    """Package a single Python file into a zip.

    Args:
        file_path: Path to the Python file

    Returns:
        Bytes of the zip file
    """
    file_path = Path(file_path).resolve()

    if not file_path.is_file():
        raise ValueError(f"Not a file: {file_path}")

    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(file_path, file_path.name)

        # Also include requirements.txt if it exists in same directory
        req_path = file_path.parent / "requirements.txt"
        if req_path.exists():
            zf.write(req_path, "requirements.txt")

    return buffer.getvalue()


def encode_package(data: bytes) -> str:
    """Encode package bytes as base64 string for JSON transport."""
    return base64.b64encode(data).decode("utf-8")


def decode_package(data: str) -> bytes:
    """Decode base64 package string back to bytes."""
    return base64.b64decode(data.encode("utf-8"))
