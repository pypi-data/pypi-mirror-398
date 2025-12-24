"""MCQ single-correct question scanner prompt."""

from vbagent.prompts.scanner.common import (
    DIAGRAM_PLACEHOLDER,
    LATEX_FORMATTING_RULES,
    OPTIONS_WITH_DIAGRAMS,
)

SYSTEM_PROMPT = r"""
## Overall Task & Output Format

**Goal:** Analyze the provided image. Generate a complete LaTeX multiple-choice physics question based **exactly** on the image, assuming it has a **single correct answer**. Include a step-by-step solution (which identifies the correct option) and, if applicable, a minimal TikZ diagram.

**CRITICAL OUTPUT CONSTRAINT:** You MUST return *only* the raw LaTeX code snippet starting precisely with `\item` and ending precisely after `\end{solution}`. Do **NOT** include *any* preamble, `\documentclass`, `\begin{document}`, explanations, comments, or any text outside of this exact snippet.

**ABSOLUTELY NO TRUNCATION:** Extract and output the COMPLETE content. Do NOT abbreviate, summarize, or truncate ANY part of the question, options, or solution. Every word, symbol, equation, and detail from the image MUST be included in full. If the content is long, output ALL of it without any shortcuts like "..." or "[continued]".

---

## Required LaTeX Structure

Follow this exact structure for your output:

1.  **Problem Statement (`\item ...`)**
    *   Begin the output immediately with `\item`.
    *   Extract the exact physics question text from the image without any modifications or additions.
    *   Use inline math mode `$ ... $` for all mathematical symbols and variables as they appear in the image.
    *   Do not include exam or year metadata (e.g., `NEET[2022]`, `JEE 2019`).

2.  **Diagram (Optional, place immediately after `\item` line if used)**
""" + DIAGRAM_PLACEHOLDER + r"""

3.  **Multiple Choice Options (`\begin{tasks}(c) ... \end{tasks}`)**
    *   Column rule: choose columns by option style.
        - Use `\begin{tasks}(2)` for numerical or short-expression options.
        - Use `\begin{tasks}(1)` for statement-based or long textual options.
    *   Extract the exact option text from the image without any modifications.
    *   Provide the options using `\task`.
    *   Based on your analysis in the solution step, mark the single correct answer by appending ` \ans` to the end of its corresponding `\task` line.
    
""" + OPTIONS_WITH_DIAGRAMS + r"""

4.  **Solution (`\begin{solution} ... \end{solution}`)**
    *   Use an `align*` environment directly inside the `solution` environment.
    *   Show key conceptual steps and reasoning for solving the problem based on the extracted text.
    *   Use `\intertext{}` for brief text explanations between equation lines. Ensure any math within `\intertext{}` uses `$ ... $`. Do not nest `\text{...}` inside `\intertext{}`; use plain prose and wrap only math in `$...$`.
    *   Critically: Evaluate the options to identify the single correct answer. Explain why it is correct and briefly why others might be incorrect if helpful for clarity. State the final correct option by letter (e.g., "Therefore, the correct option is (c)."). This analysis justifies the `\ans` marking in the `tasks` environment.
    *   Keep the solution concise and elegant. Show conceptual steps, but omit trivial intermediate algebra where appropriate.
    *   Align equations using `&`. Use `\\` to end lines.
    *   Keep only one step in every line of calculation.
    *   Strictly forbidden: Do not leave any blank lines inside the `align*` environment.

---

""" + LATEX_FORMATTING_RULES + r"""

---

**Final Check:** Ensure your output is ONLY the LaTeX snippet from `\item` to `\end{solution}` with no extra text or comments.
"""

USER_TEMPLATE = "Extract LaTeX from this physics question image."

__all__ = ["SYSTEM_PROMPT", "USER_TEMPLATE"]
