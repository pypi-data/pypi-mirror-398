#!/usr/bin/env python3
"""Post-process generated markdown files to be MDX-compatible.

Escapes curly braces outside of code blocks to prevent MDX from
interpreting them as JSX expressions.
"""

import html
import re
import sys
from pathlib import Path


def decode_html_entities(content: str) -> str:
    """Decode HTML entities like &#x27; to actual characters."""
    return html.unescape(content)


def escape_angle_brackets(content: str) -> str:
    """Escape < that could be misinterpreted as JSX tags.

    MDX interprets <foo as JSX. We escape < when followed by
    characters that don't form valid HTML tags (numbers, symbols, etc).
    """
    # Escape < followed by a digit or other non-tag characters
    # Valid tag starts: letter, /, !
    content = re.sub(r'<(?=[0-9])', r'\\<', content)
    return content


def escape_curly_braces(content: str) -> str:
    """Escape { and } outside of code blocks."""
    lines = content.split('\n')
    result = []
    in_code_block = False

    for line in lines:
        # Track code block state
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            result.append(line)
            continue

        if in_code_block:
            result.append(line)
        else:
            # Escape curly braces outside code blocks
            line = line.replace('{', '\\{').replace('}', '\\}')
            result.append(line)

    return '\n'.join(result)


def process_file(filepath: Path) -> None:
    """Process a single markdown file."""
    content = filepath.read_text()
    # Decode HTML entities, escape angle brackets, then escape curly braces
    fixed = decode_html_entities(content)
    fixed = escape_angle_brackets(fixed)
    fixed = escape_curly_braces(fixed)
    if content != fixed:
        filepath.write_text(fixed)
        print(f'Fixed: {filepath}')


def main():
    if len(sys.argv) < 2:
        print('Usage: fix_mdx.py <directory>')
        sys.exit(1)

    directory = Path(sys.argv[1])
    if not directory.is_dir():
        print(f'Not a directory: {directory}')
        sys.exit(1)

    for md_file in directory.rglob('*.md'):
        process_file(md_file)


if __name__ == '__main__':
    main()
