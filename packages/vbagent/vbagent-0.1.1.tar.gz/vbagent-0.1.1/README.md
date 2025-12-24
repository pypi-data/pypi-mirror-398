# VBAgent

A multi-agent CLI tool for processing physics question images. Supports classification, LaTeX extraction, TikZ diagram generation, variant creation, and format conversion.

## Installation

### From PyPI

```bash
pip install vbagent
```

### From Source

```bash
# Clone the repository
git clone https://github.com/vaibhavblayer/vbagent.git
cd vbagent

# Install with pip
pip install .

# Or install in development mode
pip install -e .

# Or using Poetry
poetry install
```

## Requirements

- Python 3.12+
- OpenAI API key (set as `OPENAI_API_KEY` environment variable)

## Configuration

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key"
```

Or configure via the CLI:

```bash
vbagent config set api-key YOUR_API_KEY
```

## Usage

### Quick Start

```bash
# Scan a physics question image to LaTeX
vbagent scan -i question.png -o output.tex

# Classify a question type
vbagent classify -i question.png

# Generate TikZ diagram from image
vbagent tikz -i diagram.png -o diagram.tex

# Generate problem variants
vbagent variant -t problem.tex -o variants.tex
```

### Commands

| Command | Description |
|---------|-------------|
| `classify` | Classify physics question image type |
| `scan` | Extract LaTeX from question image |
| `tikz` | Generate TikZ/PGF code for diagrams |
| `idea` | Extract physics concepts and ideas |
| `alternate` | Generate alternative solutions |
| `variant` | Generate problem variants (numerical, conceptual, context) |
| `convert` | Convert between question formats |
| `process` | Run full processing pipeline |
| `batch` | Batch process multiple images with resume capability |
| `ref` | Manage reference context files |
| `config` | Configure models and settings |
| `check` | QA review with interactive approval |

### Batch Processing

Process multiple images with automatic resume on interruption:

```bash
# Initialize batch processing
vbagent batch init -i ./images -o ./output

# Continue processing (resumes from where it left off)
vbagent batch continue

# Check status
vbagent batch status
```

### Full Pipeline

Process a single image through the complete pipeline:

```bash
# Basic processing (classify + scan + tikz)
vbagent process -i question.png

# With ideas extraction
vbagent process -i question.png --ideas

# With alternate solutions
vbagent process -i question.png --alternate

# With variant generation
vbagent process -i question.png --variants numerical,context

# Full pipeline with all features
vbagent process -i question.png --ideas --alternate --variants numerical,context,conceptual
```

Process a range of images:

```bash
# Process Problem_1.png through Problem_5.png
vbagent process -i images/Problem_1.png -r 1 5

# Process range with parallel workers (faster)
vbagent process -i images/Problem_1.png -r 1 10 --parallel 3

# Process range with all features
vbagent process -i images/Problem_1.png -r 1 5 --ideas --alternate --variants numerical
```

Process TeX file with multiple items:

```bash
# Process items 1-5 from a TeX file
vbagent process -t problems.tex --range 1 5

# With alternate solutions and ideas
vbagent process -t problems.tex --range 1 5 --alternate --ideas
```

Custom output directory:

```bash
vbagent process -i question.png -o ./my_output
```

#### Process Command Options

| Option | Description |
|--------|-------------|
| `-i, --image` | Image file to process |
| `-t, --tex` | TeX file containing problems |
| `-r, --range` | Range of items to process (1-based, inclusive) |
| `--variants` | Variant types (comma-separated: numerical,context,conceptual,calculus) |
| `--alternate` | Generate alternate solutions |
| `--ideas` | Extract physics concepts |
| `--ref` | Reference directories for TikZ |
| `-o, --output` | Output directory (default: agentic) |
| `--context` | Use reference context (default: yes) |
| `-p, --parallel` | Parallel workers for batch (default: 1, max: 10) |

#### Output Structure

```
agentic/
├── scans/problem_1.tex           # Extracted LaTeX
├── classifications/problem_1.json # Question metadata
├── tikz/problem_1.tex            # Generated TikZ diagrams
├── ideas/problem_1.json          # Physics concepts (if --ideas)
├── alternates/problem_1.tex      # Alternate solutions (if --alternate)
├── variants/
│   ├── numerical/problem_1.tex   # Numerical variants
│   ├── context/problem_1.tex     # Context variants
│   └── conceptual/problem_1.tex  # Conceptual variants
└── CONTEXT.md                    # Documentation for AI agents
```

### Help

```bash
# General help
vbagent --help

