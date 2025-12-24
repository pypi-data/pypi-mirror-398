#!/usr/bin/env python3
"""
Generate documentation for all encoders from their source code.

This script:
1. Reads all encoder source files from src/usenc/encoders/
2. Extracts encoder information (name, description, parameters, examples)
3. Generates individual markdown files in docs/encoders/
4. Generates the main encoders.md listing all encoders
"""

import re
import sys
from pathlib import Path
from typing import Any, List, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from usenc.encoders import ENCODERS


def extract_docstring_parts(docstring: str) -> Tuple[str, str, List[str]]:
    """
    Extract parts from encoder docstring.

    Args:
        docstring: The class docstring

    Returns:
        tuple: (short_description, long_description, examples_list)
    """
    if not docstring:
        return "", "", []

    # Split into lines and clean
    lines = docstring.strip().split("\n")
    cleaned_lines = [line.strip() for line in lines]

    # First non-empty line is short description
    short_desc = ""
    long_desc_lines = []
    examples = []

    state = "short"  # short, long, examples

    for line in cleaned_lines:
        if not line and state == "short":
            state = "long"
            continue

        # Check if we're entering examples section
        if line.lower().startswith("examples:"):
            state = "examples"
            continue

        if state == "short":
            short_desc = line
        elif state == "long":
            long_desc_lines.append(line)
        elif state == "examples":
            # Parse example lines like "hello world -> hello%20world"
            examples.append(line)

    long_desc = "\n".join(long_desc_lines)

    return short_desc, long_desc, examples


def format_param_flag(param_name: str) -> str:
    """Convert parameter name to CLI flag format."""
    return f"--{param_name.replace('_', '-')}"


def generate_encoder_markdown(encoder_name: str, encoder_class: Any) -> str:
    """
    Generate markdown documentation for a single encoder.

    Args:
        encoder_name: Name of the encoder (e.g., 'url')
        encoder_class: The encoder class

    Returns:
        str: Markdown formatted documentation
    """
    # Extract information from docstring
    docstring = encoder_class.__doc__ or ""
    short_desc, long_desc, examples = extract_docstring_parts(docstring)

    # Build markdown document
    md = []

    # NAME section
    md.append("### NAME")
    md.append("")
    md.append(f"`{encoder_name}` - {short_desc}")
    md.append("")

    # DESCRIPTION section (if long description exists)
    if long_desc:
        md.append("### DESCRIPTION")
        md.append("")
        md.append(long_desc)
        md.append("")

    # OPTIONS section
    if hasattr(encoder_class, "params") and encoder_class.params:
        md.append("### OPTIONS")
        md.append("")

        for param_name, param_spec in encoder_class.params.items():
            flag = format_param_flag(param_name)
            help_text = param_spec.get("help", "")

            md.append("")
            md.append(f"#### {flag}")
            md.append('<div class="option-desc">')
            if help_text:
                md.append(help_text)
            md.append("</div>")

        md.append("")

    # EXAMPLES section
    if examples:
        md.append("### EXAMPLES")
        md.append("")
        md.append("Sample  |   Encoded")
        md.append("--- | ---")

        for example in examples:
            # Parse "input -> output" format
            if "->" in example:
                parts = example.split("->", 1)
                if len(parts) == 2:
                    input_str = parts[0].strip()
                    output_str = parts[1].strip()
                    md.append(f"`{input_str}` | `{output_str}`")

    return "\n".join(md) + "\n"


def generate_encoder_list() -> str:
    """
    Generate a markdown list of all available encoders.

    Returns:
        str: Markdown formatted list of encoders with descriptions
    """
    lines = []

    for encoder_name in sorted(ENCODERS.keys()):
        encoder_class = ENCODERS[encoder_name]

        # Extract short description from docstring
        docstring = encoder_class.__doc__ or ""
        short_desc, _, _ = extract_docstring_parts(docstring)

        # Add encoder to list with link to its documentation
        lines.append(
            f"- **[{encoder_name}](https://crashoz.github.io/usenc/encoders/{encoder_name}/)** - {short_desc}"
        )

    return "\n".join(lines)


def copy_readme(project_root: Path, docs_dir: Path):
    """
    Update README.md with the list of all available encoders and copy to docs/index.md.

    Args:
        project_root: Path to project root
        docs_dir: Path to docs directory
    """
    readme_src = project_root / "README.md"
    readme_dst = docs_dir / "index.md"

    if not readme_src.exists():
        print(f"  ⚠ Warning: README.md not found at {readme_src}")
        return

    # Read README content
    content = readme_src.read_text(encoding="utf-8")

    # Generate encoder list
    encoder_list = generate_encoder_list()

    # Find the "## Available Encoders" section and insert the list
    # Look for the section header and replace content until the next ## section
    pattern = r"(## Available Encoders\n\n).*?(\n\n## |\Z)"
    replacement = f"\\1{encoder_list}\\n\\n\\2"

    modified_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # Write modified content back to README.md
    readme_src.write_text(modified_content, encoding="utf-8")
    print("  ✓ Updated README.md with encoder list")

    # Write modified content to index.md
    readme_dst.write_text(modified_content, encoding="utf-8")
    print("  ✓ Copied README.md to docs/index.md")


def main():
    """Main function to generate all documentation."""
    # Get project paths
    project_root = Path(__file__).parent.parent
    docs_dir = project_root / "docs"
    encoders_dir = docs_dir / "encoders"

    # Create encoders directory if it doesn't exist
    encoders_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Generating Encoder Documentation")
    print("=" * 60)
    print()

    # Copy README.md to docs directory
    print("Copying README.md...")
    copy_readme(project_root, docs_dir)
    print()

    # Generate documentation for each encoder
    print(f"Found {len(ENCODERS)} encoders")
    print()

    for encoder_name in sorted(ENCODERS.keys()):
        encoder_class = ENCODERS[encoder_name]

        print(f"  ✓ Generating docs for '{encoder_name}'")

        # Generate the markdown documentation
        doc_content = generate_encoder_markdown(encoder_name, encoder_class)

        # Write to file
        doc_file = encoders_dir / f"{encoder_name}.md"
        doc_file.write_text(doc_content, encoding="utf-8")

    print()
    print(f"Generated {len(ENCODERS)} encoder documentation files")
    print(f"  → {encoders_dir}/")
    print()

    print("=" * 60)
    print("Documentation Generation Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
