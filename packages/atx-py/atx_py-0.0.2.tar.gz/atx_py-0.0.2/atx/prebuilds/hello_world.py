"""
atx build --tool-name hello_world --tool-version 1 atx/prebuilds/hello_world.py

./dist/hello_world/1/tool
"""

from typing import Any, Optional

from atx import AielloToolx

TOOL_NAME: str = "hello_world"
TOOL_DESCRIPTION: str = "Print 'Hello, World!'"


class HelloWorld(AielloToolx):
    def name(self) -> str:
        return TOOL_NAME

    def description(self, context: Optional[str] = None) -> str:
        return TOOL_DESCRIPTION

    def parameters(self, context: Optional[str] = None) -> dict[str, Any]:
        return {}

    def run(
        self, arguments: Optional[str] = None, context: Optional[str] = None
    ) -> str:
        return "Hello, World!"
