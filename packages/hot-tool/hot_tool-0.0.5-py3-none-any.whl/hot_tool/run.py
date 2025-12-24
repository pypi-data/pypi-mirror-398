# hot_tool/run.py
import argparse
import json
import logging
import sys
from typing import Optional, Type, Union

from hot_tool import (
    HotMultipleToolImplementationsFoundError,
    HotTool,
    HotToolImplementationNotFoundError,
)

logger = logging.getLogger(__name__)


def get_all_descendants(base_class: Type) -> list[Type]:
    """
    Recursively get all descendant classes of a base class.
    Returns a flat list of all subclasses at any depth.
    """
    result: list[Type] = []
    for child in base_class.__subclasses__():
        result.append(child)
        # Recursively get descendants of this child
        result.extend(get_all_descendants(child))
    return result


def is_method_implemented(
    cls: Type, method_name: str, base_class: Type[HotTool]
) -> bool:
    """
    Check if a method is implemented (not inherited directly from base_class).
    Returns True if the method is defined in any class except base_class.
    """
    # Traverse MRO to find the first class that defines this method
    for base in cls.__mro__:
        if method_name in base.__dict__:
            # Found the definer, check if it's not the base class
            return base is not base_class
    return False


def get_concrete_tool_classes(
    base_class: Type[HotTool], module_name: Optional[str] = None
) -> list[Type[HotTool]]:
    """
    Get concrete tool classes that implement both run() and function_definition().
    Optionally filter by module name to get only script-defined classes.
    """
    all_descendants = get_all_descendants(base_class)
    concrete_classes: list[Type[HotTool]] = []

    for cls in all_descendants:
        # Check if this class has both required methods implemented
        has_run = is_method_implemented(cls, "run", base_class)
        has_function_def = is_method_implemented(cls, "function_definition", base_class)

        if has_run and has_function_def:
            # If module_name is specified, only include classes from that module
            if module_name is None or cls.__module__ == module_name:
                concrete_classes.append(cls)

    return concrete_classes


def run_tool(
    tool: Union[Type[HotTool], HotTool],
    arguments: Optional[str] = None,
    context: Optional[str] = None,
) -> str:
    if isinstance(tool, Type) and issubclass(tool, HotTool):
        tool = tool()
    elif isinstance(tool, HotTool):
        tool = tool
    else:
        raise ValueError(f"Invalid tool type: {type(tool)}")

    return tool.run(arguments=arguments, context=context)


def run_as_executable():
    # Only get tools defined in the current script (__main__)
    concrete_tools = get_concrete_tool_classes(HotTool, module_name="__main__")

    if len(concrete_tools) == 0:
        # Check if there are any HotTool subclasses at all in the script
        all_script_descendants = [
            cls for cls in get_all_descendants(HotTool) if cls.__module__ == "__main__"
        ]

        if len(all_script_descendants) == 0:
            raise HotToolImplementationNotFoundError(
                "No tool class found in this script. "
                "Please define a class that inherits from HotTool "
                "and implements both run() and function_definition() methods."
            )
        else:
            # Found classes but they don't implement required methods
            class_names = [cls.__name__ for cls in all_script_descendants]

            # Check which methods are missing for better error message
            missing_methods: list[str] = []
            sample_class = all_script_descendants[0]
            if "run" not in sample_class.__dict__:
                missing_methods.append("run()")
            if "function_definition" not in sample_class.__dict__:
                missing_methods.append("function_definition()")

            missing_methods_str = " and ".join(missing_methods)
            error_msg = (
                f"Found tool class(es) {class_names} but missing "
                f"required method(s): {missing_methods_str}. "
                "Both run() and function_definition() must be implemented. "
                "See examples/ directory for reference."
            )
            raise HotToolImplementationNotFoundError(error_msg)
    elif len(concrete_tools) > 1:
        tool_names = [cls.__name__ for cls in concrete_tools]
        raise HotMultipleToolImplementationsFoundError(
            f"Multiple tool implementations found in script: {tool_names}. "
            "Only one concrete tool class is allowed per script."
        )

    tool_class = concrete_tools[0]

    parser = argparse.ArgumentParser(description="")

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(
        dest="subcommand",
        help="Available commands",
    )

    # function-definition subcommand
    function_def_parser = subparsers.add_parser(
        "function-definition",
        help="Print the function definition in JSON format",
    )
    function_def_parser.add_argument(
        "--context",
        type=str,
        default=None,
        help="Context for the tool. default is None.",
    )

    # Run subcommand (for explicit run, though we support implicit run too)
    run_parser = subparsers.add_parser(
        "run",
        help="Run the tool (default behavior)",
    )
    run_parser.add_argument(
        "--arguments",
        type=str,
        default=None,
        help="Arguments for the tool. default is None.",
    )
    run_parser.add_argument(
        "--context",
        type=str,
        default=None,
        help="Context for the tool. default is None.",
    )

    # Add arguments to main parser for backward compatibility (no subcommand)
    parser.add_argument(
        "--arguments",
        type=str,
        default=None,
        help="Arguments for the tool. default is None.",
    )
    parser.add_argument(
        "--context",
        type=str,
        default=None,
        help="Context for the tool. default is None.",
    )

    args = parser.parse_args()

    # Handle function-definition subcommand
    if args.subcommand == "function-definition":
        try:
            tool_instance = tool_class()
            function_def = tool_instance.function_definition(context=args.context)
            print(json.dumps(function_def))
            sys.exit(0)
        except NotImplementedError:
            logger.error("function_definition() method not implemented")
            sys.exit(1)
        except Exception as e:
            logger.exception(e)
            logger.error(f"Error getting function definition: {e}")
            sys.exit(1)

    # Handle run subcommand or default behavior (no subcommand)
    else:
        try:
            result = run_tool(
                tool_class, arguments=args.arguments, context=args.context
            )
            logger.info(f"Tool result: {str(result)[:100]}")
            print(result)  # print to stdout for LLM to read

        except Exception as e:
            logger.exception(e)
            logger.error(f"Error running tool: {e}")
            sys.exit(1)

    return None
