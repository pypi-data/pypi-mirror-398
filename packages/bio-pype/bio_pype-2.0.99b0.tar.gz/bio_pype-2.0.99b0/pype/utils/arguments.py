"""Argument handling system for bio_pype.

This module provides functionality for:
- Processing command line arguments
- Handling pipeline configuration arguments
- Managing batch processing arguments
- Converting between argument formats

Key components:
- PipelineItemArguments: Container for pipeline arguments
- Argument: Base class for single arguments
- CompositeArgument: Combined arguments from multiple sources
- BatchFileArgument: Arguments from batch files
- BatchListArgument: Arguments from list batches
- ConstantArgument: Static argument values
"""

import re
from copy import copy
from typing import Any, Dict, List, Optional, Union

from pype.exceptions import ArgumentError
from pype.misc import xopen
from pype.modules.snippets import PYPE_SNIPPETS_MODULES


def compose_batch_description(
    batch_description: Dict[str, Any], str_description: str
) -> str:
    """Create help text for batch arguments describing file format and columns.

    Generates user-friendly help text that explains the structure of batch
    input files, including required and optional column headers, and how
    they map to snippet arguments.

    Args:
        batch_description: Dictionary with keys:
            - 'required': List of required column names
            - 'optional': (Optional) List of optional column names
            - 'snippet': Name of the snippet being executed
        str_description: Base description string to prepend to the output

    Returns:
        Formatted help text combining batch configuration details and
        instructions for using the batch file.

    Example:
        batch_desc = {
            'required': ['sample_id', 'input_file'],
            'optional': ['output_dir'],
            'snippet': 'process_sample'
        }
        help_text = compose_batch_description(
            batch_desc,
            'Process multiple samples from a batch file'
        )
        # Returns text explaining the tab-separated format with 2 required
        # columns, 1 optional column, and instructions to check the snippet
        # help for full argument details.
    """
    columns_names = batch_description["required"]
    try:
        optional_columns_names = batch_description["optional"]
    except KeyError:
        optional_columns_names = None
    snippet = batch_description["snippet"]
    if optional_columns_names:
        description = (
            "A tab separated text file that needs to have %i column "
            "headers:\n  %s\nAnd optionally the column headers:\n  %s\n"
            "Each row in the batch file will be independently \nrun "
            "by the "
            "snippet %s"
        ) % (
            len(columns_names),
            "\n  ".join(columns_names),
            "\n ".join(optional_columns_names),
            snippet,
        )
    else:
        description = (
            "A tab separated text file that needs to have %i column "
            "headers:\n  %s\nEach row in the batch file will be "
            "independently \nrun by the "
            "snippet %s"
        ) % (len(columns_names), "\n  ".join(columns_names), snippet)
    description = (
        "%s\nFor more details on the batch file column names "
        "see the help message at:\n    pype snippets %s\n"
        "Where each argument corresponds to a column in the "
        "batch file" % (description, snippet)
    )
    return "%s\n%s" % (str_description, description)


def get_arg_from_string(arg_string: str) -> Dict[str, Optional[str]]:
    """Extract argument name and type from format string.

    Args:
        arg_string: Argument string in format '%(name)s' or similar

    Returns:
        Dict with 'arg' and 'arg_type' keys
    """
    types_dict = {"s": "str", "i": "int", "f": "float"}
    arg_tag_str = r"\%\(.+\)[s,i,f]"
    if re.match(arg_tag_str, arg_string):
        arg_type = types_dict[arg_string[arg_string.find(")") + 1]]
        arg = arg_string[arg_string.find("%(") + 2 : arg_string.find(")")]
    else:
        arg_type = None
        arg = None
    return {"arg": arg, "arg_type": arg_type}


def __add_argument_by_type__(argument_type: str) -> Any:
    arg_type_fn_dict = {
        "composite_arg": CompositeArgument,
        "batch_list_arg": BatchListArgument,
        "batch_file_arg": BatchFileArgument,
        "constant_arg": ConstantArgument,
        "argv_arg": Argument,
    }
    try:
        return arg_type_fn_dict[argument_type]
    except KeyError:
        raise ArgumentError(f"Invalid argument type: {argument_type}")


