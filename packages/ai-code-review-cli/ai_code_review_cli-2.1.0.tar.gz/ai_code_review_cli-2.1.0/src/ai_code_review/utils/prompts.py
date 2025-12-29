"""LangChain prompt templates and chains for AI code review."""

from __future__ import annotations

from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from ai_code_review.models.config import Config
from ai_code_review.models.platform import PullRequestData
from ai_code_review.models.review import CodeReview
from ai_code_review.utils.constants import (
    MAX_COMMENT_BODY_LENGTH,
    MAX_OTHER_COMMENTS_IN_SYNTHESIS,
)

# Few-shot examples for better review quality
_FEW_SHOT_EXAMPLES = """
## Example Reviews

### Example 1: Security Issue

**Input:** SQL query using string interpolation
**Review:** Identified SQL injection vulnerability, suggested parameterized queries
**Risk:** High

### Example 2: Performance Issue

**Input:** N+1 query pattern in user fetching
**Review:** Identified performance bottleneck, suggested batch fetching
**Risk:** Medium

### Example 3: Well-Implemented Code

**Input:** Cached permission lookup with proper error handling
**Review:** Objective description, no issues identified, optional minor suggestion
**Risk:** Low
"""

# Legacy format examples for fallback to StrOutputParser
_LEGACY_FORMAT_FULL = """## AI Code Review

### 📋 MR Summary
[Write ONE sentence summarizing the change]

- **Key Changes:** [List 2-3 most important changes]
- **Impact:** [Describe affected modules/functionality]
- **Risk Level:** [Low/Medium/High] - [Brief reason]

### Detailed Code Review

[Technical review focusing on logic, security, performance, architecture]

#### 📂 File Reviews
[Only include if you have specific file feedback]

<details>
<summary><strong>📄 `filename`</strong> - Brief issue summary</summary>

- **[Review]** Actionable review with reasoning
- **[Question]** Clarifying questions (if needed)
- **[Suggestion]** Improvement suggestions (if needed)

</details>

### ✅ Summary

- **Overall Assessment:** [State findings: critical issues exist or review complete]
- **Priority Issues:** [Most critical items]
- **Minor Suggestions:** [Optional improvements]"""

_LEGACY_FORMAT_COMPACT = """## AI Code Review

### Detailed Code Review

[Technical review focusing on logic, security, performance, architecture]

#### 📂 File Reviews
[Only include if you have specific file feedback]

<details>
<summary><strong>📄 `filename`</strong> - Brief issue summary</summary>

- **[Review]** Actionable review with reasoning
- **[Question]** Clarifying questions (if needed)
- **[Suggestion]** Improvement suggestions (if needed)

</details>

### ✅ Summary

- **Overall Assessment:** [State findings: critical issues exist or review complete]
- **Priority Issues:** [Most critical items]
- **Minor Suggestions:** [Optional improvements]"""

_LEGACY_FORMAT_LOCAL = """## Local Code Review

### 🔍 Code Analysis

[Technical review focusing on logic, security, performance, architecture]

### 📂 File Reviews

**📄 `filename`** - Brief issue summary
- **Review:** Actionable review with reasoning
- **Question:** Clarifying questions (if needed)
- **Suggestion:** Improvement suggestions (if needed)

### ✅ Summary

**Overall Assessment:** [Quality rating + key recommendations]

**Priority Issues:**
- [Most critical item 1]
- [Most critical item 2]

**Minor Suggestions:**
- [Optional improvement 1]
- [Optional improvement 2]"""


def create_system_prompt(
    include_mr_summary: bool = True, local_mode: bool = False
) -> str:
    """Create system prompt for code review with structured output.

    Args:
        include_mr_summary: Whether summary fields will be populated
        local_mode: Whether this is a local git review

    Returns:
        Quality-focused system prompt (no format instructions)
    """
    summary_instruction = ""
    if not include_mr_summary:
        summary_instruction = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  IMPORTANT: Skip Summary Fields
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Do NOT populate these fields (leave as null/None):
- summary
- key_changes
- risk_level
- risk_justification

