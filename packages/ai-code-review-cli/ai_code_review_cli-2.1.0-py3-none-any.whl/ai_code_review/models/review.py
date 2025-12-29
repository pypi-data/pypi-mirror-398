"""Review data models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ReviewComment(BaseModel):
    """A single review comment on a specific code location."""

    issue_type: Literal[
        "bug",
        "security",
        "performance",
        "logic",
        "style",
        "documentation",
        "testing",
        "architecture",
        "naming",
        "complexity",
        "other",
    ] = Field(
        description="Category of the issue identified. Must be one of: bug, security, performance, logic, style, documentation, testing, architecture, naming, complexity, other"
    )
    severity: Literal["critical", "major", "minor", "suggestion"] = Field(
        description="Severity level: critical=must fix, major=should fix, minor=nice to fix, suggestion=optional"
    )
    description: str = Field(
        description="Clear, actionable description of the issue (1-3 sentences)"
    )
    suggestion: str | None = Field(
        default=None,
        description="Specific suggestion for how to fix or improve the code",
    )
    code_example: str | None = Field(
        default=None,
        description="REQUIRED for concrete fixes: Code snippet demonstrating the exact fix. Include for: security vulnerabilities, logic errors, bug fixes, performance improvements. Omit for: exploratory suggestions, architectural advice, questions.",
    )


class FileReview(BaseModel):
    """Review for a single file with all its comments."""

    file_path: str = Field(description="Path to the reviewed file")
    summary: str = Field(
        description="Brief summary of changes in this file (1-2 sentences)"
    )
    comments: list[ReviewComment] = Field(
        default_factory=list, description="Specific review comments for this file"
    )
    questions: list[str] = Field(
        default_factory=list,
        description="Clarifying questions about the code changes in this file",
        max_length=8,  # Hard limit: keeps questions focused and relevant
    )


class CodeReview(BaseModel):
    """Complete structured code review for a merge/pull request."""

    # Summary section (optional based on include_mr_summary)
    summary: str | None = Field(
        default=None,
        description="High-level summary of the changes (1-2 sentences). What does this MR/PR accomplish?",
    )
    key_changes: list[str] = Field(
        default_factory=list,
        description="List of 2-4 most important changes in this MR/PR",
        max_length=6,  # Hard limit: allows 4 + buffer of 2
    )
    modules_affected: list[str] = Field(
        default_factory=list,
        description="List of modules, components, or areas affected by these changes",
        max_length=10,  # Hard limit: reasonable max for affected modules
    )
    risk_level: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="Risk assessment: low=safe changes, medium=needs review, high=critical changes",
    )
    risk_justification: str | None = Field(
        default=None, description="Brief explanation of the risk level assessment"
    )

    # Detailed review section
    general_feedback: str = Field(
        description="Technical review focusing on logic, security, performance, and architecture (2-4 paragraphs)"
    )
    file_reviews: list[FileReview] = Field(
        default_factory=list,
        description="Per-file review comments and suggestions (only include files with specific feedback)",
    )

    # Summary assessment
    overall_assessment: str = Field(
        description="Summary of findings: state if critical issues exist, otherwise note completion of review (1-2 sentences, NO quality ratings)"
    )
    priority_issues: list[str] = Field(
        default_factory=list,
        description="Critical issues that MUST be addressed before merge (maximum 8 items, prioritize by impact)",
        max_length=10,  # Hard limit: allows 8 + buffer of 2
    )
    minor_suggestions: list[str] = Field(
        default_factory=list,
        description="Optional improvements and nice-to-haves (maximum 8 items, prioritize most impactful)",
        max_length=12,  # Hard limit: allows 8 + buffer of 4
    )


class ReviewSummary(BaseModel):
    """High-level summary of a merge request."""

    title: str
    key_changes: list[str]
    modules_affected: list[str]
    user_impact: str
    technical_impact: str
    risk_level: str  # "Low", "Medium", "High"
    risk_justification: str


class ReviewResult(BaseModel):
    """Complete review result including both review and optional summary."""

    review: CodeReview
    summary: ReviewSummary | None = None

    def to_markdown(
        self,
        template_type: Literal["gitlab", "github", "local"] = "gitlab",
        include_summary: bool = True,
    ) -> str:
        """Convert review result to markdown using Jinja2 templates.

        Args:
            template_type: Target platform for formatting
            include_summary: Whether to include MR/PR summary section

        Returns:
            Formatted markdown string
        """
        # Detect legacy/fallback format (StrOutputParser response)
        # If the review was generated with fallback, the LLM already generated
        # complete markdown, so we return it directly to avoid duplicate headers
        is_legacy_format = (
            not self.review.file_reviews
            and not self.review.priority_issues
            and not self.review.minor_suggestions
            and self.review.overall_assessment == "AI Review Generated"
        )

        if is_legacy_format:
            # Return raw markdown from fallback (already formatted by LLM)
            return self.review.general_feedback

        from ai_code_review.utils.templates import render_review

        return render_review(self.review, template_type, include_summary)
