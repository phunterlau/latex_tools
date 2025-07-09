#!/usr/bin/env python3
"""
LaTeX Project Expander - Improved Version

Converts a LaTeX project into a single, self-contained file with all includes
expanded and relevant bibliography entries appended.
"""

import os
import re
import sys
import argparse
import logging
from typing import Set, List, Optional, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def strip_comments(line: str) -> str:
    """Strip LaTeX comments but preserve escaped percent signs."""
    # Handle escaped percent signs and comments more robustly
    pattern = r'(?<!\\)(?:\\\\)*%.*'
    return re.sub(pattern, '', line)


def find_main_tex_file(directory: Path) -> Optional[Path]:
    """Find the main .tex file by looking for one with '\\begin{document}'."""
    tex_files = []
    main_candidates = []
    
    for tex_file in directory.rglob('*.tex'):
        tex_files.append(tex_file)
        try:
            with tex_file.open('r', encoding='utf-8') as f:
                content = f.read()
                if r'\begin{document}' in content:
                    main_candidates.append(tex_file)
        except (UnicodeDecodeError, PermissionError) as e:
            logger.warning(f"Could not read {tex_file}: {e}")
            continue
    
    if len(main_candidates) == 1:
        return main_candidates[0]
    elif len(main_candidates) > 1:
        logger.warning(f"Multiple main files found: {main_candidates}")
        # Prefer files named 'main.tex' or in root directory
        for candidate in main_candidates:
            if candidate.name.lower() in ['main.tex', 'paper.tex', 'article.tex']:
                return candidate
        # Return the one closest to root
        return min(main_candidates, key=lambda p: len(p.parts))
    else:
        logger.error(f"No main .tex file found in {directory}")
        logger.info(f"Found .tex files: {[str(f) for f in tex_files]}")
        return None


