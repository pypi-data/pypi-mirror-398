"""Snippet management and execution system.

This module handles all aspects of snippet processing:
- Loading snippets from Python and Markdown files
- Validating snippet configurations
- Processing snippet arguments
- Managing snippet execution
- Tracking snippet results

Key classes:
- Snippet: Handler for Python-based snippets
- SnippetMd: Handler for Markdown-based snippets
- ChunksCommands: Manages code chunk execution
"""

import importlib
import json
import os
import re
from subprocess import PIPE, Popen
from typing import Any, Dict, List, Optional

import yaml

from pype.__config__ import PYPE_SNIPPETS, PYPE_TMP
from pype.argparse import ArgumentParser
from pype.exceptions import (
    SnippetError,
    SnippetNotFoundError,
    SnippetResultsArgumentError,
    SnippetResultsTemplateSobstitutionError,
)
from pype.misc import (
    basename_no_extension,
    bases_format,
    generate_uid,
    package_files,
    package_modules,
)
from pype.process import Command


def snippets_modules_list(
    snippets_dict: Dict[str, Any], pype_snippets: Any = PYPE_SNIPPETS
) -> Dict[str, Any]:
    """Load Python snippet modules.

    Args:
        snippets_dict: Dictionary to store loaded snippets

    Returns:
        Updated dictionary with loaded snippets

    Raises:
        SnippetError: If snippet loading fails
    """
    try:
        snippets_modules = package_modules(pype_snippets)
        for snippets_module in sorted(snippets_modules):
            snippet_name = snippets_module.split(".")[-1]
            snippet_i = Snippet(pype_snippets, snippet_name, snippets_module)
            snippets_dict[snippet_name] = snippet_i
        return snippets_md_list(snippets_dict, pype_snippets)
    except Exception as e:
        raise SnippetError(f"Failed to load snippet modules: {str(e)}")


def snippets_md_list(
    snippets_dict: Dict[str, Any], pype_snippets: Any = PYPE_SNIPPETS
) -> Dict[str, Any]:
    """Load Markdown snippet modules.

    Args:
        snippets_dict: Dictionary to store loaded snippets

    Returns:
        Updated dictionary with loaded snippets

    Raises:
        SnippetError: If snippet loading fails
    """
    try:
        snippets_modules = package_files(pype_snippets, "md")
        for snippets_module in sorted(snippets_modules):
            snippet_name = os.path.basename(os.path.splitext(snippets_module)[0])
            snippet_i = SnippetMd(pype_snippets, snippet_name, snippets_module)
            snippets_dict[snippet_name] = snippet_i
        return snippets_dict
    except Exception as e:
        raise SnippetError(f"Failed to load snippet modules: {str(e)}")


class Snippet:
    """Handler for Python-based snippets.

    Attributes:
        module_name: Name of the snippet module
        mod: Loaded Python module object
        check_results: Whether to validate result files after execution (default: True)
    """

    def __init__(self, parent: Any, module_name: str, module_def: str):
        """Initialize Python snippet.

        Args:
            parent: Parent module/package
            module_name: Name of snippet module
            module_def: Module definition/path

        Raises:
            SnippetNotFoundError: If module cannot be loaded
        """
        try:
            self.module_name = module_name

            # Try to get as attribute first (if already cached)
            self.mod: Optional[Any] = getattr(parent, self.module_name, None)

            # If not found, try dynamic import with full module path
            if self.mod is None:
                self.mod = importlib.import_module(module_def)
                # Cache it in parent for future access
                setattr(parent, self.module_name, self.mod)
        except Exception:
            raise SnippetNotFoundError(module_name)

    def check_results_enabled(self) -> bool:
        """Check if result file validation is enabled.

        Can be overridden by modules by defining check_results() method.

        Returns:
            True if results should be validated, False otherwise
        """
        try:
            return self.mod.check_results()
        except AttributeError:
            return True

    def requirements(self) -> Dict[str, Any]:
        """Get snippet requirements."""
        return self.mod.requirements()

    def friendly_name(self, args: Dict[str, Any]) -> str:
        """Get friendly name for the snippet."""
        try:
            return self.mod.friendly_name(args)
        except AttributeError:
            return self.module_name

    def results(self, args: Dict[str, Any]) -> Any:
        """Get results from the snippet."""
        try:
            return self.mod.results(args)
        except KeyError as e:
            missing_key = e.args[0]
            # Find which template variables are used in the code
            available_keys = set(args.keys())
            raise SnippetResultsArgumentError(
                snippet_name=self.module_name,
                missing_key=missing_key,
                available_keys=available_keys,
            ) from e

    def add_parser(self, subparsers: Any) -> Any:
        """Add argument parser for the snippet."""
        return self.mod.add_parser(subparsers, self.module_name)

    def snippet(self, parser: Any, args: Dict[str, Any], profile: Any, log: Any) -> Any:
        """Execute the snippet."""
        program = getattr(self.mod, self.module_name)
        return program(parser, self.module_name, args, profile, log)