class PipelineItemArguments:
    """Container for pipeline item arguments.

    Collects and manages arguments defined in pipeline YAML files.
    Handles different argument types and their conversion to command line format.
    """

    def __init__(self):
        self.arguments: List[Any] = []

    def add_argument(
        self, argument: Dict[str, Any], argument_type: str = "argv_arg"
    ) -> None:
        """Add argument of specified type.

        Args:
            argument: Argument definition dictionary
            argument_type: Type of argument to create

        Raises:
            ArgumentError: If argument type is invalid
        """
        try:
            self.arguments.append(__add_argument_by_type__(argument_type)(argument))
        except KeyError as e:
            raise ArgumentError(f"Invalid argument type: {argument_type}")

    def to_dict(self, args_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Convert arguments to dictionary format.

        Args:
            args_dict: Optional existing arguments dictionary

        Returns:
            Dictionary of processed arguments
        """
        res_args = {}
        batch_argv = []
        for argument in self.arguments:
            arg_argv = argument.to_argv(args_dict)
            if argument.type.startswith("batch_"):
                batch_argv = arg_argv
            else:
                if arg_argv[0] in res_args:
                    arg_val = res_args[arg_argv[0]]
                    arg_new = arg_argv[1]

                    # Handle combination of existing and new values
                    if isinstance(arg_val, list) and isinstance(arg_new, list):
                        # Both are lists: extend to flatten
                        res_args[arg_argv[0]] = arg_val + arg_new
                    elif isinstance(arg_val, list):
                        # arg_val is list, arg_new is single item
                        res_args[arg_argv[0]] = arg_val + [arg_new]
                    elif isinstance(arg_new, list):
                        # arg_val is single item, arg_new is list
                        res_args[arg_argv[0]] = [arg_val] + arg_new
                    else:
                        # Both are single items
                        res_args[arg_argv[0]] = [arg_val, arg_new]
                else:
                    res_args[arg_argv[0]] = arg_argv[1]

        if batch_argv:
            res_args_batch = []
            for item in batch_argv:
                temp_item = item.copy()
                temp_item.update(res_args)
                res_args_batch.append(temp_item)
            res_args = res_args_batch

        return res_args


class Argument:
    def __init__(self, argument: Dict[str, Any]):
        self.argument = argument
        self.type = "argv_arg"
        self.value = argument["pipeline_arg"]
        self.key = argument["prefix"]
        try:
            self.action = argument["action"]
        except KeyError:
            self.action = "store"
        try:
            self.nargs = argument["nargs"]
        except KeyError:
            self.nargs = None

    def to_argv(
        self, args_dict: Optional[Dict[str, Any]] = None
    ) -> List[Union[str, Any]]:
        if args_dict is None:
            return [self.key, self.value]

        # Check if value is a variable reference like %(variable)s
        arg_key = get_arg_from_string(self.value)

        # If arg_key["arg"] is None, it's a literal value, not a variable
        if arg_key["arg"] is None:
            value = self.value
        else:
            # It's a variable reference, look it up in args_dict
            value = args_dict[arg_key["arg"]]

        if self.action == "store_false":
            value = not value
        return [self.key, value]


class CompositeArgument(Argument):
    """Handle composite arguments built from multiple sources.

    Retrieves results from a snippet's results method and processes them into
    arguments. Does not appear in argument help messages.

    Attributes:
        arguments: PipelineItemArguments instance containing child arguments
        type: Always 'composite_arg'
        value: None (not displayed in help)
    """

    def __init__(self, argument: Dict[str, Any]):
        super().__init__(argument)
        self.arguments = PipelineItemArguments()
        for argument_i in self.argument["pipeline_arg"]["result_arguments"]:
            try:
                arg_type = argument_i["type"]
            except KeyError:
                arg_type = "argv_arg"
            arg_main = {key: argument_i[key] for key in ["prefix", "pipeline_arg"]}
            self.arguments.add_argument(arg_main, arg_type)
        self.type = "composite_arg"
        self.value = None

    def to_argv(
        self, args_dict: Optional[Dict[str, Any]] = None
    ) -> List[Union[str, Any]]:
        snippet = self.argument["pipeline_arg"]["snippet_name"]
        res_key = self.argument["pipeline_arg"]["result_key"]
        if args_dict is None:
            value = self.value
        else:
            res_args = self.arguments.to_dict(args_dict)
            if isinstance(res_args, dict):
                res_args = [res_args]
            value = []
            for res_arg in res_args:
                snippet_module = copy(PYPE_SNIPPETS_MODULES[snippet])
                value.append(snippet_module.results(res_arg)[res_key])
        return [self.key, value]


class BatchFileArgument(Argument):
    """Process arguments from a batch input file.

    Reads arguments from a tab-separated file and converts them into
    a list of argument dictionaries for batch processing. Required for
    batch snippet/pipeline execution.

    The input file must have:
    - Tab-separated columns
    - Header row with argument names
    - One set of arguments per line
    """

    def __init__(self, argument: Dict[str, Any]):
        super().__init__(argument)
        self.type = "batch_arg"

    def to_argv(
        self, args_dict: Optional[Dict[str, Any]] = None
    ) -> Optional[List[Dict[str, str]]]:
        if args_dict is None:
            batch_values = None
        else:
            batch_file = self.value % args_dict
            batch_values = []
            with xopen(batch_file, "rt") as input_list:
                argument_keys = next(input_list).strip().split("\t")
                for line in input_list:
                    line_args = {}
                    line = line.strip().split("\t")
                    for index in range(len(argument_keys)):
                        line_args[argument_keys[index]] = line[index]
                    batch_values.append(line_args)
        return batch_values


class BatchListArgument(Argument):
    """
    BatchArgument read the arguments from a file and return the list of
    arguments.
    It is required for the execution of a batch snippet or batch pipeline.
    """

    def __init__(self, argument: Dict[str, Any]):
        super().__init__(argument)
        self.type = "batch_arg"
        self.value = "batch_list"

    def to_argv(
        self, args_dict: Optional[Dict[str, Any]] = None
    ) -> Optional[List[Dict[str, str]]]:
        if args_dict is None:
            batch_values = None
        else:
            batch_values = self.argument["pipeline_arg"]
        return batch_values


class ConstantArgument(Argument):
    """
    Represents a constant argument with a fixed key-value pair.

    This argument type holds a constant key and value that will always be
    included in command-line arguments, regardless of runtime inputs.
    """

    def __init__(self, argument: Dict[str, Any]):
        super().__init__(argument)
        self.type = "str_arg"
        self.action = "store"
        self.nargs = None

    def to_argv(
        self, args_dict: Optional[Dict[str, Any]] = None
    ) -> List[Union[str, Any]]:
        return [self.key, self.value]