Focus ONLY on detailed file reviews and concrete issues.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    # This is a prompt template, not SQL code. The "SQL" text is educational content for the LLM.
    return f"""You are an expert senior software engineer specializing in code reviews.
{summary_instruction}

## Your Expertise
- Security vulnerabilities and best practices
- Performance optimization and algorithmic efficiency
- Code maintainability, readability, and SOLID principles
- Testing strategies and edge case identification
- Language-specific idioms and patterns

## Your Review Process

Before generating your review, internally follow this analysis process:

1. **UNDERSTAND INTENT**: Analyze the MR/PR description and commit messages to understand what the author is trying to accomplish and why.

2. **FIRST PASS**: Quickly scan ALL changes to get a holistic view of the implementation approach and identify critical files.

3. **SYNTHESIZE**: Summarize the overall intent vs. the actual implementation. Note any discrepancies.

4. **MACRO REVIEW**: Evaluate overall logic, security implications, design decisions, and alignment with project patterns.

5. **MICRO REVIEW**: Analyze each change for implementation errors, edge cases, and specific improvements.

After completing this analysis, provide only the final structured review.

## Understanding the Diff
- Lines with '+' are NEW code (the author's proposed solution)
- Lines with '-' are OLD code being REMOVED
- Focus on the actual changes, treating '+' lines as the implementation to evaluate
- When suggesting improvements, reference specific aspects of the proposed changes

## Tone & Communication Style

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  CRITICAL: You are a BUG DETECTOR, not a quality evaluator.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Your role:** Identify bugs, security risks, logic errors, and missing validations.

**Use factual, technical language:**
- Describe what the code does, not whether it's "good" or "bad"
- Focus on concrete problems: missing validations, security risks, performance issues
- State impacts directly: "Missing null check causes exception" not "Poor error handling"

**When issues found:**
"Missing input validation on line 42. Risk: SQL injection if userId contains special characters."

**When no issues:**
"No critical issues identified. Minor suggestions provided for testing coverage."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Remember: Your role = Find bugs. NOT: Judge quality.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Version Changes

Your version knowledge is outdated. When reviewing dependencies:
- Trust author's version choices
- Focus on dependency conflicts or structural issues, not version recommendations
- Example: Flag if two libraries conflict, not which version to use

## Review Priorities (in order)
1. **Security**: Authentication, authorization, injection, data exposure
2. **Correctness**: Logic errors, edge cases, error handling
3. **Performance**: Algorithmic complexity, resource usage, bottlenecks
4. **Maintainability**: Readability, naming, complexity, duplication
5. **Testing**: Coverage gaps, testability concerns

## Code Examples - IMPORTANT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  For EVERY concrete fix, you MUST include code_example
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**REQUIRED - Include code_example for:**
1. Security vulnerabilities (show sanitized version)
2. Logic errors (show corrected logic)
3. Bug fixes (show fixed code)
4. Performance issues (show optimized version)
5. Missing error handling (show try/catch or validation)

**Example 1 - Security fix:**
```python
# Fixed: Use parameterized query
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

**Example 2 - Logic error:**
```python
# Fixed: Check for None before accessing
if user is not None and user.is_active:
    process_request(user)
```

**Example 3 - Performance:**
```python
# Fixed: Use set for O(1) lookup instead of O(N)
valid_ids = set(allowed_ids)
if user_id in valid_ids:
    # process...
```

**Example 4 - Missing validation:**
```python
# Fixed: Add input validation
if not username or len(username) < 3:
    raise ValueError("Username must be at least 3 characters")
```

**SKIP code_example ONLY when:**
- Asking clarifying questions
- Suggesting exploratory refactoring
- Multiple valid approaches exist

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Default: If you can show a fix, include code_example.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Quality Standards
- Be specific: Reference exact lines/functions when possible
- Be actionable: Every issue should have a clear fix
- Be proportional: Critical bugs > style nitpicks
- Be educational: Explain *why* something is an issue
- Include code examples for concrete fixes

    {{few_shot_examples}}"""


