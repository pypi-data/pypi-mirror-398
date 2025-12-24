"""QA Review Agent for physics question quality assurance.

Uses OpenAI Agents SDK to analyze physics problems and variants,
generating structured suggestions with diffs for any issues found.
"""

import asyncio
import logging
import random
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from pydantic import BaseModel, Field

from vbagent.agents.base import (
    create_agent,
    create_image_message,
    run_agent,
)
from vbagent.agents.selector import ProblemContext
from vbagent.models.diff import generate_unified_diff
from vbagent.models.review import ReviewIssueType, ReviewResult, Suggestion
from vbagent.prompts.reviewer import SYSTEM_PROMPT, format_review_prompt


logger = logging.getLogger(__name__)


# Retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0  # seconds
DEFAULT_MAX_DELAY = 30.0  # seconds
DEFAULT_EXPONENTIAL_BASE = 2.0


class ReviewErrorType(str, Enum):
    """Types of errors that can occur during review."""
    API_ERROR = "api_error"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    INVALID_RESPONSE = "invalid_response"
    UNKNOWN = "unknown"


@dataclass
class ReviewError:
    """Error information from a failed review.
    
    Attributes:
        error_type: Type of error that occurred
        message: Human-readable error message
        retryable: Whether the error is retryable
        original_exception: The original exception if available
    """
    error_type: ReviewErrorType
    message: str
    retryable: bool = True
    original_exception: Optional[Exception] = None


def _classify_exception(e: Exception) -> ReviewError:
    """Classify an exception into a ReviewError.
    
    Args:
        e: The exception to classify
        
    Returns:
        ReviewError with appropriate type and retryability
    """
    error_str = str(e).lower()
    exception_type = type(e).__name__
    
    # Rate limiting errors
    if "rate" in error_str and "limit" in error_str:
        return ReviewError(
            error_type=ReviewErrorType.RATE_LIMIT,
            message=f"Rate limit exceeded: {e}",
            retryable=True,
            original_exception=e,
        )
    
    # Timeout errors
    if "timeout" in error_str or "timed out" in error_str:
        return ReviewError(
            error_type=ReviewErrorType.TIMEOUT,
            message=f"Request timed out: {e}",
            retryable=True,
            original_exception=e,
        )
    
    # API errors (usually retryable)
    if any(x in error_str for x in ["api", "server", "503", "502", "500", "connection"]):
        return ReviewError(
            error_type=ReviewErrorType.API_ERROR,
            message=f"API error: {e}",
            retryable=True,
            original_exception=e,
        )
    
    # Validation/parsing errors (not retryable)
    if any(x in exception_type.lower() for x in ["validation", "parse", "json"]):
        return ReviewError(
            error_type=ReviewErrorType.INVALID_RESPONSE,
            message=f"Invalid response format: {e}",
            retryable=False,
            original_exception=e,
        )
    
    # Default: unknown error, try once more
    return ReviewError(
        error_type=ReviewErrorType.UNKNOWN,
        message=f"Unexpected error: {e}",
        retryable=True,
        original_exception=e,
    )


def _calculate_backoff_delay(
    attempt: int,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    exponential_base: float = DEFAULT_EXPONENTIAL_BASE,
) -> float:
    """Calculate exponential backoff delay with jitter.
    
    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation
        
    Returns:
        Delay in seconds
    """
    # Exponential backoff: base_delay * (exponential_base ^ attempt)
    delay = base_delay * (exponential_base ** attempt)
    
    # Add jitter (±25%)
    jitter = delay * 0.25 * (2 * random.random() - 1)
    delay += jitter
    
    # Cap at max delay
    return min(delay, max_delay)


# Lazy-loaded pydantic models and agent to avoid heavy imports at module load
_RawSuggestion = None
_RawReviewResult = None
_reviewer_agent = None


def _get_pydantic_models():
    """Lazily create pydantic models for structured output."""
    global _RawSuggestion, _RawReviewResult
    
    if _RawSuggestion is None:
        from pydantic import BaseModel, Field
        
        class RawSuggestion(BaseModel):
            """Raw suggestion from the AI before diff generation."""
            issue_type: str = Field(description="Type of issue: latex_syntax, physics_error, solution_error, variant_inconsistency, formatting, other")
            file_path: str = Field(description="Path to the file containing the issue")
            description: str = Field(description="Brief description of the issue")
            reasoning: str = Field(description="Detailed explanation of the issue and fix")
            confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0 to 1.0")
            original_content: str = Field(description="The problematic content from the file")
            suggested_content: str = Field(description="The corrected content")
        
        class RawReviewResult(BaseModel):
            """Raw review result from the AI."""
            passed: bool = Field(description="Whether the problem passed review with no issues")
            suggestions: list[RawSuggestion] = Field(
                default_factory=list,
                description="List of suggested fixes"
            )
            summary: str = Field(description="Summary of the review findings")
        
        _RawSuggestion = RawSuggestion
        _RawReviewResult = RawReviewResult
    
    return _RawSuggestion, _RawReviewResult