class SnippetMd:
    """Handler for Markdown-based snippets.

    Attributes:
        module_name: Name of the snippet module
        mod: Loaded Markdown module object
    """

    def __init__(self, parent: Any, module_name: str, module_def: str):
        """Initialize Markdown snippet.

        Args:
            parent: Parent module/package
            module_name: Name of snippet module
            module_def: Module definition/path

        Raises:
            SnippetNotFoundError: If module cannot be loaded
        """
        try:
            self.module_name = module_name
            self.parse(module_def)
        except Exception as e:
            raise SnippetNotFoundError(module_name)
        self.cached_results = None
        self.cached_name = None

    def requirements(self) -> Dict[str, Any]:
        """Get snippet requirements."""
        requirements_chunk = self.mod["requirements"].strip().split("\n")
        requirements = None
        if "yaml" in requirements_chunk[0]:
            requirements = yaml.safe_load(
                "\n".join([i for i in requirements_chunk if not i.startswith("```")])
            )
        elif "json" in requirements_chunk[0]:
            requirements = json.load(
                "\n".join([i for i in requirements_chunk if not i.startswith("```")])
            )
        return requirements

    def check_results_enabled(self) -> bool:
        """Check if result file validation is enabled.

        Reads from the results chunk header (defaults to True).

        Returns:
            True if results should be validated, False otherwise
        """
        try:
            self.parse_results_chunks(PYPE_TMP)
            if self.results_chunk is not None:
                return self.results_chunk.check_results
        except (KeyError, AttributeError):
            pass
        return True

    def friendly_name(self, args: Dict[str, Any]) -> str:
        """Get friendly name for the snippet."""
        if self.cached_name is None:
            args = self.return_args(args)
            try:
                self.parse_name_chunks(PYPE_TMP)
                self.name_chunk.write_code(args)
                self.cached_name = self.name_chunk.run()
            except KeyError:
                self.cached_name = self.module_name
        return self.cached_name

    def results(self, args: Dict[str, Any]) -> Any:
        """Get results from the snippet."""
        if self.cached_results is None:
            args = self.return_args(args)
            self.parse_results_chunks(PYPE_TMP)
            self.results_chunk.write_code(args)
            self.cached_results = self.results_chunk.run()
        return self.cached_results

    def add_parser(self, subparsers: Any) -> Any:
        """Add argument parser for the snippet."""
        description = " ".join(
            [t.strip() for t in self.mod["description"].strip().split("\n")]
        )
        return subparsers.add_parser(self.module_name, help=description, add_help=False)

    def argparse(self, parser: Any) -> Any:
        """Parse arguments for the snippet."""
        arguments = ArgumentList(self.module_name, self.mod["arguments"])
        return arguments.add_to_parser(self.add_parser(parser))

    def snippet(
        self, parser: Any, args: Dict[str, Any], profile: Any, log: Any
    ) -> None:
        """Execute the snippet."""
        self.parse_snippet_chunks(log.__path__)
        args = self.argparse(parser).parse_args(args)
        args = vars(args)
        commands = ChunksCommands(log, profile)
        commands.add_chunks(
            self.snippet_chunks, args, self.results(args), self.requirements()
        )
        commands.run_chunks()

    def parse(self, file_name: str) -> None:
        """Parse the Markdown file."""
        self.mod = {}
        keywords = (
            "description",
            "requirements",
            "results",
            "arguments",
            "snippet",
            "name",
        )
        k_idx = None
        context = None
        context_txt = ""
        with open(file_name, "rt") as input_md:
            for line in input_md:
                if line.startswith("## "):
                    if context is not None:
                        self.mod[context] = context_txt
                    k_idx = None
                    context = None
                    context_txt = ""
                    line = line.strip().split(" ")
                    if any(k in line for k in keywords):
                        for item in line:
                            try:
                                k_idx = keywords.index(item)
                            except ValueError:
                                pass
                        context = keywords[k_idx]
                else:
                    context_txt += line
            self.mod[context] = context_txt

    def parse_snippet_chunks(self, pwd: str) -> None:
        """Parse snippet chunks."""
        self.snippet_chunks = []
        chunk_header = []
        open_chunk = False
        lines_splits = (line for line in self.mod["snippet"].split("\n"))
        for line in lines_splits:
            if line.startswith(">") and open_chunk is False:
                chunk_header.append(line.lstrip(">").strip())
            elif line.startswith("```") and open_chunk is False:
                chunk = CodeChunk(self.module_name, next(lines_splits), pwd)
                chunk.io_header = chunk_header
                chunk_header = []
                self.snippet_chunks.append(chunk)
                open_chunk = True
            elif line.startswith("```") and open_chunk is True:
                open_chunk = False
            elif open_chunk is True:
                self.snippet_chunks[len(self.snippet_chunks) - 1].add_code(line)

    def parse_results_chunks(self, pwd: str) -> None:
        """Parse results chunks."""
        self.results_chunk = None
        open_chunk = False
        lines_splits = (line for line in self.mod["results"].split("\n"))
        for line in lines_splits:
            if line.startswith("```") and open_chunk is False:
                self.results_chunk = ResultsChunk(
                    self.module_name, next(lines_splits), pwd
                )
                open_chunk = True
            elif line.startswith("```") and open_chunk is True:
                open_chunk = False
            elif open_chunk is True:
                self.results_chunk.add_code(line)

    def parse_name_chunks(self, pwd: str) -> None:
        """Parse name chunks."""
        self.name_chunk = None
        open_chunk = False
        lines_splits = (line for line in self.mod["name"].split("\n"))
        for line in lines_splits:
            if line.startswith("```") and open_chunk is False:
                header = next(lines_splits)
                if header.startswith("@"):
                    self.name_chunk = NameChunk(self.module_name, header, pwd)
                else:
                    self.name_chunk = NameChunk(self.module_name, str(), pwd)
                    self.name_chunk.add_code(header)
                open_chunk = True
            elif line.startswith("```") and open_chunk is True:
                open_chunk = False
            elif open_chunk is True:
                self.name_chunk.add_code(line)

    def return_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Return arguments for the snippet."""
        if any(k.startswith("-") for k in args.keys()):
            matching_args = {}
            parser = ArgumentParser(prog="pype", description=self.module_name)
            subparsers = parser.add_subparsers(dest="modules")
            arg_parser = self.argparse(subparsers)
            # FIXME using the internal _actions attribute is an hack
            # future releases of argparse may broke this behavior
            # (hover it's not being the case in the last 5 or so
            # years :)).
            for action in arg_parser._actions:
                options = action.option_strings
                dest = action.dest
                for key in args:
                    if key in options:
                        matching_args[dest] = args[key]
            args = matching_args
        return args


# FIXME Code to implement the SnippetMd class
# it will need to be refactored after a
# final implementation


class CodeChunk:
    """Handler for code chunks within snippets.

    Attributes:
        snippet_name: Name of the snippet
        id: Unique identifier for the chunk
        program: Program to execute the chunk
        attr: Additional attributes for the chunk
        code: List of code lines
        io_header: Input/output header information
        code_file: Path to the code file
    """

    def __init__(self, snippet_name: str, header: str, code_path: str):
        """Initialize code chunk.

        Args:
            snippet_name: Name of the snippet
            header: Header information for the chunk
            code_path: Path to the code file
        """
        self.snippet_name = snippet_name
        self.parse_header(header)
        self.code = []
        self.io_header = str()
        random_id = generate_uid(n=4)
        self.code_file = os.path.join(
            code_path, "%s_%s_%s" % (random_id, self.snippet_name, self.id)
        )

    def add_code(self, line: str) -> None:
        """Add code line to the chunk."""
        self.code.append(line)

    def parse_header(self, header: str) -> None:
        """Parse header information for the chunk."""
        header = [h.strip() for h in header.lstrip("@").split(",")]
        try:
            self.id = header[1]
            self.program = header[0]
            self.attr = {}
            for attr in header[2:]:
                split_attr = attr.split("=")
                self.attr[split_attr[0]] = split_attr[1]
        except IndexError:
            raise (
                Exception(
                    "Unformatted header %s for snippet %s"
                    % (", ".join(header), self.snippet_name)
                )
            )

    def write_code(self, args: Dict[str, Any], log: Optional[Any] = None) -> None:
        """Write code to the file."""
        args_replace = {}
        for arg_key in args:
            arg_value = args[arg_key]
            if isinstance(arg_value, list):
                args_replace[arg_key] = " ".join(arg_value)
            else:
                args_replace[arg_key] = arg_value

        try:
            code_main = "\n".join(self.code) % args_replace
        except KeyError as e:
            missing_key = e.args[0]
            # Find which template variables are used in the code
            template_vars = set(re.findall(r"%\((\w+)\)", "\n".join(self.code)))
            available_keys = set(args_replace.keys())
            missing_keys = template_vars - available_keys

            raise SnippetResultsTemplateSobstitutionError(
                snippet_name=self.snippet_name,
                chunk_id=self.id,
                missing_key=missing_key,
                template_vars=template_vars,
                available_keys=available_keys,
                missing_keys=missing_keys,
            ) from e
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Template substitution failed in snippet '{self.snippet_name}', chunk '{self.id}': {e}"
            ) from e

        with open(self.code_file, "wt") as code_file:
            code_file.write("#!%s\n\n" % self.program)
            code_file.write(code_main)
        os.chmod(self.code_file, 0o760)
        if log is not None:
            log.log.info("Write chunk %s code into %s" % (self.id, self.code_file))

    def set_io(self, args: Dict[str, Any]) -> None:
        """Set input/output for the chunk."""
        self.input = []
        self.output = []
        items = None
        io_switch = None
        for line in self.io_header:
            line = line.split(":")
            if len(line) == 2:
                items = line[1].split()
                io_switch = line[0].strip()
            elif len(line) == 1:
                items = line[0].split()
            for item in items:
                item = item.strip()
                if io_switch == "_input_":
                    wildcard = ""
                    if item.endswith("*"):
                        item = item[:-1]
                        wildcard = "(*)"
                    if item.endswith("~"):
                        item = item[:-1]
                        wildcard = "(~)"
                    elif item.endswith(".."):
                        item = item[:-2]
                        wildcard = "(..)"
                    value = args[item]
                    if isinstance(value, list):
                        self.input += value
                    else:
                        self.input.append("%s%s" % (value, wildcard))
                elif io_switch == "_output_":
                    self.output.append(args[item])


class ResultsChunk(CodeChunk):
    """Handler for results chunks within snippets.

    Attributes:
        check_results: Whether to validate result files after execution (default: True)
    """

    def parse_header(self, header: str) -> None:
        """Parse header information for the chunk.

        Header format: @program, parser[, check_results]
        Examples:
            @/bin/sh, yaml
            @/bin/sh, yaml, check_results=False
            @/bin/sh, yaml, False
        """
        header = [h.strip() for h in header.lstrip("@").split(",")]
        try:
            self.parser = header[1]
            self.program = header[0]
            self.id = "results"
            self.check_results = True  # Default to True

            # Parse optional check_results attribute
            if len(header) > 2:
                for attr in header[2:]:
                    if attr.lower() in ("false", "0", "no"):
                        self.check_results = False
                    elif attr.startswith("check_results="):
                        value = attr.split("=")[1].lower()
                        self.check_results = value not in ("false", "0", "no")
        except IndexError:
            raise Exception(
                "Unformatted header %s for snippet %s"
                % (", ".join(header), self.snippet_name)
            )

    def run(self) -> Any:
        """Run the results chunk."""
        parsed_results = None
        command = Popen([self.code_file], stdin=PIPE, stdout=PIPE)
        results = command.communicate()
        if self.parser == "yaml":
            parsed_results = yaml.safe_load(results[0])
        elif self.parser == "json":
            parsed_results = json.loads(results[0])
        os.remove(self.code_file)
        return parsed_results


class NameChunk(CodeChunk):
    """Handler for name chunks within snippets."""

    def parse_header(self, header: str) -> None:
        """Parse header information for the chunk."""
        if header == "":
            self.program = "/bin/bash"
        else:
            header = [h.strip() for h in header.lstrip("@").split(",")]
            self.program = header[0]
        self.id = "friendly_name"

    def run(self) -> str:
        """Run the name chunk."""
        command = Popen([self.code_file], stdin=PIPE, stdout=PIPE)
        results = command.communicate()
        os.remove(self.code_file)
        return results[0].strip().decode("utf-8")


class ArgumentList:
    """Handler for argument lists within snippets."""

    def __init__(self, snippet_name: str, text: str):
        """Initialize argument list.

        Args:
            snippet_name: Name of the snippet
            text: Argument list text
        """
        self.snippet_name = snippet_name
        self.text = text
        self.indent = 4
        self.index_re = re.compile(r"\b\d+\b")
        self.arg_re = re.compile(r"^[ ]{0,%d}\d+\.[ ]+(.*)" % (self.indent - 1))
        self.opt_re = re.compile(r"-\s*([^\n]+):")
        self.arguments = []
        self.parse_text(text)

    def parse_text(self, text: str) -> None:
        """Parse argument list text."""
        index_list = 0
        last_option = None
        for line in text.split("\n"):
            if self.arg_re.match(line):
                index_list = int(self.index_re.findall(line)[0])
                arg = self.arg_re.findall(line)[0]
                self.arguments.append({})
                self.arguments[index_list - 1]["argument"] = arg
                self.arguments[index_list - 1]["options"] = {}

            elif index_list > 0:
                text = line.strip()
                if self.opt_re.match(text):
                    last_option = self.opt_re.findall(text)[0]
                    text_option = text.split(":", 1)[1].strip()
                    self.arguments[index_list - 1]["options"][last_option] = text_option
                else:
                    if len(text) == 0:
                        pass
                    else:
                        self.arguments[index_list - 1]["options"][last_option] += (
                            " %s" % text
                        )

    def add_to_parser(self, parser: ArgumentParser) -> ArgumentParser:
        """Add arguments to the parser."""
        type_dict = {"str": str, "int": int, "float": float}
        for argument in self.arguments:
            arg = argument["argument"].split("/")
            for i in range(len(arg)):
                if len(arg[i]) == 1:
                    arg[i] = "-%s" % arg[i]
                else:
                    arg[i] = "--%s" % arg[i]
            parser_opts = (
                "help",
                "default",
                "required",
                "nargs",
                "type",
                "action",
                "choices",
            )
            arg_opts = {}
            for opt_key in argument["options"]:
                if opt_key in parser_opts:
                    if opt_key == "required":
                        if argument["options"][opt_key] == "true":
                            arg_opts[opt_key] = True
                    elif opt_key == "type":
                        arg_opts[opt_key] = type_dict[argument["options"][opt_key]]
                    elif opt_key == "choices":
                        if "," in argument["options"][opt_key]:
                            arg_opts[opt_key] = [
                                choice.strip()
                                for choice in argument["options"][opt_key].split(",")
                            ]
                        else:
                            arg_opts[opt_key] = [
                                choice.strip()
                                for choice in argument["options"][opt_key].split()
                            ]
                    else:
                        arg_opts[opt_key] = argument["options"][opt_key]
            parser.add_argument(*arg, **arg_opts)
        return parser


class ChunksCommands:
    """Handler for managing and executing chunks of commands."""

    def __init__(self, log: Any, profile: Any):
        """Initialize chunks commands.

        Args:
            log: Logger object
            profile: Profile object
        """
        self.log = log
        self.profile = profile
        self.commands = {}
        self.run_order = []

    def add_chunks(
        self,
        chunks: List[CodeChunk],
        args: Dict[str, Any],
        results: Dict[str, Any],
        requirements: Dict[str, Any],
    ) -> None:
        """Add chunks to the commands.

        Args:
            chunks: List of code chunks
            args: Arguments for the chunks
            results: Results from the chunks
            requirements: Requirements for the chunks
        """
        profile_dict = {
            "profile_%s" % key: val for key, val in self.profile.files.items()
        }
        results_dict = {"results_%s" % key: val for key, val in results.items()}
        requirements_dict = {
            "requirements_%s" % key: val for key, val in requirements.items()
        }
        try:
            mem_req_mb = int(
                bases_format(requirements_dict["requirements_mem"]) / (1000 * 1000)
            )
            requirements_dict["requirements_mem"] = mem_req_mb
        except KeyError:
            pass
        profile_genome_build = {"profile_genome_build": self.profile.genome_build}
        tmp_dict = {"pype_tmp": PYPE_TMP}
        extra_args = {
            **args,
            **profile_dict,
            **results_dict,
            **tmp_dict,
            **requirements_dict,
            **profile_genome_build,
        }
        for chunk in chunks:
            chunk.set_io(extra_args)
            chunk.write_code(extra_args, self.log)
            self.commands[chunk.id] = Command(
                chunk.code_file, self.log, self.profile, chunk.id
            )
            for input_file in chunk.input:
                if input_file.endswith("(*)"):
                    input_file = input_file[:-3]
                    self.commands[chunk.id].add_input(input_file, match="recursive")
                elif input_file.endswith("(~)"):
                    input_path = os.path.dirname(input_file)
                    self.commands[chunk.id].add_input(input_path)
                elif input_file.endswith("(..)"):
                    input_file = input_file[:-4]
                    input_file = os.path.join(
                        os.path.dirname(input_file), basename_no_extension(input_file)
                    )
                    self.commands[chunk.id].add_input(input_file, match="recursive")
                else:
                    self.commands[chunk.id].add_input(input_file)
            for output in chunk.output:
                self.commands[chunk.id].add_output(output)
            try:
                self.commands[chunk.id].add_namespace(
                    self.profile.programs[chunk.attr["namespace"]]
                )
            except KeyError:
                self.log.log.error(
                    "Failed to load a namespace for chunk %s "
                    "in snippet %s" % (chunk.id, chunk.snippet_name)
                )
        for chunk in chunks:
            try:
                stdout_to = chunk.attr["stdout"]
                self.commands[stdout_to].pipe_in(
                    self.commands[chunk.id], local_script=True
                )
            except KeyError:
                self.run_order.append(chunk.id)

    def run_chunks(self) -> None:
        """Run the chunks."""
        for chunk_id in self.run_order:
            self.commands[chunk_id].release_stdout()
            self.commands[chunk_id].run(local_script=True)
            self.commands[chunk_id].close()
