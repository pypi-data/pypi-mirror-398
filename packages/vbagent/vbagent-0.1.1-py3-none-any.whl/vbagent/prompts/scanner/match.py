"""Match-the-following question scanner prompt."""

from vbagent.prompts.scanner.common import DIAGRAM_PLACEHOLDER

SYSTEM_PROMPT = r"""
## Overall Task & Output Format

**Goal:** Analyze the provided image and extract a matching-type question. Format the texts in LaTeX format with the question in `\item` command, then diagram in tikz env nested within center env if there is any diagram present, then make the table for list/column/anything, then put the options in a tasks environment.

**CRITICAL OUTPUT CONSTRAINT:** Return only the raw LaTeX snippet starting precisely with `\item` and ending precisely after `\end{solution}`. Do not include any preamble, `\documentclass`, `\begin{document}`, or extra commentary.

**ABSOLUTELY NO TRUNCATION:** Extract and output the COMPLETE content. Do NOT abbreviate, summarize, or truncate ANY part of the question, table entries, options, or solution. Every word, symbol, equation, and detail from the image MUST be included in full. If the content is long, output ALL of it without any shortcuts like "..." or "[continued]".

---

## Required LaTeX Structure

1.  **Problem Statement (`\item ...`)**
    * Begin immediately with `\item`.
    * Extract the exact question text from the image.

2.  **Diagram (Optional)**
""" + DIAGRAM_PLACEHOLDER + r"""

3.  **Matching Table**
    * Use a table environment with appropriate column widths.
    * Format columns clearly with Column I and Column II headers.
    * Use `\renewcommand{\arraystretch}{2}` for better spacing.

4.  **Options (`\begin{tasks}(2) ... \end{tasks}`)**
    * Provide matching combinations using `\task`.
    * Mark the correct answer by appending ` \ans` to the correct option.

5.  **Solution (`\begin{solution} ... \end{solution}`)**
    * Use an `align*` environment inside the solution.
    * Explain the matching logic step by step.
    * Use `\intertext{}` for prose between equations.

---

## Example Structure

```latex
\item This is a sample question for matching type questions. Match column I with column II. 

\begin{center}
    \renewcommand{\arraystretch}{2}
    \begin{tabular}{p{0.25cm}p{8cm}|p{0.25cm}p{5cm}}
    \hline
    & Column I & & Column II \\
    \hline
    (a) & Item A description & (p) & Match P description \\
    (b) & Item B description & (q) & Match Q description \\
    (c) & Item C description & (r) & Match R description \\
    (d) & Item D description & (s) & Match S description \\
    \hline
    \end{tabular}
\end{center}

\begin{tasks}(2)
    \task $a \rightarrow p$, $b \rightarrow q$, $c \rightarrow r$, $d \rightarrow s$
    \task $a \rightarrow q$, $b \rightarrow p$, $c \rightarrow s$, $d \rightarrow r$ \ans
    \task $a \rightarrow r$, $b \rightarrow s$, $c \rightarrow p$, $d \rightarrow q$
    \task $a \rightarrow s$, $b \rightarrow r$, $c \rightarrow q$, $d \rightarrow p$
\end{tasks}
\begin{solution}
    \begin{align*}
        \intertext{Analyzing each match:}
        \intertext{(a) matches with (q) because...}
        \intertext{(b) matches with (p) because...}
        \intertext{(c) matches with (s) because...}
        \intertext{(d) matches with (r) because...}
        \intertext{Therefore, the correct option is (b).}
    \end{align*}
\end{solution}
```

---

## Strict LaTeX Rules

* Inline math: always `$...$`.
* Macros with braces: `\vec{a}`, `\frac{a}{b}`.
* Use `\left(\cdot\right)` for delimiters.
* No blank lines inside `align*` environment.

---

**Final Check:** Ensure your output is ONLY the LaTeX snippet from `\item` to `\end{solution}` with no extra text or comments.
"""

USER_TEMPLATE = "Extract LaTeX from this physics question image."

__all__ = ["SYSTEM_PROMPT", "USER_TEMPLATE"]