def create_review_prompt(
    include_mr_summary: bool = True, local_mode: bool = False
) -> ChatPromptTemplate:
    """Create prompt template for structured code review (no format instructions).

    This prompt focuses on review quality and problem identification. Format instructions
    are not needed because the LLM outputs a structured CodeReview object directly via
    with_structured_output().

    For models without structured output support, use create_legacy_review_prompt()
    which includes explicit markdown format instructions for StrOutputParser.

    Args:
        include_mr_summary: Whether summary fields should be populated
        local_mode: Whether this is a local git review

    Returns:
        ChatPromptTemplate for structured review generation
    """
    template = """Analyze the following code changes and provide a structured review.

{review_context_section}

{language_hint_section}

{project_context_section}

---

{diff_content}"""

    return ChatPromptTemplate.from_messages(
        [("system", "{system_prompt}"), ("human", template)]
    )


def create_legacy_system_prompt(
    include_mr_summary: bool = True, local_mode: bool = False
) -> str:
    """Create legacy system prompt with format instructions for StrOutputParser fallback.

    This prompt includes explicit format requirements for models that don't support
    structured output.

    Args:
        include_mr_summary: Whether to include MR Summary section
        local_mode: Whether this is a local git review

    Returns:
        System prompt with format requirements
    """
    if local_mode:
        sections = [
            "   - ### 🔍 Code Analysis",
            "   - ### 📂 File Reviews",
            "   - ### ✅ Summary",
        ]
    elif include_mr_summary:
        sections = [
            "   - ### 📋 MR Summary",
            "   - ### Detailed Code Review",
            "   - #### 📂 File Reviews (if needed)",
            "   - ### ✅ Summary",
        ]
    else:
        sections = [
            "   - ### Detailed Code Review",
            "   - #### 📂 File Reviews (if needed)",
            "   - ### ✅ Summary",
        ]

    section_list = "\n".join(sections)
    header_title = "## Local Code Review" if local_mode else "## AI Code Review"

    return f"""You are an expert senior software engineer and a meticulous code reviewer.

CRITICAL FORMAT REQUIREMENTS - FAILURE TO FOLLOW WILL RESULT IN REJECTED OUTPUT:
1. Start with exactly "{header_title}"
2. Use exactly these section headers in order:
{section_list}
3. Use only these section headers - maintain the structure shown
4. Write within the defined sections - each section serves a specific purpose
5. Keep each section concise and focused

UNDERSTANDING THE DIFF FORMAT:
The code changes are shown in unified diff format:
- Lines starting with '+' are NEW code being ADDED in this change
- Lines starting with '-' are OLD code being REMOVED in this change
- Lines without '+' or '-' are context lines (unchanged code for reference)

**Review the changes:**
- Focus on the NEW code (lines with '+') and what's being removed (lines with '-')
- The '+' lines show code already added - review these for issues
- The '-' lines show code already removed - verify nothing important was lost

Your goal is to provide concise, high-quality, constructive feedback on code changes.
Focus ONLY on the changes in the diff, not the entire codebase.
Your tone should be helpful, collaborative, and professional."""


def create_legacy_review_prompt(
    include_mr_summary: bool = True, local_mode: bool = False
) -> ChatPromptTemplate:
    """Create legacy prompt template with format instructions for StrOutputParser.

    Args:
        include_mr_summary: Whether to include MR Summary section
        local_mode: Whether this is a local git review

    Returns:
        ChatPromptTemplate with format examples
    """
    if local_mode:
        format_example = _LEGACY_FORMAT_LOCAL
    else:
        format_example = (
            _LEGACY_FORMAT_FULL if include_mr_summary else _LEGACY_FORMAT_COMPACT
        )

    template = f"""IGNORE any tendency to write free-form analysis. You MUST follow this EXACT template.

{{review_context_section}}

{{language_hint_section}}

{{project_context_section}}

❌ INCORRECT (unstructured analysis):
"This patchset introduces several changes..."

✅ REQUIRED FORMAT (follow exactly):

{format_example}

**CRITICAL: Match the format above exactly.** Use the same markdown structure, emoji, and section headers shown in the example.

---

{{diff_content}}"""

    return ChatPromptTemplate.from_messages(
        [("system", "{system_prompt}"), ("human", template)]
    )


# Data processing functions for chain inputs
def _extract_diff_content(input_data: dict[str, Any]) -> str:
    """Extract diff content from input data.

    Args:
        input_data: Dictionary containing 'diff' key with code changes

    Returns:
        The diff content as string
    """
    return str(input_data["diff"])


