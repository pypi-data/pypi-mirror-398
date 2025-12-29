"""Validation utilities for sanitizing sensitive data in error messages."""

from __future__ import annotations

from pydantic import ValidationError

from ai_code_review.utils.constants import SENSITIVE_FIELDS


def sanitize_validation_error(
    error: ValidationError,
    sensitive_fields: set[str] | frozenset[str] | None = None,
) -> str:
    """
    Sanitize Pydantic validation errors to hide sensitive input values.

    Replaces input_value with [REDACTED] for sensitive fields like tokens and API keys.
    This prevents accidental leakage of sensitive data in logs or error messages.

    Special handling for root/model validators:
    - When a model_validator fails, Pydantic may return empty loc with input=full config dict
    - This function detects such cases and redacts the entire dict if it contains sensitive keys
    - This prevents the full configuration (with secrets) from being logged

    Args:
        error: Pydantic ValidationError to sanitize
        sensitive_fields: Set of field names to redact. If None, uses SENSITIVE_FIELDS constant
            from constants.py (gitlab_token, github_token, ai_api_key)

    Returns:
        Sanitized error message string with sensitive values replaced by [REDACTED]
        or [REDACTED_ROOT_CONFIG] for root validator errors with sensitive data

    Example:
        >>> from pydantic import BaseModel, ValidationError
        >>> class Config(BaseModel):
        ...     api_key: str
        >>> try:
        ...     Config(api_key="")
        ... except ValidationError as e:
        ...     sanitized = sanitize_validation_error(e, {"api_key"})
        ...     print(sanitized)
    """
    # Default sensitive fields if not provided
    if sensitive_fields is None:
        sensitive_fields = SENSITIVE_FIELDS

    # Convert error to dict format for easier manipulation
    errors = error.errors()

    # Build sanitized error message
    error_lines = [f"{error.error_count()} validation error(s) for {error.title}"]

    for err in errors:
        # Get field name (could be nested, so use last element)
        field = err["loc"][-1] if err["loc"] else "unknown"

        # Check if this is a sensitive field
        is_sensitive = any(sensitive in str(field) for sensitive in sensitive_fields)

        # Build error detail line
        loc_str = ".".join(str(loc_part) for loc_part in err["loc"]) or "__root__"
        error_lines.append(f"{loc_str}")

        # Message
        msg = err["msg"]
        error_lines.append(f"  {msg}")

        # Input value (hide if sensitive)
        input_val = err.get("input")

        # CRITICAL: Handle root validator errors where input might be the full config dict
        # Root validators (model_validator) can have empty loc and input = entire dict
        if not err["loc"] or err["loc"] == ("__root__",):
            # This is a root/model validator error
            if isinstance(input_val, dict):
                # Check if dict contains any sensitive keys
                if any(key in sensitive_fields for key in input_val.keys()):
                    error_lines.append(
                        "  [type=value_error, input_value='[REDACTED_ROOT_CONFIG]']"
                    )
                    continue
                # Dict doesn't contain sensitive keys, show it
                error_lines.append(
                    f"  [type={err['type']}, input_value={repr(input_val)}]"
                )
            elif input_val is not None:
                # Root error but not a dict, show it
                error_lines.append(
                    f"  [type={err['type']}, input_value={repr(input_val)}]"
                )
        elif is_sensitive and input_val:
            # Field-level validator for sensitive field
            error_lines.append("  [type=value_error, input_value='[REDACTED]']")
        elif input_val is not None:
            # Non-sensitive field validator
            error_lines.append(f"  [type={err['type']}, input_value={repr(input_val)}]")

    return "\n".join(error_lines)
