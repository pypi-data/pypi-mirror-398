"""Common prompt components for scanner prompts.

Shared TikZ guidelines, LaTeX formatting rules, and other reusable prompt sections.
"""

# TikZ Variable Guidelines - shared across all scanner prompts
TIKZ_GUIDELINES = r"""
    **TikZ Variable Guidelines (CRITICAL - CLEAN, MINIMAL VARIABLES):**
    
    **PRINCIPLES:**
    1. Define only BASE dimensions as variables (things you might adjust)
    2. Use NODES with anchors for objects (blocks, shapes) - enables relative positioning
    3. Use TikZ RELATIVE POSITIONING: `below of=`, `above of=`, `xshift`, `yshift`
    4. Use `node[midway]` for labels on lines/springs - NO position calculations
    5. Use SCOPES for repeated structures - avoids coordinate bloat
    
    *   Use `\pgfmathsetmacro` for base dimensions only:
        ```latex
        \pgfmathsetmacro{\containerWidth}{3.8}
        \pgfmathsetmacro{\containerHeight}{2.6}
        \pgfmathsetmacro{\waterLevel}{1.6}
        ```
    *   Define reusable styles with `\tikzset`.
    
    **Use Calc-Based Relative Positioning (CRITICAL - PREFERRED):**
    *   Use `$(node.anchor)+(x,y)$` to chain nodes from each other:
        ```latex
        \tikzset{
            pulley/.style={draw, thick, circle, minimum size=1cm, fill=white},
            block/.style={draw, thick, fill=white, minimum width=1.2cm, minimum height=0.8cm}
        }
        % BEST - use calc library: $(node.anchor)+(x,y)$
        \pic[rotate=180] (ceiling) at (0,0) {frame=2cm};
        \node[pulley] (pulley) at ($(ceiling-center)+(0,-1)$) {};
        \node[block] (block_right) at ($(pulley.east)+(0,-2)$) {$m_1$};
        \node[block] (block_left) at ($(pulley.west)+(0,-2.5)$) {$m_2$};
        
        % Also OK - use below of=, xshift, yshift:
        \node[block] (box1) [below of=pulley1, yshift=-1.5cm] {$m_1$};
        
        % BAD - calculating absolute coordinates:
        \pgfmathsetmacro{\boxOneX}{0}
        \pgfmathsetmacro{\boxOneY}{-2.5}
        \node[block] (box1) at (\boxOneX, \boxOneY) {$m$};
        ```
    
    **Use node[midway] for Labels on Lines/Springs (CRITICAL):**
        ```latex
        % GOOD - use node[midway] for labels:
        \draw[spring] (ceiling-center) -- (pulley1.north) node[midway, right=2mm] {$k$};
        \draw[thick] (pulley1.south) -- (box1.north) node[midway, right] {$T$};
        \draw[dashed] (A) -- (B) node[midway, above] {$d$};
        
        % BAD - calculating label positions separately:
        \pgfmathsetmacro{\labelX}{...}
        \pgfmathsetmacro{\labelY}{...}
        \node at (\labelX, \labelY) {$k$};
        ```
    
    **Springs/Coils - use EXACT decoration settings (CRITICAL):**
        ```latex
        % ALWAYS define spring style with these EXACT settings:
        \tikzset{
            spring/.style={thick, decorate, decoration={
                coil,
                amplitude=4pt,
                segment length=4.5pt,
                pre length=5pt,
                post length=5pt
            }}
        }
        % Usage - ALWAYS use node[midway] for labels:
        \draw[spring] (0,0) -- (0,-2) node[midway, right=5pt] {$k$};
        ```
    *   BAD: manual bezier curves for springs
    *   BAD: different amplitude/segment values
    *   BAD: calculating label position separately
    *   GOOD: use the exact spring/.style with node[midway] for labels
    
    **Repeated Structures - Use Scope with Shift:**
    *   For similar structures side-by-side (e.g., two containers), use `\begin{scope}[xshift=...]` instead of duplicating code:
        ```latex
        \pgfmathsetmacro{\scopeShift}{\containerWidth + 1.5}
        \begin{scope}[xshift=0cm]
            \draw (0,0) rectangle (\containerWidth, \containerHeight);
            \node[block] (blockA) at (...) {};
        \end{scope}
        \begin{scope}[xshift=\scopeShift cm]  % Same code, just shifted!
            \draw (0,0) rectangle (\containerWidth, \containerHeight);
            \node[block] (blockB) at (...) {};
        \end{scope}
        ```
    *   BAD: Duplicating code with `(5.2+\blockX, \blockY)` everywhere
    *   GOOD: Use scope to shift, then use same local coordinates inside each scope
    
    **Simple Plots - Use \draw plot with domain/samples:**
    *   For schematic curves, use `\draw plot` with actual functions:
        ```latex
        \draw[thin, ->] (0,0) -- (3,0) node[right] {$t$};
        \draw[thin, ->] (0,-1) -- (0,1) node[above] {$y$};
        \draw[thick] plot[domain=0:2.5, samples=50] (\x, {sin(4*\x r)*exp(-0.5*\x)});
        ```
    *   Use `plot[domain=a:b, samples=N]` - NOT `plot[smooth, tension=...]`
    *   Keep axes `thin`, data curves `thick`
    
    **KinemaTikZ Package (for mechanical diagrams):**
    *   Use `kinematikz` for frames, supports, pivots in mechanics diagrams
    *   IMPORTANT: Anchors use HYPHEN `-` not DOT `.`
        ```latex
        % Frame types
        \pic (support) at (0,0) {frame=2.5cm};
        \pic (base) at (0,0) {frame pivot flat=2cm};
        \pic[rotate=180] (ceiling) at (0,\topY) {frame=2.6cm};
        
        % Access anchors with hyphen:
        \draw (support-center) -- (mass.north);  % support is \pic, mass is \node
        % Available: -left, -right, -center, -north, -south, -in, -out
        ```
"""

