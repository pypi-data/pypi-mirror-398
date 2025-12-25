from typing import Any, Optional

from hot_tool import FunctionDefinition, HotTool


class AielloToolx(HotTool):
    def name(self) -> str:
        raise NotImplementedError

    def description(self, context: Optional[str] = None) -> str:
        raise NotImplementedError

    def parameters(self, context: Optional[str] = None) -> dict[str, Any]:
        raise NotImplementedError

    def function_definition(self, context: Optional[str] = None) -> FunctionDefinition:
        parameters = self.parameters(context)
        parameters["strict"] = True
        parameters["required"] = True
        return FunctionDefinition(
            name=self.name(),
            description=self.description(context),
            parameters=parameters,
        )

    def run(
        self, arguments: Optional[str] = None, context: Optional[str] = None
    ) -> str:
        raise NotImplementedError
