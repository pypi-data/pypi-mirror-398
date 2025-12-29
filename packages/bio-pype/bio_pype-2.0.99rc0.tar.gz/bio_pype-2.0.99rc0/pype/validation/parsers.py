"""Markdown and YAML parsing utilities for validation.

This module provides utilities for parsing Markdown snippets and YAML files
used in bio_pype configuration.
"""

import re
from typing import Dict, List, Optional, Set, Tuple

from pype.validation.core import Location, ParsedSection, VariableInfo


class MarkdownSectionParser:
    """Parser for Markdown files with section-based structure.

    Bio_pype Markdown files use ## headers to define sections.
    This parser extracts those sections while respecting code blocks
    (## inside code blocks should not be treated as section headers).
    """

    @staticmethod
    def parse_sections(content: str) -> Dict[str, ParsedSection]:
        """Parse Markdown content into sections by ## headers.

        Args:
            content: Raw Markdown file content

        Returns:
            Dictionary mapping section name -> ParsedSection

        Example:
            content = '''# Title
            ## description
            Some description here

            ## arguments
            1. arg1
            '''
            sections = MarkdownSectionParser.parse_sections(content)
            # sections = {
            #     'description': ParsedSection('description', 'Some description...', 1, 2),
            #     'arguments': ParsedSection('arguments', '1. arg1', 4, 4)
            # }
        """
        sections: Dict[str, ParsedSection] = {}
        current_section: Optional[str] = None
        current_content: List[str] = []
        start_line: int = 0
        in_code_block: bool = False

        for line_num, line in enumerate(content.split("\n")):
            # Track code blocks to ignore ## inside them
            if line.strip().startswith("```"):
                in_code_block = not in_code_block

            # Only treat ## as section header if not inside code block
            if line.startswith("## ") and not in_code_block:
                # Save previous section
                if current_section is not None:
                    sections[current_section] = ParsedSection(
                        name=current_section,
                        content="\n".join(current_content),
                        start_line=start_line,
                        end_line=line_num - 1,
                    )

                # Start new section
                # Extract section name (lowercase for consistency)
                current_section = line[3:].strip().lower()
                current_content = []
                start_line = line_num
            else:
                current_content.append(line)

        # Save last section
        if current_section is not None:
            sections[current_section] = ParsedSection(
                name=current_section,
                content="\n".join(current_content),
                start_line=start_line,
                end_line=len(content.split("\n")) - 1,
            )

        return sections

    @staticmethod
    def parse_code_chunks(content: str) -> List[Dict[str, any]]:
        """Extract code chunks (``` blocks) from content.

        Returns a list of code chunks with their headers and content.

        Args:
            content: Raw content containing code blocks

        Returns:
            List of dicts with keys: {
                'header': str (first line after ```),
                'code': str (block content),
                'start_line': int,
                'end_line': int
            }
        """
        chunks = []
        in_block = False
        block_start = 0
        block_header = ""
        block_content = []

        for line_num, line in enumerate(content.split("\n")):
            if line.startswith("```") and not in_block:
                # Starting a code block
                in_block = True
                block_start = line_num
                block_header = ""
                block_content = []
            elif line.startswith("```") and in_block:
                # Ending a code block
                in_block = False
                chunks.append(
                    {
                        "header": block_header,
                        "code": "\n".join(block_content),
                        "start_line": block_start,
                        "end_line": line_num,
                    }
                )
            elif in_block and block_header == "":
                # First line after ``` is the header
                block_header = line
            elif in_block:
                block_content.append(line)

        return chunks


class VariableTracker:
    """Track variable definitions and usage in Markdown content.

    Tracks Python-style string formatting variables: %(var_name)format
    Format can be: s, i, f(Python format specifiers)

    This tracks variables used in code, not bash variables like ${var}.
    """

    # Pattern for Python-style variable formatting: %(varname)format
    VARIABLE_PATTERN = re.compile(r"%\((\w+)\)[sif]")

    @staticmethod
    def find_variables(content: str) -> Dict[str, VariableInfo]:
        """Find all Python-style variables in content.

        Args:
            content: Raw content to scan for variables

        Returns:
            Dictionary mapping variable name -> VariableInfo

        Example:
            content = '''output = "%(output)s"
            count = %(count)d
            '''
            vars = VariableTracker.find_variables(content)
            # vars = {
            #     'output': VariableInfo('output', [Location(0, 9, 19), ...]),
            #     'count': VariableInfo('count', [Location(1, 8, 17)])
            # }
        """
        variables: Dict[str, VariableInfo] = {}

        for line_num, line in enumerate(content.split("\n")):
            for match in VariableTracker.VARIABLE_PATTERN.finditer(line):
                var_name = match.group(1)
                location = Location(
                    line=line_num,
                    start_char=match.start(),
                    end_char=match.end(),
                )

                if var_name not in variables:
                    variables[var_name] = VariableInfo(name=var_name)

                variables[var_name].locations.append(location)

        return variables

    @staticmethod
    def get_defined_variables(arguments_section: str) -> Set[str]:
        """Extract variable names defined in arguments section.

        Parses numbered argument format:
        1. arg_name/shortcut
        2. other_arg

        Args:
            arguments_section: Content of ## arguments section

        Returns:
            Set of variable names defined as arguments
        """
        defined = set()

        # Pattern: line starts with digits followed by . and argument name
        arg_pattern = re.compile(r"^\d+\.\s+(\w+)")

        for line in arguments_section.split("\n"):
            match = arg_pattern.match(line.strip())
            if match:
                arg_name = match.group(1)
                defined.add(arg_name)

        return defined