def _get_reviewer_agent():
    """Lazily create the reviewer agent."""
    global _reviewer_agent
    
    if _reviewer_agent is None:
        _, RawReviewResult = _get_pydantic_models()
        _reviewer_agent = create_agent(
            name="QAReviewer",
            instructions=SYSTEM_PROMPT,
            output_type=RawReviewResult,
            agent_type="reviewer",
        )
    
    return _reviewer_agent


def _convert_issue_type(issue_type_str: str) -> ReviewIssueType:
    """Convert string issue type to enum, with fallback to OTHER."""
    try:
        return ReviewIssueType(issue_type_str.lower())
    except ValueError:
        return ReviewIssueType.OTHER


def _create_suggestion_with_diff(
    raw: RawSuggestion,
    context: ProblemContext,
) -> Suggestion:
    """Convert a raw suggestion to a Suggestion with generated diff.
    
    Args:
        raw: Raw suggestion from the AI
        context: Problem context for file path resolution
        
    Returns:
        Suggestion with unified diff
    """
    # Generate unified diff
    diff = generate_unified_diff(
        original=raw.original_content,
        modified=raw.suggested_content,
        file_path=raw.file_path,
    )
    
    return Suggestion(
        issue_type=_convert_issue_type(raw.issue_type),
        file_path=raw.file_path,
        description=raw.description,
        reasoning=raw.reasoning,
        confidence=raw.confidence,
        original_content=raw.original_content,
        suggested_content=raw.suggested_content,
        diff=diff,
    )


async def review_problem(
    context: ProblemContext,
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
) -> ReviewResult:
    """Review a problem and generate suggestions.
    
    Analyzes the problem's LaTeX content, variants, and optionally
    the source image to identify quality issues.
    
    Implements retry with exponential backoff for transient API errors.
    
    Args:
        context: ProblemContext with all files loaded
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Base delay for exponential backoff in seconds (default: 1.0)
        
    Returns:
        ReviewResult with pass/fail status and suggestions
        
    Raises:
        ReviewAgentError: If all retry attempts fail
    """
    # Format the review prompt with actual file paths
    prompt = format_review_prompt(
        problem_id=context.problem_id,
        latex_content=context.latex_content,
        latex_path=context.latex_path,
        variants=context.variants if context.variants else None,
        variant_paths=context.variant_paths if context.variant_paths else None,
        has_image=context.image_path is not None,
    )
    
    last_error: Optional[ReviewError] = None
    reviewer_agent = _get_reviewer_agent()
    _, RawReviewResult = _get_pydantic_models()
    
    for attempt in range(max_retries + 1):
        try:
            # Run the agent with or without image
            if context.image_path:
                # Include image in the review
                message = create_image_message(context.image_path, prompt)
                raw_result: RawReviewResult = await run_agent(reviewer_agent, message)
            else:
                # Text-only review
                raw_result = await run_agent(reviewer_agent, prompt)
            
            # Validate the response
            if raw_result is None:
                raise ValueError("Agent returned None response")
            
            # Convert raw suggestions to Suggestions with diffs
            suggestions = [
                _create_suggestion_with_diff(raw, context)
                for raw in raw_result.suggestions
            ]
            
            return ReviewResult(
                problem_id=context.problem_id,
                passed=raw_result.passed,
                suggestions=suggestions,
                summary=raw_result.summary,
            )
            
        except Exception as e:
            last_error = _classify_exception(e)
            
            logger.warning(
                f"Review attempt {attempt + 1}/{max_retries + 1} failed for "
                f"{context.problem_id}: {last_error.message}"
            )
            
            # Don't retry if error is not retryable
            if not last_error.retryable:
                logger.error(f"Non-retryable error for {context.problem_id}: {last_error.message}")
                break
            
            # Don't sleep after the last attempt
            if attempt < max_retries:
                delay = _calculate_backoff_delay(attempt, base_delay)
                logger.info(f"Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
    
    # All retries exhausted
    raise ReviewAgentError(
        f"Failed to review {context.problem_id} after {max_retries + 1} attempts",
        last_error=last_error,
    )


class ReviewAgentError(Exception):
    """Exception raised when review agent fails after all retries.
    
    Attributes:
        message: Error message
        last_error: The last ReviewError that occurred
    """
    
    def __init__(self, message: str, last_error: Optional[ReviewError] = None):
        super().__init__(message)
        self.last_error = last_error


def review_problem_sync(
    context: ProblemContext,
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
) -> ReviewResult:
    """Synchronous wrapper for review_problem.
    
    Args:
        context: ProblemContext with all files loaded
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Base delay for exponential backoff in seconds (default: 1.0)
        
    Returns:
        ReviewResult with pass/fail status and suggestions
        
    Raises:
        ReviewAgentError: If all retry attempts fail
    """
    return asyncio.run(review_problem(context, max_retries, base_delay))
