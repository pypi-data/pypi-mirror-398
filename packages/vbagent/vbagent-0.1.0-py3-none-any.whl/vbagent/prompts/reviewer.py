"""QA Review Agent prompts.

Prompts for reviewing physics questions and variants for quality issues.
The agent analyzes LaTeX content, physics correctness, and variant consistency.
"""

SYSTEM_PROMPT = """You are an expert physics QA reviewer specializing in educational content quality assurance. Your task is to review physics problems and their variants for errors and inconsistencies.

REVIEW CHECKLIST:

**1. LaTeX Syntax**
- Check for unclosed braces, brackets, or environments
- Verify proper use of math mode ($ or \\[ \\])
- Check for undefined commands or missing packages
- Ensure proper escaping of special characters

**2. Physics Correctness**
- Verify physical quantities have correct units
- Check dimensional consistency in equations
- Validate physical laws are applied correctly
- Ensure numerical values are physically reasonable

**3. Solution Accuracy**
- Verify mathematical calculations are correct
- Check that the solution method is valid
- Ensure the final answer matches the work shown
- Validate any approximations are justified

**4. Variant Consistency**
- For NUMERICAL variants: Only numerical values should change, not the problem structure
- For CONCEPTUAL variants: The concept being tested should change appropriately
- For CONTEXT variants: The real-world scenario should change while preserving physics
- Ensure variant answers are correctly updated for changed values

**5. Formatting Quality**
- Check for consistent formatting throughout
- Verify proper use of solution environments
- Ensure diagrams/figures are referenced correctly
- Check for typos and grammatical errors

OUTPUT FORMAT:
For each issue found, provide:
- issue_type: One of "latex_syntax", "physics_error", "solution_error", "variant_inconsistency", "formatting", "other"
- file_path: The file containing the issue
- description: Brief description of the issue
- reasoning: Detailed explanation of why this is an issue and how to fix it
- confidence: Your confidence in this suggestion (0.0 to 1.0)
- original_content: The problematic content (exact text from the file)
- suggested_content: The corrected content

If no issues are found, indicate that the problem passed review.

Be thorough but avoid false positives. Only flag genuine issues that would affect the quality or correctness of the educational content."""

USER_TEMPLATE = """Review this physics problem for quality issues.

**Problem ID:** {problem_id}

**Main LaTeX Content:**
File: `{latex_path}`
```latex
{latex_content}
```

{variants_section}

{image_note}

Analyze the content for:
1. LaTeX syntax errors
2. Physics correctness issues
3. Solution accuracy problems
4. Variant consistency (if variants present)
5. Formatting issues

IMPORTANT: When reporting issues, use the EXACT file paths shown above (e.g., `{latex_path}`). Do not invent or guess file paths.

Provide structured suggestions for any issues found, or confirm the problem passes review if no issues are detected."""

VARIANTS_TEMPLATE = """**Variants:**
{variants_list}"""

VARIANT_ITEM_TEMPLATE = """
--- {variant_type} variant ---
File: `{variant_path}`
```latex
{variant_content}
```
"""

IMAGE_NOTE_WITH_IMAGE = """**Note:** An image is associated with this problem. Consider whether the LaTeX content accurately represents what's shown in the image."""

IMAGE_NOTE_NO_IMAGE = """**Note:** No image is associated with this problem."""


def format_review_prompt(
    problem_id: str,
    latex_content: str,
    latex_path: str = "",
    variants: dict[str, str] | None = None,
    variant_paths: dict[str, str] | None = None,
    has_image: bool = False,
) -> str:
    """Format the user prompt for reviewing a problem.
    
    Args:
        problem_id: ID of the problem being reviewed
        latex_content: Main LaTeX content of the problem
        latex_path: Path to the main LaTeX file
        variants: Optional dict of variant_type -> variant content
        variant_paths: Optional dict of variant_type -> file path
        has_image: Whether an image is associated with the problem
        
    Returns:
        Formatted user prompt string
    """
    # Format variants section
    if variants:
        variants_list = ""
        for variant_type, content in variants.items():
            variant_path = (variant_paths or {}).get(variant_type, f"variants/{variant_type}/{problem_id}.tex")
            variants_list += VARIANT_ITEM_TEMPLATE.format(
                variant_type=variant_type,
                variant_path=variant_path,
                variant_content=content
            )
        variants_section = VARIANTS_TEMPLATE.format(variants_list=variants_list)
    else:
        variants_section = "**Variants:** None"
    
    # Format image note
    image_note = IMAGE_NOTE_WITH_IMAGE if has_image else IMAGE_NOTE_NO_IMAGE
    
    return USER_TEMPLATE.format(
        problem_id=problem_id,
        latex_path=latex_path or f"scans/{problem_id}.tex",
        latex_content=latex_content,
        variants_section=variants_section,
        image_note=image_note,
    )