# Command-specific help
vbagent scan --help
vbagent variant --help
```

### Scan Command

Extract LaTeX from physics question images:

```bash
# Basic scan with auto-classification
vbagent scan -i question.png

# Save output to file
vbagent scan -i question.png -o output.tex

# Override question type (skip classification)
vbagent scan -i question.png --type mcq_sc
```

### Variant Command

Generate problem variants with controlled modifications:

```bash
# Numerical variant (change numbers only)
vbagent variant -t problem.tex --type numerical

# Context variant (change scenario)
vbagent variant -t problem.tex --type context

# Generate multiple variants
vbagent variant -t problem.tex --type numerical --count 3

# Process range of items
vbagent variant -t problems.tex --type numerical -r 1 5

# Multi-context variant (combine problems)
vbagent variant --type multi --context p1.tex --context p2.tex -o combined.tex

# From image (scans first)
vbagent variant -i image.png --type numerical -o variant.tex
```

#### Variant Types

| Type | Description |
|------|-------------|
| `numerical` | Change only numbers, keep context |
| `context` | Change scenario, keep numbers |
| `conceptual` | Change physics concept |
| `calculus` | Add calculus elements |
| `multi` | Combine multiple problems |

### Alternate Command

Generate alternative solution methods:

```bash
# Generate one alternate solution
vbagent alternate -t problem.tex

# Generate multiple alternates
vbagent alternate -t problem.tex -n 3

# With ideas context
vbagent alternate -t problem.tex --ideas ideas.json

# Save to file
vbagent alternate -t problem.tex -n 2 -o alternates.tex
```

### Check Command (QA Review)

AI-powered quality review with interactive approval workflow:

```bash
# Start a review session (random 5 problems)
vbagent check run

# Review more problems
vbagent check run -c 10

# Review specific problem
vbagent check run -p Problem_42

# Review from specific directory
vbagent check run -d ./my_output

# View suggestion history
vbagent check history

# Apply a stored suggestion
vbagent check apply 42

# Resume interrupted session
vbagent check resume abc123
```

#### Check Subcommands

| Subcommand | Description |
|------------|-------------|
| `run` | Start a random QA review session |
| `history` | View suggestion history |
| `apply` | Apply a stored suggestion by ID |
| `resume` | Resume an interrupted session |
| `solution` | Check solution correctness |
| `grammar` | Check grammar and spelling |
| `clarity` | Check clarity and conciseness |
| `tikz` | Check TikZ diagram code |

### TikZ Command

Generate TikZ/PGF code for diagrams:

```bash
# From image
vbagent tikz -i diagram.png

# With description
vbagent tikz -d "A block on an inclined plane with friction"

# Save to file
vbagent tikz -i diagram.png -o diagram.tex

# With reference directories
vbagent tikz -i diagram.png --ref ./tikz_examples/
```

### Idea Command

Extract physics concepts and ideas from problems:

```bash
# From TeX file
vbagent idea -t problem.tex

# Save to JSON
vbagent idea -t problem.tex -o ideas.json
```

## Supported Question Types

- MCQ Single Correct
- MCQ Multiple Correct
- Assertion-Reason
- Match the Following
- Passage/Comprehension
- Subjective/Numerical

## Variant Types

- **Numerical**: Change numerical values while preserving physics
- **Conceptual**: Modify the underlying concept
- **Context**: Change the real-world scenario

## Platform Support

Works on macOS, Windows, and Linux. Sleep prevention during batch processing is supported on all platforms.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run specific test
pytest tests/test_scanner.py -v
```

## License

MIT
