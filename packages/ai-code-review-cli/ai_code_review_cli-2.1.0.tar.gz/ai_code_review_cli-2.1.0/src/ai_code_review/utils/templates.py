"""Jinja2 template rendering for code review output."""

from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING, Literal

from jinja2 import Environment, PackageLoader

from ai_code_review.models.review import CodeReview

if TYPE_CHECKING:
    from ai_code_review.models.config import PlatformProvider


@cache
def _get_or_create_environment() -> Environment:
    """Get cached Jinja2 environment or create new one.

    The environment is created once and cached as a singleton for performance.
    Jinja2 environments are relatively expensive to initialize.
    Uses @cache (unbounded) which is appropriate for singleton pattern (Python 3.9+).

    Uses PackageLoader for robust resource loading that works with:
    - Standard pip installations
    - Editable installs (pip install -e)
    - Zip-based distributions (zipapp, PEX, shiv)
    - Frozen executables (PyInstaller, cx_Freeze)

    Returns:
        Configured Jinja2 Environment with custom filters
    """
    env = Environment(
        loader=PackageLoader("ai_code_review.utils", "review_templates"),
        # Security note: autoescape=False is intentional for markdown generation
        # - Templates render markdown with deliberate HTML tags (<details>, etc.)
        # - Content sources: LLM-generated reviews, git diffs, commit messages
        # - Output destinations: GitLab/GitHub (both sanitize HTML) or terminal
        # - XSS risk is mitigated by platform sanitization at render time
        # - User-controlled content is limited to code/commits in controlled repos
        autoescape=False,  # nosec B701: Intentional for markdown generation. See security note above.
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Register custom filters
    env.filters["risk_emoji"] = _risk_emoji

    return env


def _risk_emoji(risk_level: str) -> str:
    """Convert risk level to emoji."""
    mapping = {
        "low": "🟢",
        "medium": "🟡",
        "high": "🔴",
    }
    return mapping.get(risk_level, "🟡")


def get_template_type_for_platform(
    platform_provider: PlatformProvider,
) -> Literal["gitlab", "github", "local"]:
    """Determine template type based on platform provider.

    Centralizes template selection logic to avoid duplication across modules.

    Args:
        platform_provider: The configured platform provider

    Returns:
        Template type matching the platform (gitlab, github, or local)
    """
    from ai_code_review.models.config import PlatformProvider

    if platform_provider == PlatformProvider.LOCAL:
        return "local"
    elif platform_provider == PlatformProvider.GITHUB:
        return "github"
    else:
        return "gitlab"


def render_review(
    review: CodeReview,
    template_type: Literal["gitlab", "github", "local"] = "gitlab",
    include_summary: bool = True,
) -> str:
    """Render a CodeReview to markdown using the appropriate template.

    Args:
        review: The structured code review to render
        template_type: Target platform (gitlab, github, local)
        include_summary: Whether to include the MR/PR summary section

    Returns:
        Formatted markdown string
    """
    env = _get_or_create_environment()

    # Select template based on type
    if template_type == "local":
        template_name = "local_review.md.j2"
    else:
        # gitlab and github use same template with minor differences
        template_name = "remote_review.md.j2"

    template = env.get_template(template_name)

    return template.render(
        review=review,
        include_summary=include_summary,
        platform=template_type,
    )
