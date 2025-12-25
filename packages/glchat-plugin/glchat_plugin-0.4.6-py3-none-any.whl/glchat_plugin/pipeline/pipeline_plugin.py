"""Base Pipeline Builder Plugin.

This module defines the base class for pipeline builder plugins.

Authors:
    Samuel Lusandi (samuel.lusandi@gdplabs.id)
    Hermes Vincentius Gani (hermes.v.gani@gdplabs.id)
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, Type, TypeVar

from bosa_core.plugin.plugin import Plugin
from gllm_core.schema import Tool
from gllm_inference.catalog.catalog import BaseCatalog
from gllm_pipeline.pipeline.pipeline import Pipeline

from glchat_plugin.config.constant import DEFAULT_ORGANIZATION_ID
from glchat_plugin.pipeline.pipeline_handler import PipelineHandler
from glchat_plugin.pipeline.tool_processor import ToolProcessor

PipelineState = TypeVar("PipelineState")
PipelinePresetConfig = TypeVar("PipelinePresetConfig", bound="BasePipelinePresetConfig")
PipelineRuntimeConfig = TypeVar("PipelineRuntimeConfig", bound="BaseModel")


@Plugin.for_handler(PipelineHandler)
class PipelineBuilderPlugin(Plugin, Generic[PipelineState, PipelinePresetConfig], ABC):
    """Base class for pipeline builder plugins.

    This class combines the Plugin architecture with the Pipeline Builder functionality.

    Attributes:
        name (str): The name of the plugin.
        description (str): The description of the plugin.
        version (str): The version of the plugin.
        organization_id (str): The organization ID.
        lmrp_catalogs (dict[str, BaseCatalog[Any]] | None): The LM request processor catalogs.
        prompt_builder_catalogs (dict[str, BaseCatalog[Any]] | None): The prompt builder catalogs.
        additional_config_class (Type[PipelineRuntimeConfig] | None): The additional runtime configuration class.
        preset_config_class (Type[PipelinePresetConfig] | None): The preset configuration class.
    """

    name: str
    description: str = "Pipeline builder plugin"
    version: str = "0.0.0"
    organization_id: str = DEFAULT_ORGANIZATION_ID

    lmrp_catalogs: dict[str, BaseCatalog[Any]] | None = None
    prompt_builder_catalogs: dict[str, BaseCatalog[Any]] | None = None

    additional_config_class: Type[PipelineRuntimeConfig] | None = None
    preset_config_class: Type[PipelinePresetConfig] | None = None

    @classmethod
    def get_preset_config_class(cls) -> Type[PipelinePresetConfig]:
        """Get the preset_config_class.

        Returns:
            Type[PipelinePresetConfig]: The pipeline preset config class.

        Raises:
            NotImplementedError: If the preset_config_class is not defined.
        """
        if cls.preset_config_class is None:
            raise NotImplementedError(f"{cls.__name__} must define a `preset_config_class` attribute.")
        return cls.preset_config_class

    @abstractmethod
    def build_initial_state(
        self,
        request_config: dict[str, Any],
        pipeline_config: dict[str, Any],
        previous_state: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> PipelineState:
        """Build the initial pipeline state.

        Args:
            request_config (dict[str, Any]): Request configuration.
            pipeline_config (dict[str, Any]): Pipeline configuration.
            previous_state (dict[str, Any] | None): Previous state.
            kwargs (Any): Additional state arguments.

        Returns:
            PipelineState: Initial pipeline state.
        """
        pass

    @abstractmethod
    async def build(
        self,
        pipeline_config: dict[str, Any],
    ) -> Pipeline:
        """Build a pipeline instance.

        Args:
            pipeline_config (dict[str, Any]): Pipeline configuration including model name and other settings.

        Returns:
            Pipeline: Built pipeline instance.
        """
        pass

    async def cleanup(self):
        """Cleanup the pipeline resources, if needed."""
        pass

    def build_additional_runtime_config(
        self,
        pipeline_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Build additional runtime configuration.

        Args:
            pipeline_config (dict[str, Any]): Pipeline configuration.

        Returns:
            dict[str, Any]: Additional runtime configuration.
        """
        if not self.additional_config_class:
            return {}

        config = self.additional_config_class(**pipeline_config)
        return config.model_dump(exclude_none=True)

    def get_config(self) -> dict[str, Any]:
        """Get the pipeline configuration.

        Returns:
            dict[str, Any]: Pipeline configuration.
        """
        if self.preset_config_class:
            return self.preset_config_class().model_dump()
        return {}

    async def build_tools(
        self,
        pipeline_config: dict[str, Any],
        prompt_builder_catalogs: dict[str, BaseCatalog[Any]] | None = None,
        lmrp_catalogs: dict[str, BaseCatalog[Any]] | None = None,
    ) -> list[ToolProcessor]:
        """Build a pipeline instance.

        Args:
            pipeline_config (dict[str, Any]): Pipeline configuration including model name and other settings.

        Returns:
            list[ToolProcessor]: Built tool processors.
        """
        return []