class CodeChunkHeaderParser:
    """Parse code chunk headers (the @interpreter, options line).

    Different sections have different header formats:
    - snippet: @interpreter, chunk_name [, options]
    - results: @interpreter, parser_format [, options]
    - name: @interpreter [, options]
    """

    @staticmethod
    def parse_snippet_chunk_header(header: str) -> Dict[str, any]:
        """Parse a snippet code chunk header.

        Format: @interpreter, chunk_name [, namespace=prog] [, stdout=chunk]

        Args:
            header: Header line (starts with @)

        Returns:
            Dict with keys: {
                'interpreter': str,
                'chunk_name': str,
                'is_valid': bool,
                'errors': List[str],
                'options': Dict[str, str]
            }
        """
        result = {
            "interpreter": "",
            "chunk_name": "",
            "is_valid": True,
            "errors": [],
            "options": {},
        }

        if not header.startswith("@"):
            result["is_valid"] = False
            result["errors"].append("Header must start with @")
            return result

        # Remove @ and split by comma
        parts = [p.strip() for p in header.lstrip("@").split(",")]

        if len(parts) < 2:
            result["is_valid"] = False
            result["errors"].append(
                "Snippet chunk header needs: @interpreter, chunk_name"
            )
            return result

        result["interpreter"] = parts[0]
        result["chunk_name"] = parts[1]

        # Validate chunk name format
        if not re.match(r"^[a-zA-Z_]\w*$", result["chunk_name"]):
            result["is_valid"] = False
            result["errors"].append(
                f"Invalid chunk name '{result['chunk_name']}': "
                "must start with letter/underscore, contain only word chars"
            )

        # Parse options
        for opt_part in parts[2:]:
            if "=" in opt_part:
                key, val = opt_part.split("=", 1)
                result["options"][key.strip()] = val.strip()
            else:
                result["errors"].append(f"Invalid option format: {opt_part}")
                result["is_valid"] = False

        return result

    @staticmethod
    def parse_results_chunk_header(header: str) -> Dict[str, any]:
        """Parse a results code chunk header.

        Format: @interpreter, parser_format [, check_results=true/false]

        Args:
            header: Header line (starts with @)

        Returns:
            Dict with keys: {
                'interpreter': str,
                'parser_format': str (yaml or json),
                'check_results': bool,
                'is_valid': bool,
                'errors': List[str]
            }
        """
        result = {
            "interpreter": "",
            "parser_format": "",
            "check_results": True,
            "is_valid": True,
            "errors": [],
        }

        if not header.startswith("@"):
            result["is_valid"] = False
            result["errors"].append("Header must start with @")
            return result

        parts = [p.strip() for p in header.lstrip("@").split(",")]

        if len(parts) < 2:
            result["is_valid"] = False
            result["errors"].append(
                "Results chunk header needs: @interpreter, parser_format"
            )
            return result

        result["interpreter"] = parts[0]
        parser_format = parts[1]

        if parser_format not in ("yaml", "json"):
            result["is_valid"] = False
            result["errors"].append(
                f"Invalid parser format '{parser_format}': must be 'yaml' or 'json'"
            )
        else:
            result["parser_format"] = parser_format

        # Parse optional check_results parameter
        for opt_part in parts[2:]:
            if opt_part.lower() in ("false", "0", "no"):
                result["check_results"] = False
            elif opt_part.startswith("check_results="):
                val = opt_part.split("=", 1)[1].lower()
                result["check_results"] = val not in ("false", "0", "no")

        return result

    @staticmethod
    def parse_name_chunk_header(header: str) -> Dict[str, any]:
        """Parse a name code chunk header.

        Format: @interpreter (optional, defaults to /bin/sh)

        Args:
            header: Header line (can start with @, or be empty)

        Returns:
            Dict with keys: {
                'interpreter': str,
                'is_valid': bool,
                'errors': List[str]
            }
        """
        result = {
            "interpreter": "/bin/sh",  # Default
            "is_valid": True,
            "errors": [],
        }

        if not header or header.strip() == "":
            # Default is fine
            return result

        if header.startswith("@"):
            result["interpreter"] = header.lstrip("@").strip()
        else:
            result["interpreter"] = header.strip()

        return result


class IODeclarationParser:
    """Parse input/output declarations from blockquotes.

    Format:
        > _input_: var1 var2*
        > _output_: result1
    """

    # Patterns for I/O declarations
    INPUT_PATTERN = re.compile(r"_input_\s*:\s*(.+)")
    OUTPUT_PATTERN = re.compile(r"_output_\s*:\s*(.+)")

    @staticmethod
    def parse_io_declarations(content: str) -> Tuple[List[str], List[str]]:
        """Parse input and output declarations from blockquote content.

        Handles wildcards:
        - * (any)
        - ~ (one level)
        - .. (pair)

        Args:
            content: Content of blockquotes (lines starting with >)

        Returns:
            Tuple of (input_vars, output_vars) as lists of variable names
        """
        inputs = []
        outputs = []

        for line in content.split("\n"):
            line = line.strip()
            if line.startswith(">"):
                line = line[1:].strip()

            # Check for input declaration
            match = IODeclarationParser.INPUT_PATTERN.search(line)
            if match:
                vars_str = match.group(1)
                # Split by whitespace, remove wildcards
                for var in vars_str.split():
                    # Remove wildcards (*, ~, ..)
                    clean_var = var.rstrip("*~.")
                    if clean_var:
                        inputs.append(clean_var)

            # Check for output declaration
            match = IODeclarationParser.OUTPUT_PATTERN.search(line)
            if match:
                vars_str = match.group(1)
                for var in vars_str.split():
                    clean_var = var.rstrip("*~.")
                    if clean_var:
                        outputs.append(clean_var)

        return inputs, outputs
