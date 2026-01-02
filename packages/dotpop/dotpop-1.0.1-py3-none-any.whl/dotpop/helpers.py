"""Helper functions for applying and exporting environment variables."""

import json
import os
import re
from typing import Dict, Set

from .resolved_env import ResolvedEnv


# Default patterns for secret redaction
DEFAULT_SECRET_PATTERNS = [
    r".*TOKEN.*",
    r".*SECRET.*",
    r".*PASSWORD.*",
    r".*KEY.*",
    r".*API_KEY.*",
    r".*PRIVATE.*",
]


def apply(values: Dict[str, str], overwrite: bool = False) -> None:
    """
    Apply values to os.environ.
    
    Args:
        values: Dictionary of values to apply
        overwrite: If True, overwrite existing values
    """
    for key, value in values.items():
        if overwrite or key not in os.environ:
            os.environ[key] = str(value)


def export(
    values: Dict[str, str],
    format: str = "dotenv",
    secret_patterns: list = None,
    redact_secrets: bool = True
) -> str:
    """
    Export values to a specific format.
    
    Args:
        values: Dictionary of values to export
        format: Output format ("dotenv", "json", "cmake", "cpp-header")
        secret_patterns: List of regex patterns for secret keys
        redact_secrets: If True, redact values matching secret patterns
    
    Returns:
        Formatted string
    """
    if secret_patterns is None:
        secret_patterns = DEFAULT_SECRET_PATTERNS
    
    # Compile patterns
    compiled_patterns = [re.compile(p, re.IGNORECASE) for p in secret_patterns]
    
    # Determine which keys are secrets
    secret_keys: Set[str] = set()
    if redact_secrets:
        for key in values.keys():
            for pattern in compiled_patterns:
                if pattern.match(key):
                    secret_keys.add(key)
                    break
    
    # Export based on format
    if format == "dotenv":
        return _export_dotenv(values, secret_keys)
    elif format == "json":
        return _export_json(values, secret_keys)
    elif format == "cmake":
        return _export_cmake(values, secret_keys)
    elif format == "cpp-header":
        return _export_cpp_header(values, secret_keys)
    else:
        raise ValueError(f"Unknown export format: {format}")


def _export_dotenv(values: Dict[str, str], secret_keys: Set[str]) -> str:
    """Export as dotenv format."""
    lines = []
    
    for key, value in sorted(values.items()):
        if key in secret_keys:
            lines.append(f'{key}="***REDACTED***"')
        else:
            # Escape quotes and newlines
            escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            lines.append(f'{key}="{escaped}"')
    
    return '\n'.join(lines) + '\n'


def _export_json(values: Dict[str, str], secret_keys: Set[str]) -> str:
    """Export as JSON."""
    output = {}
    
    for key, value in values.items():
        if key in secret_keys:
            output[key] = "***REDACTED***"
        else:
            output[key] = value
    
    return json.dumps(output, indent=2, sort_keys=True)


def _export_cmake(values: Dict[str, str], secret_keys: Set[str]) -> str:
    """Export as CMake set commands."""
    lines = []
    
    for key, value in sorted(values.items()):
        if key in secret_keys:
            lines.append(f'set({key} "***REDACTED***")')
        else:
            # Escape for CMake
            escaped = value.replace('\\', '\\\\').replace('"', '\\"')
            lines.append(f'set({key} "{escaped}")')
    
    return '\n'.join(lines) + '\n'


def _export_cpp_header(values: Dict[str, str], secret_keys: Set[str]) -> str:
    """Export as C++ header with defines."""
    lines = [
        '#pragma once',
        '',
        '// Auto-generated environment variables',
        '',
    ]
    
    for key, value in sorted(values.items()):
        if key in secret_keys:
            lines.append(f'#define {key} "***REDACTED***"')
        else:
            # Escape for C++
            escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            lines.append(f'#define {key} "{escaped}"')
    
    return '\n'.join(lines) + '\n'
