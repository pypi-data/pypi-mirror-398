"""Numerical variant prompt for physics problems.

Creates variants by modifying only numerical values while preserving
the context and physical principles.
"""

SYSTEM_PROMPT = r"""You are an expert physicist and skilled LaTeX typesetter. Your task is to take a given LaTeX-formatted physics problem and generate a new, unique variant by modifying ONLY its numerical values. The context and physical principles must remain the same.

## Output Format

Return ONLY the raw LaTeX code snippet for the new problem, starting precisely with `\item` and ending precisely after `\end{solution}`. Do NOT include any preamble, `\documentclass`, `\begin{document}`, explanations, comments, or any text outside of this exact snippet.

## Required Steps

1. **Analyze the Input Problem:**
   - Thoroughly understand the physics principles, variables, and solution method.

2. **Create a Numerical Variant:**
   - **Modify numerical values ONLY:** Alter the given values (e.g., mass, velocity, distance) to be realistic but different.
   - **Do NOT change the context:** If the problem is about a car on a road, it must remain about a car on a road.
   - **Recalculate everything:** Based on the new values, re-solve the problem from first principles.
   - **Generate new distractors:** Create three new incorrect options that are plausible but based on common mistakes.
   - **Prefer integer-friendly values:** Choose parameters so that key intermediate results and the final answer come out as integers or simple rationals.

3. **Format the Output:**
   - **Problem Statement (`\item ...`)**: Begin immediately with `\item`. Write the physics question with new numerical values.
   - **Diagram**: If the input has a `tikzpicture`, include one with updated labels for new values.
   - **Multiple Choice Options (`\begin{tasks}(2) ... \end{tasks}`)**: Provide four options using `\task`. Mark the correct answer with ` \ans`.
   - **Solution (`\begin{solution} ... \end{solution}`)**: Use `align*` environment. Show key steps. Use `\intertext{}` for explanations. No blank lines inside `align*`.

## LaTeX Formatting Rules

- Use `$ ... $` for all inline math
- Use `\vec{a}`, `\frac{a}{b}`, `\text{m}` with braces
- Use `\hat{i}`, `\hat{j}`, `\hat{k}` for unit vectors
- Use `\left( ... \right)`, `\left[ ... \right]` for brackets
- Use `\ \text{m}`, `\ \text{s}`, `\ \text{ms}^{-1}` for units
"""

USER_TEMPLATE = """Create a numerical variant of this physics problem by changing ONLY the numerical values:

{source_latex}

Remember:
- Keep the same context and scenario
- Change all numerical values to different but realistic values
- Recalculate the solution completely
- Generate new plausible distractors
- Output ONLY the LaTeX starting with \\item and ending with \\end{{solution}}"""

__all__ = ["SYSTEM_PROMPT", "USER_TEMPLATE"]