# Shorter version for prompts that don't need full examples
TIKZ_GUIDELINES_SHORT = r"""
    **TikZ Variable Guidelines (CRITICAL):**
    *   Use `\pgfmathsetmacro` for base dimensions with camelCase names.
    *   Define reusable styles with `\tikzset` (e.g., `block/.style`, `pulley/.style`).
    *   **Calc-based positioning (PREFERRED):** Use `$(node.anchor)+(x,y)$` to chain nodes.
    *   **Also OK:** Use `[below of=node, xshift=..., yshift=...]` for relative positioning.
    *   **Labels on lines/springs:** Use `node[midway, right]` - NOT separate position calculations.
    *   **Springs/Coils:** Use `spring/.style` with EXACT settings: `amplitude=4pt, segment length=4.5pt, pre length=5pt, post length=5pt`.
    *   **Repeated Structures:** Use `\begin{scope}[xshift=...]` instead of duplicating code.
    *   **Simple plots:** Use `\draw plot[domain=0:2, samples=50] (\x, {sin(\x r)});` - thin axes, thick curves.
    *   **KinemaTikZ:** Use `\pic (name) {frame=2cm};` - anchors use hyphen: `name-center`, `name-left`.
"""

# LaTeX formatting rules - shared across all scanner prompts
LATEX_FORMATTING_RULES = r"""
## Strict LaTeX Formatting Rules

Adhere to these rules meticulously:

*   **Math Mode:** Use `$ ... $` for *all* inline math.
*   **Macros:** Always use `{}`: `\vec{a}`, `\frac{a}{b}`.
*   **Vectors:** Use `\vec{a}` for generic vectors and `\hat{i}`, `\hat{j}`, `\hat{k}` for unit vectors.
*   **Fractions:** Use `\frac{a}{b}`. **Do not use** `\tfrac`.
*   **Parentheses/Brackets:** Use `\left( ... \right)`, `\left[ ... \right]`, `\left| ... \right|`. **Do not use** `\bigl`, `\bigr`, `\Bigl`, `\Bigr`, etc.
*   **Intertext rule:** Inside `\intertext{...}`, do not use `\text{...}`. Use plain text and wrap math with `$...$`.
"""

# pgfplots axis environment example
PGFPLOTS_EXAMPLE = r"""
    *   **For graphs/plots with axes:** Use pgfplots `axis` environment:
        ```latex
        \begin{center}
        \begin{tikzpicture}
        \begin{axis}[
            axis lines = middle,
            xlabel = {$t$ (s)},
            ylabel = {$x$ (m)},
            xmin = 0, xmax = 10,
            ymin = -5, ymax = 10,
            grid = major,
            grid style = {dashed, line width=0.1pt, black!20},
            xtick = {0,1,2,3,4,5,6,7,8,9,10},
            ytick = {-5,0,5,10},
            tick label style = {font=\footnotesize},
            width = 8cm,
            height = 5cm,
        ]
        \addplot[thick] coordinates {(0,0) (1,-5) (2,0) (3,5)};
        \end{axis}
        \end{tikzpicture}
        \end{center}
        ```
"""

# Diagram placeholder instruction - scanner outputs placeholder, TikZ agent generates actual code
DIAGRAM_PLACEHOLDER = r"""
    **Diagram Handling (IMPORTANT):**
    *   If the image contains a diagram, output ONLY a placeholder:
        ```latex
        \begin{center}
            \input{diagram}
        \end{center}
        ```
    *   Do NOT generate TikZ code during scanning - the TikZ agent will generate it separately.
    *   Place the placeholder immediately after the `\item` line (before options/tasks).
"""

# Options with diagrams - scanner outputs placeholders, TikZ agent generates definitions
OPTIONS_WITH_DIAGRAMS = r"""
    **IMPORTANT - Options with Diagrams/Graphs:**
    If the options contain diagrams or graphs, output ONLY placeholders in the tasks:
    ```latex
    % Placeholder comment for TikZ agent to generate option diagrams
    % OPTIONS_DIAGRAMS: 4 options with graphs showing different curves
    \begin{tasks}(2)
        \task \OptionA
        \task \OptionB
        \task \OptionC \ans
        \task \OptionD
    \end{tasks}
    ```
    *   Do NOT generate TikZ code for options during scanning.
    *   The TikZ agent will generate `\def\OptionA{...}`, `\def\OptionB{...}`, etc.
    *   Just use `\OptionA`, `\OptionB`, `\OptionC`, `\OptionD` as placeholders in tasks.
    *   Add a comment describing what each option diagram shows (for TikZ agent).
"""

__all__ = [
    "TIKZ_GUIDELINES",
    "TIKZ_GUIDELINES_SHORT",
    "LATEX_FORMATTING_RULES",
    "PGFPLOTS_EXAMPLE",
    "OPTIONS_WITH_DIAGRAMS",
    "DIAGRAM_PLACEHOLDER",
]
