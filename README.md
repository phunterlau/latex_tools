# LaTeX Tools for Scientific Writing

A collection of utilities to streamline LaTeX document processing and make scientific writing more efficient, especially when working with AI/LLM tools.

## Tools

### 📄 `expand.py` - LaTeX Project Expander

Converts a LaTeX project (such as those from Overleaf) into a single, self-contained LaTeX file that includes all dependencies and citations. This is particularly useful for sharing your work with Large Language Models (LLMs) that need to understand the complete document structure.

#### Features

- **Automatic Main File Detection**: Finds the main `.tex` file by looking for `\begin{document}`
- **Recursive Include/Input Expansion**: Processes `\input{}` and `\include{}` statements recursively
- **Citation Extraction**: Identifies all citation keys (`\cite`, `\citep`, `\citet`, etc.)
- **Bibliography Integration**: Extracts relevant BibTeX entries from `.bib` files
- **Comment Preservation**: Handles LaTeX comments correctly (preserves escaped `%` signs)
- **Missing File Handling**: Gracefully handles missing files with clear markers
- **LLM-Friendly Output**: Appends a dedicated section with all bibliography entries

#### Usage

```bash
# Process a directory (auto-finds main .tex file)
python expand.py /path/to/latex/project

# Process a specific .tex file
python expand.py /path/to/main.tex
```

#### Input/Output

**Input**:

- A LaTeX project directory or a specific `.tex` file
- Associated `.bib` files in the same directory

**Output**:

- `<filename>_output.tex` - A single expanded LaTeX file
- All `\input` and `\include` statements resolved
- Complete bibliography section for LLM reference

#### Example

Given a project structure:

```text
my_paper/
├── main.tex          # Contains \input{sections/intro}
├── sections/
│   ├── intro.tex     # Contains \cite{smith2023}
│   └── methods.tex
└── references.bib    # Contains @article{smith2023, ...}
```

Running `python expand.py my_paper/` produces `main_output.tex` with:

- All section files merged into a single document
- All citations preserved in context
- Bibliography entries appended at the end for LLM reference

#### Technical Details

- **Encoding**: UTF-8 support for international characters
- **Recursion Protection**: Prevents infinite loops from circular includes
- **Path Resolution**: Handles relative paths correctly
- **Extension Handling**: Automatically adds `.tex` extension when missing
- **Comment Parsing**: Uses regex to properly handle LaTeX comments

#### Use Cases

1. **LLM Assistance**: Prepare your LaTeX project for AI tools that need complete context
2. **Collaboration**: Share a self-contained version of your paper
3. **Submission**: Create a single file for journals that require consolidated submissions
4. **Backup**: Generate a complete snapshot of your project
5. **Review**: Provide reviewers with a single file containing everything

---

### 🚀 `expand_improved.py` - Enhanced LaTeX Project Expander

An improved version of `expand.py` with robust error handling, better BibTeX parsing, and additional features.

#### New Features & Improvements

- **Robust BibTeX Parsing**: Proper handling of nested braces and complex entries
- **Command-Line Interface**: Full argument parsing with options
- **Better Error Handling**: Comprehensive error checking and informative messages
- **Logging System**: Proper logging instead of debug prints
- **Enhanced Citation Support**: Supports biblatex commands (`\autocite`, `\textcite`, etc.)
- **Path Handling**: Uses `pathlib` for robust cross-platform path operations
- **Type Hints**: Full type annotations for better code maintainability
- **Circular Include Detection**: Prevents infinite loops from circular dependencies
- **Multiple Main File Handling**: Smart detection when multiple main files exist
- **Encoding Robustness**: Better handling of different file encodings
- **Deduplication**: Avoids duplicate bibliography entries

#### Enhanced Usage

```bash
# Basic usage (same as original)
python expand_improved.py /path/to/latex/project

# Specify custom output filename
python expand_improved.py main.tex -o my_paper_complete.tex

# Skip bibliography processing (faster for large projects)
python expand_improved.py main.tex --no-bib

# Enable verbose logging for debugging
python expand_improved.py main.tex -v
```

#### Command-Line Options

- `-o, --output`: Specify custom output filename
- `--no-bib`: Skip bibliography processing for faster execution
- `-v, --verbose`: Enable detailed logging for debugging
- `-h, --help`: Show help message

#### Improvements Over Original

| Feature | Original | Improved |
|---------|----------|----------|
| BibTeX parsing | Simple regex (fragile) | Robust brace-counting parser |
| Error messages | Basic debug prints | Structured logging with levels |
| Citation support | Basic `\cite` variants | Full biblatex command support |
| File handling | Manual string operations | Type-safe `pathlib` operations |
| Circular includes | Not detected | Detected and handled gracefully |
| Command options | None | Full CLI with argparse |
| Code quality | No type hints | Full type annotations |
| Error recovery | Crashes on errors | Graceful error handling |

---

## Installation

1. Clone this repository:

   ```bash
   git clone <repository-url>
   cd latex-tools
   ```

2. Ensure you have Python 3.6+ installed

3. No additional dependencies required - uses only Python standard library

## Contributing

Feel free to contribute additional LaTeX tools or improvements to existing ones. Please follow these guidelines:

- Write clear documentation for new tools
- Include usage examples
- Add error handling for common edge cases
- Maintain compatibility with standard LaTeX conventions

## License

[Add your license here]

## Roadmap

Future tools planned for this repository:

- **Citation Formatter**: Convert between citation styles
- **Figure Optimizer**: Compress and optimize images for LaTeX
- **Table Generator**: Convert CSV/Excel to LaTeX tables
- **Style Checker**: Validate LaTeX best practices
- **Template Manager**: Manage and apply LaTeX templates

---

## Last Updated

July 2025

## Troubleshooting

### No bibliography entries found

- Ensure your project directory contains `.bib` files
- Check that your LaTeX files contain citation commands (`\cite{}`, `\citep{}`, etc.)
- Use `-v` flag with the improved version to see detailed logging
- The tool searches recursively, so `.bib` files in subdirectories will be found

### No main file found

- Make sure at least one `.tex` file contains `\begin{document}`
- Check file permissions and encoding (use UTF-8)
- The tool searches recursively in the provided directory

### Circular include detected

- This warning appears when files include each other in a loop
- The tool handles this gracefully by skipping repeated includes