def _create_language_hint_section(input_data: dict[str, Any]) -> str:
    """Create language hint section if language is provided.

    Args:
        input_data: Dictionary that may contain 'language' key

    Returns:
        Formatted language section or empty string if no language provided
    """
    language = input_data.get("language")
    if language:
        return f"**Primary Language:** {language}"
    return ""


def _create_project_context_section(input_data: dict[str, Any]) -> str:
    """Create project context section if context is provided.

    Args:
        input_data: Dictionary that may contain 'context' key

    Returns:
        Formatted context section or empty string if no context provided
    """
    context = input_data.get("context")
    if context and context.strip():
        return f"""## Project Context & Guidelines

{context}

IMPORTANT: Apply the above project guidelines and conventions systematically when reviewing the code changes below. Follow the specific patterns, requirements, checklists, and best practices outlined in the context. Reference these guidelines directly in your review and ensure compliance with the established project standards."""
    return ""


def _create_system_prompt_func(
    include_mr_summary: bool, local_mode: bool = False
) -> Any:
    """Create a system prompt function with configuration baked in.

    This factory pattern is used because the LangChain Expression Language (LCEL)
    pipeline expects a callable that accepts a single dictionary argument.

    Args:
        include_mr_summary: Whether to include MR Summary section
        local_mode: Whether this is a local git review

    Returns:
        Function that returns system prompt with few-shot examples
    """

    def _get_system_prompt(input_data: dict[str, Any]) -> str:
        """Get system prompt with configuration already determined."""
        prompt = create_system_prompt(
            include_mr_summary=include_mr_summary, local_mode=local_mode
        )
        # Replace placeholder with actual few-shot examples
        return prompt.replace("{few_shot_examples}", _FEW_SHOT_EXAMPLES)

    return _get_system_prompt


def _create_legacy_system_prompt_func(
    include_mr_summary: bool, local_mode: bool = False
) -> Any:
    """Create a legacy system prompt function for fallback.

    Args:
        include_mr_summary: Whether to include MR Summary section
        local_mode: Whether this is a local git review

    Returns:
        Function that returns legacy system prompt with format instructions
    """

    def _get_legacy_system_prompt(input_data: dict[str, Any]) -> str:
        """Get legacy system prompt for StrOutputParser fallback."""
        return create_legacy_system_prompt(
            include_mr_summary=include_mr_summary, local_mode=local_mode
        )

    return _get_legacy_system_prompt


def _build_chain_inputs(
    include_mr_summary: bool, local_mode: bool = False, use_legacy: bool = False
) -> dict[str, Any]:
    """Build input transformation functions for review chain.

    Args:
        include_mr_summary: Whether to include MR Summary section
        local_mode: Whether this is a local git review (simpler format)
        use_legacy: Whether to use legacy system prompt with format instructions

    Returns:
        Dictionary mapping template variables to transformation functions
    """
    system_prompt_func = (
        _create_legacy_system_prompt_func(include_mr_summary, local_mode)
        if use_legacy
        else _create_system_prompt_func(include_mr_summary, local_mode)
    )

    return {
        "system_prompt": system_prompt_func,
        "diff_content": _extract_diff_content,
        "language_hint_section": _create_language_hint_section,
        "project_context_section": _create_project_context_section,
        "review_context_section": _create_review_context_section,
    }


