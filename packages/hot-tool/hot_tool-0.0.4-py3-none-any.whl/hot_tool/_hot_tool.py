from typing import Dict, Optional, Required, TypeAlias, TypedDict

FunctionParameters: TypeAlias = Dict[str, object]


class FunctionDefinition(TypedDict, total=False):
    """Reference: `openai.types.shared_params.function_definition.FunctionDefinition`"""

    name: Required[str]
    description: str
    parameters: FunctionParameters
    strict: Optional[bool]


class HotTool:
    def function_definition(self, context: Optional[str] = None) -> FunctionDefinition:
        raise NotImplementedError("Subclasses must implement this method")

    def run(
        self, arguments: Optional[str] = None, context: Optional[str] = None
    ) -> str:
        raise NotImplementedError("Subclasses must implement this method")