def expand_includes(filepath: Path, already_included: Optional[Set[Path]] = None, 
                   base_dir: Optional[Path] = None) -> List[str]:
    """Recursively expand \\input and \\include statements."""
    if already_included is None:
        already_included = set()
    if base_dir is None:
        base_dir = filepath.parent
    
    content = []
    abs_filepath = filepath.resolve()
    
    if abs_filepath in already_included:
        logger.warning(f"Circular include detected: {filepath}")
        return [f'% [CIRCULAR INCLUDE: {filepath}]\n']
    
    already_included.add(abs_filepath)
    
    try:
        with filepath.open('r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                parse_line = strip_comments(line)
                
                # Enhanced regex to handle more include patterns
                include_match = re.match(
                    r'\s*\\(input|include|InputIfFileExists|subfile)\s*\{\s*([^}]+)\s*\}',
                    parse_line
                )
                
                if include_match:
                    cmd, incfile = include_match.groups()
                    incfile = incfile.strip()
                    
                    # Handle relative paths
                    if not incfile.endswith('.tex'):
                        incfile += '.tex'
                    
                    incfile_path = base_dir / incfile
                    
                    if incfile_path.exists():
                        logger.debug(f"Including {incfile_path}")
                        content.extend(expand_includes(
                            incfile_path, already_included, incfile_path.parent
                        ))
                    else:
                        logger.warning(f"Missing include file: {incfile_path}")
                        content.append(f'% [MISSING FILE: {incfile_path}]\n')
                else:
                    content.append(line)
                    
    except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
        logger.error(f"Error reading {filepath}: {e}")
        content.append(f'% [ERROR READING FILE: {filepath} - {e}]\n')
    
    return content


def extract_citations(tex_content: List[str]) -> Set[str]:
    """Extract citation keys from various LaTeX citation commands."""
    # Comprehensive citation pattern matching
    cite_patterns = [
        r'\\cite\w*\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}',  # \cite, \citep, \citet, etc.
        r'\\autocite\w*\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}',  # biblatex autocite
        r'\\textcite\w*\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}',  # biblatex textcite
        r'\\parencite\w*\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}',  # biblatex parencite
        r'\\footcite\w*\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}',  # biblatex footcite
    ]
    
    citations = set()
    
    for line in tex_content:
        for pattern in cite_patterns:
            for match in re.finditer(pattern, line):
                keys = match.group(1)
                for key in keys.split(','):
                    key = key.strip()
                    if key:
                        citations.add(key)
    
    return citations


def find_bib_files(directory: Path) -> List[Path]:
    """Return list of .bib files in the directory and subdirectories."""
    return list(directory.rglob('*.bib'))


class BibTeXParser:
    """Robust BibTeX entry parser."""
    
    def __init__(self, content: str):
        self.content = content
        self.entries = {}
        self._parse()
    
    def _parse(self):
        """Parse BibTeX content and extract entries."""
        # Remove comments
        lines = []
        for line in self.content.split('\n'):
            line = line.strip()
            if line and not line.startswith('%'):
                lines.append(line)
        
        content = '\n'.join(lines)
        
        # Find entry boundaries more robustly
        entry_pattern = r'@(\w+)\s*\{\s*([^,\s]+)\s*,'
        
        pos = 0
        while pos < len(content):
            match = re.search(entry_pattern, content[pos:])
            if not match:
                break
            
            entry_start = pos + match.start()
            entry_type = match.group(1)
            entry_key = match.group(2)
            
            # Find the end of this entry by counting braces
            brace_count = 0
            entry_end = entry_start
            in_entry = False
            
            for i, char in enumerate(content[entry_start:], entry_start):
                if char == '{':
                    brace_count += 1
                    in_entry = True
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and in_entry:
                        entry_end = i + 1
                        break
            
            if entry_end > entry_start:
                entry_content = content[entry_start:entry_end]
                self.entries[entry_key] = entry_content
                pos = entry_end
            else:
                pos += match.end()
    
    def get_entries(self, keys: Set[str]) -> List[str]:
        """Get BibTeX entries for the specified keys."""
        found_entries = []
        missing_keys = []
        
        for key in keys:
            if key in self.entries:
                found_entries.append(self.entries[key])
            else:
                missing_keys.append(key)
        
        if missing_keys:
            logger.warning(f"Missing bibliography entries: {missing_keys}")
            for key in missing_keys:
                found_entries.append(f'% [Entry for {key} not found]')
        
        return found_entries


def extract_bib_entries(bib_files: List[Path], citation_keys: Set[str]) -> List[str]:
    """Extract BibTeX entries for the given keys from all bib files."""
    all_entries = []
    remaining_keys = citation_keys.copy()
    
    for bib_file in bib_files:
        if not remaining_keys:
            break
            
        try:
            with bib_file.open('r', encoding='utf-8') as f:
                content = f.read()
            
            parser = BibTeXParser(content)
            found_keys = set(parser.entries.keys()) & remaining_keys
            
            if found_keys:
                logger.info(f"Found {len(found_keys)} entries in {bib_file.name}")
                entries = parser.get_entries(found_keys)
                all_entries.extend(entries)
                remaining_keys -= found_keys
                
        except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
            logger.error(f"Error reading {bib_file}: {e}")
    
    if remaining_keys:
        logger.warning(f"Could not find entries for: {remaining_keys}")
        for key in remaining_keys:
            all_entries.append(f'% [Entry for {key} not found in any .bib file]')
    
    return all_entries


def create_output_filename(input_file: Path, custom_name: Optional[str] = None) -> Path:
    """Create output filename."""
    if custom_name:
        return Path(custom_name)
    return input_file.parent / f"{input_file.stem}_expanded.tex"


def main():
    parser = argparse.ArgumentParser(
        description='Expand LaTeX project into a single file with dependencies'
    )
    parser.add_argument('input', help='Input .tex file or directory')
    parser.add_argument('-o', '--output', help='Output filename')
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Enable verbose logging')
    parser.add_argument('--no-bib', action='store_true',
                       help='Skip bibliography processing')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        return 1
    
    # Find main tex file
    if input_path.is_dir():
        main_tex = find_main_tex_file(input_path)
        if not main_tex:
            logger.error("Could not find main .tex file in directory")
            return 1
    else:
        main_tex = input_path
    
    logger.info(f"Processing main file: {main_tex}")
    
    # Create output filename
    output_file = create_output_filename(main_tex, args.output)
    logger.info(f"Output will be written to: {output_file}")
    
    # Expand includes
    try:
        expanded_content = expand_includes(main_tex)
        logger.info(f"Expanded {len(expanded_content)} lines")
    except Exception as e:
        logger.error(f"Error expanding includes: {e}")
        return 1
    
    # Process bibliography
    bib_entries = []
    if not args.no_bib:
        citations = extract_citations(expanded_content)
        logger.info(f"Found {len(citations)} unique citations")
        
        if citations:
            bib_files = find_bib_files(main_tex.parent)
            logger.info(f"Found {len(bib_files)} .bib files")
            
            if bib_files:
                bib_entries = extract_bib_entries(bib_files, citations)
    
    # Write output
    try:
        with output_file.open('w', encoding='utf-8') as f:
            f.writelines(expanded_content)
            
            if bib_entries:
                f.write("\n\n% === Bibliography Entries for LLM Reference ===\n")
                f.write("% The following BibTeX entries correspond to citations in the document.\n")
                f.write("% This section is added for LLM tools to understand the references.\n\n")
                
                for entry in bib_entries:
                    f.write(entry)
                    f.write('\n\n')
            else:
                f.write("\n\n% === No Bibliography Entries Found ===\n")
        
        logger.info(f"Successfully wrote expanded file to {output_file}")
        return 0
        
    except Exception as e:
        logger.error(f"Error writing output file: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