def create_synthesis_prompt() -> ChatPromptTemplate:
    """Create prompt for synthesizing PR/MR context with comments.

    This prompt is used with a fast model to preprocess:
    - All comments and reviews (including resolved)
    - PR/MR description
    - Commit messages

    Output is a concise synthesis that highlights:
    - Author responses to previous AI reviews (CRITICAL)
    - Issues already identified and addressed
    - Ongoing discussions
    - Consensus points from reviewers

    Returns:
        ChatPromptTemplate for synthesis
    """
    system_prompt = """You are an expert at analyzing code review discussions.

Your task is to synthesize comments, reviews, and context from a PR/MR into a concise summary
that helps an AI code reviewer avoid repeating mistakes or already-addressed suggestions.

Focus on:
1. CRITICAL: Author responses to AI reviews (corrections, clarifications, updates)
2. Issues that were raised and already addressed
3. Ongoing discussions that need attention
4. Consensus points from multiple reviewers

Be concise and actionable. The output will be used as context for the main review."""

    template = """## PR/MR Description

{pr_description}

## Commit Messages

{commit_messages}

## Reviews and Comments

{reviews_and_comments}

---

Synthesize the above into a concise summary (max 500 words) that highlights:

1. **CRITICAL Author Corrections**: Any responses from the PR/MR author that correct, clarify, or invalidate previous AI review suggestions

2. **Addressed Issues**: Problems that were raised and have been resolved

3. **Active Discussions**: Ongoing conversations that the new review should be aware of

4. **Reviewer Consensus**: Points where multiple reviewers agree

Format as markdown with clear sections. Be specific and reference file/line when relevant."""

    return ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", template)]
    )


def _format_reviews_and_comments(pr_data: PullRequestData, bot_username: str) -> str:
    """Format reviews and comments for synthesis prompt.

    Args:
        pr_data: Pull request data containing reviews and comments
        bot_username: Username of the bot to identify AI reviews

    Returns:
        Formatted string with reviews and comments
    """
    lines = []

    # Format reviews
    if pr_data.reviews:
        lines.append("### Reviews\n")
        for review in pr_data.reviews:
            is_bot = " [AI REVIEW]" if review.author == bot_username else ""
            lines.append(
                f"**{review.author}**{is_bot} ({review.state}, {review.submitted_at}):\n"
                f"{review.body}\n"
            )

    # Format comments grouped by author
    if pr_data.comments:
        lines.append("\n### Comments\n")

        # Separate author responses to bot from other comments
        author_responses = []
        other_comments = []

        for comment in pr_data.comments:
            if comment.is_system:
                continue

            is_author = comment.author == pr_data.info.author
            mentions_bot = bot_username.lower() in comment.body.lower()

            if is_author and mentions_bot:
                author_responses.append(comment)
            else:
                other_comments.append(comment)

        # Author responses first (CRITICAL)
        if author_responses:
            lines.append("\n#### CRITICAL: Author Responses\n")
            for comment in author_responses:
                location = f" on {comment.path}:{comment.line}" if comment.path else ""
                resolved = " [RESOLVED]" if comment.resolved else ""
                lines.append(
                    f"**{comment.author}**{location}{resolved}:\n{comment.body}\n"
                )

        # Other comments (most recent first for active discussions)
        if other_comments:
            lines.append("\n#### Other Comments\n")
            # Sort by created_at descending (most recent first), then take top N
            sorted_comments = sorted(
                other_comments, key=lambda c: c.created_at, reverse=True
            )
            for comment in sorted_comments[:MAX_OTHER_COMMENTS_IN_SYNTHESIS]:
                location = f" on {comment.path}:{comment.line}" if comment.path else ""
                resolved = " [RESOLVED]" if comment.resolved else ""
                lines.append(
                    f"**{comment.author}**{location}{resolved}:\n{comment.body[:MAX_COMMENT_BODY_LENGTH]}\n"
                )

    return "\n".join(lines) if lines else "No reviews or comments yet."


def _format_commit_messages(pr_data: PullRequestData) -> str:
    """Format commit messages for synthesis.

    Args:
        pr_data: Pull request data containing commits

    Returns:
        Formatted string with commit messages
    """
    lines = []
    for commit in pr_data.commits[:10]:  # Limit to recent 10
        lines.append(f"- **{commit.short_id}**: {commit.title}")
    return "\n".join(lines) if lines else "No commits."


def create_synthesis_chain(llm: Any) -> Any:
    """Create chain for synthesizing review context.

    Args:
        llm: Fast language model (e.g., gemini-2.5-flash)

    Returns:
        LangChain pipeline for synthesis
    """
    prompt = create_synthesis_prompt()
    chain = prompt | llm | StrOutputParser()
    return chain


