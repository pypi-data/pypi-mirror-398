"""Tool processor.

This module provides a base class for tool processors.

Authors:
    Surya Mahadi (surya.mahadi@gdplabs.id)

References:
    None
"""

from abc import ABC, abstractmethod
from typing import Any

from gllm_core.schema import Tool


class ToolProcessor(ABC):
    """Tool processor.

    This class is responsible for processing tools.

    Attributes:
        tool (Tool): The tool.
    """

    def __init__(self, tool: Tool):
        """Initialize the tool processor.

        Args:
            tool (Tool): The tool.
        """
        self.tool = tool

    @property
    def name(self) -> str:
        """Get the name of the tool.

        Returns:
            str: The name of the tool.
        """
        return self.tool.name

    @abstractmethod
    async def preprocess(
        self,
        pipeline_config: dict[str, Any],
        inputs: dict[str, Any],
        config: dict[str, Any],
        **kwargs: Any,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Process a tool.

        Args:
            pipeline_config (dict[str, Any]): The pipeline configuration.
            inputs (dict[str, Any]): The inputs to the tool.
            config (dict[str, Any]): The configuration of the tool.
            kwargs (Any): The keyword arguments to pass to the tool.

        Returns:
            tuple[dict[str, Any], dict[str, Any]]: The inputs and configuration for the tool invocation.
        """
        raise NotImplementedError

    @abstractmethod
    async def postprocess(self, result: Any) -> dict[str, Any]:
        """Postprocess a tool for json friendly output.

        Args:
            result (Any): The result of the tool invocation.

        Returns:
            dict[str, Any]: The result of the tool invocation.
        """
        raise NotImplementedError

    async def process(
        self,
        pipeline_config: dict[str, Any],
        inputs: dict[str, Any],
        config: dict[str, Any],
        **kwargs: Any,
    ) -> Any:
        """Process a tool.

        Args:
            pipeline_config (dict[str, Any]): The pipeline configuration.
            inputs (dict[str, Any]): The inputs to the tool.
            config (dict[str, Any]): The configuration of the tool.
            kwargs (Any): The keyword arguments to pass to the tool.

        Returns:
            Any: The result of the tool invocation.
        """
        tool_input, config = await self.preprocess(
            pipeline_config=pipeline_config,
            inputs=inputs,
            config=config,
            **kwargs,
        )
        result = await self.tool.invoke(
            input=tool_input,
            context=config,
        )
        return await self.postprocess(result)
