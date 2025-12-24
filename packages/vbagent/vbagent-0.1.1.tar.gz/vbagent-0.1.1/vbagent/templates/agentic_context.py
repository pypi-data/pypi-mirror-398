"""Template for CONTEXT.md file generated in agentic output directories.

This file helps external AI agents (Codex, Claude Code, Cursor, etc.)
understand the directory structure and work with physics problems.
"""

CONTEXT_TEMPLATE = '''# Physics Problems Workspace

This directory contains AI-processed physics problems with LaTeX content,
TikZ diagrams, solutions, and variants. Use this guide to understand the
structure and formatting conventions.

## Directory Structure

```
{directory_name}/
├── CONTEXT.md              # This file
├── scans/                  # Extracted LaTeX from images
│   └── Problem_N.tex       # Original problem + solution
├── classifications/        # Problem metadata (JSON)
│   └── Problem_N.json      # Type, difficulty, concepts
├── tikz/                   # TikZ diagram code
│   └── Problem_N.tex       # Standalone TikZ pictures
├── ideas/                  # Extracted physics concepts (JSON)
│   └── Problem_N.json      # Concepts, formulas, techniques
├── alternates/             # Alternative solution approaches
│   └── Problem_N.tex       # Different methods to solve
└── variants/               # Problem variations
    ├── numerical/          # Changed numerical values
    ├── context/            # Different real-world scenarios
    ├── conceptual/         # Concept-testing variations
    └── calculus/           # Calculus-based versions
```

## Problem File Format (scans/*.tex)

Each problem file follows this LaTeX structure:

```latex
\\item [Problem statement with physics scenario]
[Optional: \\begin{{tasks}}(4) for MCQ options]
\\begin{{solution}}
[Step-by-step solution with equations]
\\end{{solution}}
```

### Key LaTeX Conventions

- **Math mode**: `$...$` for inline, `\\[...\\]` or `align*` for display
- **Units**: Use `\\SI{{value}}{{unit}}` or `\\,\\text{{unit}}`
- **Fractions**: `\\frac{{num}}{{den}}`, not `/`
- **Vectors**: `\\vec{{v}}` or `\\mathbf{{v}}`
- **MCQ options**: `\\begin{{tasks}}(4)` with `\\task` before each option

### Example Problem Structure

```latex
\\item A ball is thrown vertically upward with initial velocity $v_0 = 20\\,\\text{{m/s}}$.
Find the maximum height reached. (Take $g = 10\\,\\text{{m/s}}^2$)
\\begin{{solution}}
Using kinematic equation: $v^2 = v_0^2 - 2gh$
At maximum height, $v = 0$:
\\[
h = \\frac{{v_0^2}}{{2g}} = \\frac{{(20)^2}}{{2 \\times 10}} = 20\\,\\text{{m}}
\\]
\\end{{solution}}
```

## TikZ Diagrams (tikz/*.tex)

TikZ files contain standalone diagram code:

```latex
\\begin{{tikzpicture}}[scale=1]
    % Coordinate system
    \\draw[->] (0,0) -- (3,0) node[right] {{$x$}};
    \\draw[->] (0,0) -- (0,3) node[above] {{$y$}};
    
    % Physics elements
    \\draw[thick] (0,0) -- (2,2);
    \\fill (2,2) circle (2pt) node[above right] {{$m$}};
\\end{{tikzpicture}}
```

### TikZ Best Practices

- Use `scale=1` for consistent sizing
- Label axes and important points
- Use `thick` for main elements, `dashed` for auxiliary lines
- Add node labels for physical quantities
- Use `->` for vectors and directions

## Classification Metadata (classifications/*.json)

```json
{{
    "question_type": "mcq_sc|mcq_mc|subjective|integer|assertion_reason|passage|match",
    "difficulty": "easy|medium|hard",
    "topic": "mechanics|thermodynamics|electromagnetism|optics|modern_physics",
    "subtopic": "specific subtopic",
    "has_diagram": true|false,
    "key_concepts": ["concept1", "concept2"],
    "requires_calculus": true|false
}}
```

## Ideas/Concepts (ideas/*.json)

```json
{{
    "concepts": ["Newton's laws", "Conservation of energy"],
    "formulas": ["F = ma", "KE = ½mv²"],
    "techniques": ["Free body diagram", "Energy conservation"],
    "difficulty_factors": ["Multiple forces", "2D motion"]
}}
```

## Working with Problems

### Review a Problem
1. Read `scans/Problem_N.tex` for the full problem and solution
2. Check `classifications/Problem_N.json` for metadata
3. View `tikz/Problem_N.tex` if diagram exists
4. See `ideas/Problem_N.json` for physics concepts

### Modify a Problem
1. Edit the `.tex` file directly
2. Ensure LaTeX syntax is valid
3. Keep solution inside `\\begin{{solution}}...\\end{{solution}}`
4. Maintain consistent formatting

### Create Variants
- `variants/numerical/` - Same problem, different numbers
- `variants/context/` - Same physics, different scenario
- `variants/conceptual/` - Tests understanding without calculation
- `variants/calculus/` - Requires calculus-based approach

## Common Physics Domains

| Domain | Key Concepts | Common Formulas |
|--------|--------------|-----------------|
| Mechanics | Forces, Motion, Energy | $F=ma$, $v=u+at$, $E=\\frac{{1}}{{2}}mv^2$ |
| Thermodynamics | Heat, Work, Entropy | $Q=mc\\Delta T$, $PV=nRT$ |
| Electromagnetism | Fields, Circuits | $F=qE$, $V=IR$, $\\oint B\\cdot dl=\\mu_0 I$ |
| Optics | Reflection, Refraction | $n_1\\sin\\theta_1=n_2\\sin\\theta_2$ |
| Modern Physics | Quantum, Relativity | $E=hf$, $E=mc^2$ |

## Quality Checklist

When reviewing or modifying problems, verify:

- [ ] Problem statement is clear and complete
- [ ] All given values have units
- [ ] Solution shows step-by-step working
- [ ] Final answer is boxed or clearly stated
- [ ] TikZ diagram matches problem description
- [ ] LaTeX compiles without errors

## File Naming Convention

- `Problem_1.tex`, `Problem_2.tex`, etc.
- Numbers correspond to original image order
- Consistent naming across all subdirectories

---

*Generated by vbagent - Physics Question Processing Pipeline*
*Problems: {problem_count} | Generated: {timestamp}*
'''


def generate_context_file(
    directory_name: str,
    problem_count: int,
) -> str:
    """Generate CONTEXT.md content for an agentic directory.
    
    Args:
        directory_name: Name of the output directory
        problem_count: Number of problems processed
        
    Returns:
        Formatted CONTEXT.md content
    """
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    return CONTEXT_TEMPLATE.format(
        directory_name=directory_name,
        problem_count=problem_count,
        timestamp=timestamp,
    )