def _create_review_context_section(input_data: dict[str, Any]) -> str:
    """Create review context section from synthesis.

    Args:
        input_data: Dictionary containing optional 'review_synthesis' key

    Returns:
        Formatted review context section or empty string
    """
    synthesis = input_data.get("review_synthesis")

    if synthesis:
        # Use preprocessed synthesis
        return f"""## Review Context and Previous Discussions

{synthesis}

**Note:** The above is a synthesis of all previous reviews, comments, and discussions.
Pay special attention to author corrections to avoid repeating invalidated suggestions.

---

"""

    # No synthesis available (first review or disabled)
    return ""


def create_review_chain(llm: Any, config: Config) -> Any:
    """Create a LangChain pipeline for structured code review.

    Uses with_structured_output() to get properly typed CodeReview objects
    instead of raw string output.

    This approach provides:
    - Structured, type-safe review data
    - No format instructions needed in prompts
    - Direct Pydantic model validation
    - Separation of data (model) and presentation (templates)

    Args:
        llm: Language model instance to use for generating reviews
        config: Configuration object with review format preferences

    Returns:
        LangChain pipeline ready to process structured review requests

    Example:
        >>> chain = create_review_chain(my_llm, config)
        >>> result = chain.invoke({
        ...     "diff": "- old code\n+ new code",
        ...     "language": "Python",
        ...     "context": "This is a web API project"
        ... })
        >>> # Result is a CodeReview object with all fields populated
    """
    # Determine if local mode based on platform
    local_mode = (
        hasattr(config, "platform_provider")
        and config.platform_provider.value == "local"
    )

    prompt_template = create_review_prompt(
        include_mr_summary=config.include_mr_summary and not local_mode,
        local_mode=local_mode,
    )
    input_transformations = _build_chain_inputs(
        include_mr_summary=config.include_mr_summary and not local_mode,
        local_mode=local_mode,
    )

    # Import logger
    import structlog

    logger = structlog.get_logger()

    # Try to use structured output for type-safe reviews
    try:
        structured_llm = llm.with_structured_output(CodeReview)

        # Get model name from LLM object (most providers use .model attribute)
        model_name = (
            getattr(llm, "model", None)
            or getattr(llm, "model_name", None)
            or config.ai_model
            or "unknown"
        )

        logger.info(
            "Using structured output for review generation",
            model=model_name,
        )

        # Create LangChain pipeline: input_transformations -> prompt -> structured_llm
        chain = input_transformations | prompt_template | structured_llm
        return chain

    except NotImplementedError as e:
        # Expected: Model/provider doesn't support structured output
        # Fallback to legacy string parser with format instructions
        model_name = (
            getattr(llm, "model", None)
            or getattr(llm, "model_name", None)
            or config.ai_model
            or "unknown"
        )

        logger.warning(
            "Structured output not supported by model, using legacy string parser",
            model=model_name,
            reason="NotImplementedError",
            error_detail=str(e),
        )
    except AttributeError:
        # Expected: LLM object doesn't have with_structured_output method
        # This happens with older LangChain versions or custom LLM wrappers
        model_name = (
            getattr(llm, "model", None)
            or getattr(llm, "model_name", None)
            or config.ai_model
            or "unknown"
        )

        logger.warning(
            "LLM does not support with_structured_output method, using legacy parser",
            model=model_name,
            reason="AttributeError",
            llm_type=type(llm).__name__,
        )
    except Exception as e:
        # Unexpected: Log as error and re-raise to avoid masking legitimate issues
        model_name = (
            getattr(llm, "model", None)
            or getattr(llm, "model_name", None)
            or config.ai_model
            or "unknown"
        )

        logger.error(
            "Unexpected error creating structured output chain",
            model=model_name,
            error_type=type(e).__name__,
            error=str(e),
        )
        raise  # Re-raise unexpected errors

    # If we reach here, we're using fallback (NotImplementedError or AttributeError)
    # Use legacy prompt with format instructions
    legacy_prompt_template = create_legacy_review_prompt(
        include_mr_summary=config.include_mr_summary and not local_mode,
        local_mode=local_mode,
    )
    legacy_input_transformations = _build_chain_inputs(
        include_mr_summary=config.include_mr_summary and not local_mode,
        local_mode=local_mode,
        use_legacy=True,  # Use legacy system prompt with format instructions
    )

    chain = (
        legacy_input_transformations | legacy_prompt_template | llm | StrOutputParser()
    )
    return chain
