"""Pipeline handler for pipeline builder plugins.

This handler manages pipeline builder plugins and provides necessary services.

Authors:
    Samuel Lusandi (samuel.lusandi@gdplabs.id)
    Hermes Vincentius Gani (hermes.v.gani@gdplabs.id)
"""

import inspect
import traceback
from typing import Any, Type

from bosa_core import Plugin
from bosa_core.plugin.handler import PluginHandler
from gllm_core.schema import Tool
from gllm_core.utils import LoggerManager
from gllm_inference.catalog import LMRequestProcessorCatalog, PromptBuilderCatalog
from gllm_pipeline.pipeline.pipeline import Pipeline
from pydantic import BaseModel, ConfigDict

from glchat_plugin.config.app_config import AppConfig
from glchat_plugin.config.constant import DEFAULT_ORGANIZATION_ID
from glchat_plugin.pipeline.tool_processor import ToolProcessor
from glchat_plugin.storage.base_chat_history_storage import BaseChatHistoryStorage


class ChatbotConfig(BaseModel):
    """Chatbot configuration class containing pipeline configs and metadata.

    Attributes:
        pipeline_type (str): Type of pipeline to use.
        pipeline_config (dict[str, Any]): Pipeline configuration dictionary.
        prompt_builder_catalogs (dict[str, PromptBuilderCatalog] | None): Mapping of prompt builder catalogs.
        lmrp_catalogs (dict[str, LMRequestProcessorCatalog] | None): Mapping of LM request processor catalogs.
    """

    pipeline_type: str
    pipeline_config: dict[str, Any]
    prompt_builder_catalogs: dict[str, PromptBuilderCatalog] | None
    lmrp_catalogs: dict[str, LMRequestProcessorCatalog] | None
    model_config = ConfigDict(arbitrary_types_allowed=True)


class PipelinePresetConfig(BaseModel):
    """Pipeline preset configuration class.

    Attributes:
        preset_id (str): Unique identifier for the pipeline preset.
        supported_models (list[dict[str, Any]]): List of models (including config) supported by this preset.
    """

    preset_id: str
    supported_models: list[dict[str, Any]]


class ChatbotPresetMapping(BaseModel):
    """Chatbot preset mapping.

    Attributes:
        pipeline_type (str): Type of pipeline.
        chatbot_preset_map (dict[str, PipelinePresetConfig]):
            Mapping of chatbot IDs to their pipeline preset configurations.
    """

    pipeline_type: str
    chatbot_preset_map: dict[str, PipelinePresetConfig]


class PipelineBundle:
    """Pipeline bundle.

    Attributes:
        pipeline (Pipeline): The pipeline.
        tools (list[ToolProcessor]): The tools.
    """

    pipeline: Pipeline
    tools: dict[str, ToolProcessor]

    def __init__(self, pipeline: Pipeline, tools: list[ToolProcessor]):
        """Initialize the pipeline bundle.

        Args:
            pipeline (Pipeline): The pipeline.
            tools (list[ToolProcessor]): The tools.
        """
        self.pipeline = pipeline
        self.tools = {tool.name: tool for tool in tools}

    async def invoke(self, **kwargs: Any) -> dict[str, Any]:
        """Invoke the pipeline bundle.

        Args:
            kwargs (Any): The keyword arguments to pass to the pipeline.

        Returns:
            dict[str, Any]: The result of the pipeline invocation.
        """
        return await self.pipeline.invoke(**kwargs)

    async def invoke_as_tool(
        self,
        tool_name: str,
        pipeline_config: dict[str, Any],
        inputs: dict[str, Any],
        config: dict[str, Any],
        **kwargs: Any,
    ) -> Any:
        """Invoke the pipeline bundle as a tool.

        Args:
            tool_name (str): The name of the tool.
            pipeline_config (dict[str, Any]): The pipeline configuration.
            inputs (dict[str, Any]): The inputs to the tool.
            config (dict[str, Any]): The configuration of the tool.
            kwargs (Any): The keyword arguments to pass to the tool.

        Returns:
            Any: The result of the tool invocation.

        Raises:
            ValueError: If the tool is not found in the pipeline bundle.
        """
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool `{tool_name}` not found in pipeline bundle")

        return await tool.process(
            pipeline_config=pipeline_config,
            inputs=inputs,
            config=config,
            **kwargs,
        )


logger = LoggerManager().get_logger(__name__)


INTERNAL_PIPELINES = ["preprocessing", "postprocessing"]


class PipelineHandler(PluginHandler):
    """Handler for pipeline builder plugins.

    This handler manages pipeline builder plugins and provides caching for built pipelines.

    Attributes:
        app_config (dict[str, AppConfig]): Application configuration.
        _activated_configs (dict[tuple[str, str], ChatbotPresetMapping]):
            Collection of chatbot preset mapping by pipeline types.
        _chatbot_configs (dict[tuple[str, str], ChatbotConfig]):
            Mapping of chatbot IDs to their configurations.
        _builders (dict[tuple[str, str], Plugin]):
            Mapping of chatbot IDs to their pipeline builder plugins.
        _plugins (dict[tuple[str, str], Plugin]):
            Mapping of pipeline types to their plugins.
        _pipeline_cache (dict[tuple[str, str, str], Pipeline]):
            Cache mapping (chatbot_id, model_id, organization_id) to Pipeline instances.
        _chatbot_pipeline_keys (dict[tuple[str, str], set[tuple[str, str, str]]]):
            Mapping of chatbot IDs to their pipeline keys.
        _pipeline_build_errors (dict[tuple[str, str, str], str]):
            Cache mapping (chatbot_id, model_id, organization_id) to error messages from failed pipeline builds.
    """

    app_config: dict[str, AppConfig] = {}
    _activated_configs: dict[tuple[str, str], ChatbotPresetMapping] = {}
    _chatbot_configs: dict[tuple[str, str], ChatbotConfig] = {}
    _builders: dict[tuple[str, str], Plugin] = {}
    _plugins: dict[tuple[str, str], Plugin] = {}
    _pipeline_cache: dict[tuple[str, str, str], PipelineBundle] = {}
    _chatbot_pipeline_keys: dict[tuple[str, str], set[tuple[str, str, str]]] = {}
    _pipeline_build_errors: dict[tuple[str, str, str], str] = {}

    def __init__(self, app_config: dict[str, AppConfig], chat_history_storage: BaseChatHistoryStorage):
        """Initialize the pipeline handler.

        Args:
            app_config (dict[str, AppConfig]): Application configuration.
            chat_history_storage (BaseChatHistoryStorage): Chat history storage.
        """
        self.app_config = app_config
        self.chat_history_storage = chat_history_storage
        self._prepare_pipelines()

    @classmethod
    def create_injections(cls, instance: "PipelineHandler") -> dict[Type[Any], Any]:
        """Create injection mappings for pipeline builder plugins.

        Args:
            instance (PipelineHandler): The handler instance providing injections.

        Returns:
            dict[Type[Any], Any]: Dictionary mapping service types to their instances.
        """
        return {
            BaseChatHistoryStorage: instance.chat_history_storage,
        }

    @classmethod
    def initialize_plugin(cls, instance: "PipelineHandler", plugin: Plugin) -> None:
        """Initialize plugin-specific resources.

        This method is called after plugin creation and service injection.
        For each pipeline builder plugin, we build pipelines for all supported models and cache them.

        Args:
            instance (PipelineHandler): The handler instance.
            plugin (Plugin): The pipeline builder plugin instance.
        """
        pass

    @classmethod
    async def ainitialize_plugin(cls, instance: "PipelineHandler", plugin: Plugin) -> None:
        """Initialize plugin-specific resources.

        This method is called after plugin creation and service injection.
        For each pipeline builder plugin, we build pipelines for all supported models and cache them.

        Args:
            instance (PipelineHandler): The handler instance.
            plugin (Plugin): The pipeline builder plugin instance.
        """
        pipeline_type = plugin.name
        organization_id = plugin.organization_id
        pipeline_type_organization_id = (pipeline_type, organization_id)
        instance._plugins[pipeline_type_organization_id] = plugin

        if pipeline_type_organization_id not in instance._activated_configs:
            return

        active_config = instance._activated_configs[pipeline_type_organization_id]
        for chatbot_id, preset in active_config.chatbot_preset_map.items():
            try:
                chatbot_organization_id = (chatbot_id, organization_id)
                if pipeline_type != instance._chatbot_configs[chatbot_organization_id].pipeline_type:
                    continue

                await cls._build_plugin(instance, chatbot_id, preset.supported_models, plugin, organization_id)
            except Exception as e:
                logger.warning(f"Failed when ainit pliugin {traceback.format_exc()}")
                logger.warning(f"Error initializing plugin for chatbot `{chatbot_id}`: {e}")

    @classmethod
    async def acleanup_plugins(cls, instance: "PipelineHandler") -> None:
        """Cleanup all plugins.

        Args:
            instance (PipelineHandler): The handler instance.
        """
        for plugin in instance._plugins.values():
            try:
                await plugin.cleanup()
            except Exception as e:
                logger.warning(f"Error cleaning up plugin `{plugin.name}`: {e}")

    @classmethod
    async def _build_plugin(
        cls,
        instance: "PipelineHandler",
        chatbot_id: str,
        supported_models: list[dict[str, Any]],
        plugin: Plugin,
        organization_id: str = DEFAULT_ORGANIZATION_ID,
    ) -> None:
        """Build a plugin for the given chatbot.

        Args:
            instance (PipelineHandler): The handler instance.
            chatbot_id (str): The chatbot ID.
            supported_models (list[dict[str, Any]]): List of models (including config).
            plugin (Plugin): The pipeline builder plugin instance.
            organization_id (str): The organization ID.
        """
        chatbot_organization_id = (chatbot_id, organization_id)

        prompt_builder_catalogs = instance._chatbot_configs[chatbot_organization_id].prompt_builder_catalogs
        plugin.prompt_builder_catalogs = prompt_builder_catalogs

        lmrp_catalogs = instance._chatbot_configs[chatbot_organization_id].lmrp_catalogs
        plugin.lmrp_catalogs = lmrp_catalogs

        instance._builders[chatbot_organization_id] = plugin

        for pipeline_type in INTERNAL_PIPELINES:
            pipeline_type_organization_id = (pipeline_type, organization_id)
            internal_plugin = instance._plugins.get(pipeline_type_organization_id)
            if internal_plugin:
                try:
                    internal_plugin.prompt_builder_catalogs = prompt_builder_catalogs
                    internal_plugin.lmrp_catalogs = lmrp_catalogs
                    pipeline_config = instance._chatbot_configs[chatbot_organization_id].pipeline_config.copy()
                    pipeline = await cls._call_build(
                        internal_plugin,
                        pipeline_config,
                        prompt_builder_catalogs,
                        lmrp_catalogs,
                    )
                    pipeline_tools = await internal_plugin.build_tools(pipeline_config, prompt_builder_catalogs, lmrp_catalogs)
                    pipeline_key = (chatbot_id, f"__{pipeline_type}__", organization_id)
                    instance._chatbot_pipeline_keys.setdefault(chatbot_organization_id, set()).add(pipeline_key)
                    instance._pipeline_cache[pipeline_key] = PipelineBundle(pipeline, pipeline_tools)

                    # Clear any previous error for this internal pipeline if build succeeded
                    instance._pipeline_build_errors.pop(pipeline_key, None)
                except Exception as e:
                    error_message = (
                        f"Error building internal pipeline `{pipeline_type}` for chatbot `{chatbot_id}`: {e}"
                    )
                    logger.warning(f"Failed when ainit plugin {traceback.format_exc()}")
                    logger.warning(error_message)

                    # Store the error message for later retrieval
                    instance._store_pipeline_build_error(
                        chatbot_id, f"__{pipeline_type}__", organization_id, error_message
                    )

        for model in supported_models:
            try:
                model_id = model.get("model_id", model.get("name"))
                if not model_id:
                    continue

                pipeline_config = instance._chatbot_configs[chatbot_organization_id].pipeline_config.copy()
                # use original model name
                pipeline_config["model_name"] = model.get("name", model_id)
                pipeline_config["model_kwargs"] = model.get("model_kwargs", {})
                pipeline_config["model_env_kwargs"] = model.get("model_env_kwargs", {})
                credentials = pipeline_config["model_env_kwargs"].get("credentials")
                if credentials:
                    pipeline_config["api_key"] = credentials

                pipeline = await cls._call_build(
                    plugin,
                    pipeline_config,
                    prompt_builder_catalogs,
                    lmrp_catalogs,
                )
                pipeline_tools = await plugin.build_tools(pipeline_config, prompt_builder_catalogs, lmrp_catalogs)
                pipeline_key = (chatbot_id, str(model_id), organization_id)
                instance._chatbot_pipeline_keys.setdefault(chatbot_organization_id, set()).add(pipeline_key)
                instance._pipeline_cache[pipeline_key] = PipelineBundle(pipeline, pipeline_tools)

                # Clear any previous error for this pipeline if build succeeded
                instance._pipeline_build_errors.pop(pipeline_key, None)
            except Exception as e:
                error_message = f"Error building pipeline for chatbot `{chatbot_id}` model `{model_id}`: {e}"
                logger.warning(f"Failed when ainit plugin {traceback.format_exc()}")
                logger.warning(error_message)

                # Store the error message for later retrieval
                instance._store_pipeline_build_error(chatbot_id, str(model_id), organization_id, error_message)

    @classmethod
    async def _call_build(
        cls,
        plugin: Plugin,
        pipeline_config: dict[str, Any],
        prompt_builder_catalogs: dict[str, PromptBuilderCatalog] | None,
        lmrp_catalogs: dict[str, LMRequestProcessorCatalog] | None,
    ) -> Pipeline:
        """Call plugin.build in a backward-compatible way.

        If the plugin.build signature declares prompt_builder_catalogs or lmrp_catalogs,
        they will be passed as keyword arguments. Otherwise, only pipeline_config is passed.
        """
        try:
            sig = inspect.signature(plugin.build)
        except (TypeError, ValueError):
            # Fallback: call with just pipeline_config
            return await plugin.build(pipeline_config)

        params = list(sig.parameters.values())
        # Skip 'self' if present
        if params and params[0].name == "self":
            params = params[1:]

        param_names = {p.name for p in params}

        if "prompt_builder_catalogs" in param_names or "lmrp_catalogs" in param_names:
            return await plugin.build(
                pipeline_config,
                prompt_builder_catalogs=prompt_builder_catalogs,
                lmrp_catalogs=lmrp_catalogs,
            )

        return await plugin.build(pipeline_config)

    def get_pipeline_builder(self, chatbot_id: str, organization_id: str = DEFAULT_ORGANIZATION_ID) -> Plugin:
        """Get a pipeline builder instance for the given chatbot.

        Args:
            chatbot_id (str): The chatbot ID.
            organization_id (str): The organization ID.

        Returns:
            Plugin: The pipeline builder instance.

        Raises:
            ValueError: If the chatbot ID is invalid or the model name is not supported.
        """
        chatbot_organization_id = (chatbot_id, organization_id)
        if chatbot_organization_id not in self._builders:
            logger.warning(
                f"Pipeline builder not found for chatbot `{chatbot_organization_id}`, attempting to rebuild..."
            )
            # Try to rebuild the plugin if it's not found
            self._try_rebuild_plugin(chatbot_id, organization_id)

        if chatbot_organization_id not in self._builders:
            raise ValueError(
                f"Pipeline builder for chatbot `{chatbot_organization_id}` not found and could not be rebuilt"
            )

        return self._builders[chatbot_organization_id]

    def _try_rebuild_plugin(self, chatbot_id: str, organization_id: str = DEFAULT_ORGANIZATION_ID) -> None:
        """Try to rebuild a plugin for the given chatbot.

        Args:
            chatbot_id (str): The chatbot ID.
            organization_id (str): The organization ID.
        """
        chatbot_organization_id = (chatbot_id, organization_id)
        try:
            # Check if we have the chatbot configuration
            if chatbot_organization_id not in self._chatbot_configs:
                logger.warning(f"Chatbot configuration not found for `{chatbot_organization_id}`")
                return

            chatbot_config = self._chatbot_configs[chatbot_organization_id]
            pipeline_type = chatbot_config.pipeline_type
            pipeline_organization_id = (pipeline_type, organization_id)

            # Check if we have the plugin for this pipeline type
            if pipeline_organization_id not in self._plugins:
                logger.warning(f"Plugin not found for pipeline type `{pipeline_organization_id}`")
                return

            plugin = self._plugins[pipeline_organization_id]

            # Get supported models from the configuration
            supported_models = list(chatbot_config.pipeline_config.get("supported_models", {}).values())

            if not supported_models:
                logger.warning(f"No supported models found for chatbot `{chatbot_id}`")
                return

            # Rebuild the plugin synchronously (this is a simplified version)
            # Set the catalogs
            plugin.prompt_builder_catalogs = chatbot_config.prompt_builder_catalogs
            plugin.lmrp_catalogs = chatbot_config.lmrp_catalogs
            self._builders[chatbot_organization_id] = plugin

            logger.info(f"Successfully rebuilt pipeline builder for chatbot `{chatbot_organization_id}`")

        except Exception as e:
            logger.warning(f"Error rebuilding plugin for chatbot `{chatbot_organization_id}`: {e}")

    async def _async_rebuild_pipeline(
        self, chatbot_id: str, model_id: str, organization_id: str = DEFAULT_ORGANIZATION_ID
    ) -> None:
        """Asynchronously rebuild a pipeline for the given chatbot and model.

        Args:
            chatbot_id (str): The chatbot ID.
            model_id (str): The model ID.
            organization_id (str): The organization ID.
        """
        chatbot_organization_id = (chatbot_id, organization_id)
        try:
            # First, ensure we have the pipeline builder
            if chatbot_organization_id not in self._builders:
                await self._async_rebuild_plugin(chatbot_id, organization_id)

            if chatbot_organization_id not in self._builders:
                logger.warning(f"Could not rebuild pipeline builder for chatbot `{chatbot_organization_id}`")
                return

            # Check if we have the chatbot configuration
            if chatbot_organization_id not in self._chatbot_configs:
                logger.warning(f"Chatbot configuration not found for `{chatbot_organization_id}`")
                return

            chatbot_config = self._chatbot_configs[chatbot_organization_id]
            plugin = self._builders[chatbot_organization_id]

            # Find the model configuration
            supported_models = list(chatbot_config.pipeline_config.get("supported_models", {}).values())
            model_config = None

            for model in supported_models:
                if model.get("model_id", model.get("name")) == model_id:
                    model_config = model
                    break
            if not model_config:
                logger.warning(
                    f"Model `{model_id}` not found in supported models "
                    f"for chatbot `{chatbot_id}` async rebuild pipeline"
                )
                return

            # Use the existing _build_plugin method to rebuild the pipeline
            await __class__._build_plugin(self, chatbot_id, [model_config], plugin, organization_id)

            logger.info(f"Successfully rebuilt pipeline for chatbot `{chatbot_organization_id}` model `{model_id}`")

        except Exception as e:
            error_message = f"Error rebuilding pipeline for chatbot `{chatbot_organization_id}` model `{model_id}`: {e}"
            logger.warning(error_message)

            # Store the error message for later retrieval
            self._store_pipeline_build_error(chatbot_id, model_id, organization_id, error_message)

    async def aget_pipeline(
        self, chatbot_id: str, model_id: str, organization_id: str = DEFAULT_ORGANIZATION_ID
    ) -> PipelineBundle:
        """Get a pipeline instance for the given chatbot and model ID (async version).

        Args:
            chatbot_id (str): The chatbot ID.
            model_id (str): The model ID to use for inference.
            organization_id (str): The organization ID.

        Returns:
            PipelineBundle: The pipeline bundle instance.

        Raises:
            ValueError: If the chatbot ID is invalid.
        """
        pipeline_key = (chatbot_id, str(model_id), organization_id)

        if pipeline_key not in self._pipeline_cache:
            logger.warning(
                f"Pipeline not found for chatbot `{chatbot_id}` model `{model_id}`, attempting to rebuild..."
            )
            # Try to rebuild the pipeline if it's not found
            await self._async_rebuild_pipeline(chatbot_id, str(model_id), organization_id)

        if pipeline_key not in self._pipeline_cache:
            # Check if there's a stored error message for this pipeline
            stored_error = self.get_pipeline_build_error(chatbot_id, str(model_id), organization_id)
            if stored_error:
                raise ValueError(
                    f"Pipeline for chatbot `{chatbot_id}` model `{model_id}` not found and could not be rebuilt. "
                    f"Previous build error: {stored_error}"
                )
            else:
                raise ValueError(
                    f"Pipeline for chatbot `{chatbot_id}` model `{model_id}` not found and could not be rebuilt"
                )

        return self._pipeline_cache[pipeline_key]

    def get_pipeline_config(self, chatbot_id: str, organization_id: str = DEFAULT_ORGANIZATION_ID) -> dict[str, Any]:
        """Get the pipeline configuration by chatbot ID.

        Args:
            chatbot_id (str): The chatbot ID.
            organization_id (str): The organization ID.

        Returns:
            dict[str, Any]: The pipeline configuration.

        Raises:
            ValueError: If the chatbot or pipeline is not found.
        """
        self._validate_pipeline(chatbot_id, organization_id)
        return self._chatbot_configs[(chatbot_id, organization_id)].pipeline_config

    def get_pipeline_type(self, chatbot_id: str, organization_id: str = DEFAULT_ORGANIZATION_ID) -> str:
        """Get the pipeline type for the given chatbot.

        Args:
            chatbot_id (str): The chatbot ID.
            organization_id (str): The organization ID.
        """
        return self._chatbot_configs[(chatbot_id, organization_id)].pipeline_type

    def get_use_docproc(self, chatbot_id: str, organization_id: str = DEFAULT_ORGANIZATION_ID) -> bool:
        """Get whether DocProc should be used for this chatbot.

        Args:
            chatbot_id (str): The chatbot ID.
            organization_id (str): The organization ID.

        Returns:
            bool: Whether DocProc should be used.

        Raises:
            ValueError: If the chatbot or pipeline is not found.
        """
        self._validate_pipeline(chatbot_id, organization_id)
        config = self._chatbot_configs[(chatbot_id, organization_id)].pipeline_config
        return config["use_docproc"]

    def get_max_file_size(self, chatbot_id: str, organization_id: str = DEFAULT_ORGANIZATION_ID) -> int | None:
        """Get maximum file size for the given chatbot.

        Args:
            chatbot_id (str): The chatbot ID.
            organization_id (str): The organization ID.

        Returns:
            int | None: The maximum file size if provided.

        Raises:
            ValueError: If the chatbot or pipeline is not found.
        """
        self._validate_pipeline(chatbot_id, organization_id)
        config = self._chatbot_configs[(chatbot_id, organization_id)].pipeline_config
        return config.get("max_file_size")

    async def create_chatbot(
        self, app_config: AppConfig, chatbot_id: str, organization_id: str = DEFAULT_ORGANIZATION_ID
    ) -> None:
        """Create a new chatbot.

        Args:
            app_config (AppConfig): The application configuration.
            chatbot_id (str): The ID of the chatbot.
            organization_id (str): The organization ID.
        """
        chatbot_info = app_config.chatbots.get(chatbot_id)

        if not chatbot_info or not chatbot_info.pipeline:
            logger.warning(f"Pipeline config not found for chatbot `{chatbot_id}`")
            return

        pipeline_info = chatbot_info.pipeline
        pipeline_type = pipeline_info["type"]
        pipeline_organization_id = (pipeline_type, organization_id)
        plugin = self._plugins.get(pipeline_organization_id)
        if not plugin:
            logger.warning(f"Pipeline plugin not found for chatbot `{chatbot_id}`")
            return

        logger.info(f"Storing pipeline config for chatbot `{chatbot_id}`")
        self._chatbot_configs[(chatbot_id, organization_id)] = ChatbotConfig(
            pipeline_type=pipeline_type,
            pipeline_config=pipeline_info["config"],
            prompt_builder_catalogs=pipeline_info["prompt_builder_catalogs"],
            lmrp_catalogs=pipeline_info["lmrp_catalogs"],
        )

        supported_models = list(pipeline_info["config"].get("supported_models", {}).values())
        await __class__._build_plugin(self, chatbot_id, supported_models, plugin, organization_id)

    async def delete_chatbot(self, chatbot_id: str, organization_id: str = DEFAULT_ORGANIZATION_ID) -> None:
        """Delete a chatbot.

        Args:
            chatbot_id (str): The ID of the chatbot.
            organization_id (str): The organization ID.
        """
        chatbot_organization_id = (chatbot_id, organization_id)
        for pipeline_key in self._chatbot_pipeline_keys.get(chatbot_organization_id, set()):
            self._pipeline_cache.pop(pipeline_key, None)

        # Clear stored error messages for this chatbot
        error_keys_to_remove = [key for key in self._pipeline_build_errors.keys() if key[0] == chatbot_organization_id]
        for key in error_keys_to_remove:
            self._pipeline_build_errors.pop(key, None)

        self._chatbot_pipeline_keys.pop(chatbot_organization_id, None)
        self._chatbot_configs.pop(chatbot_organization_id, None)
        self._builders.pop(chatbot_organization_id, None)

    async def update_chatbots(
        self, app_config: AppConfig, chatbot_ids: list[str], organization_id: str = DEFAULT_ORGANIZATION_ID
    ) -> None:
        """Update the chatbots.

        Args:
            app_config (AppConfig): The application configuration.
            chatbot_ids (list[str]): The updated chatbot IDs.
            organization_id (str): The organization ID.
        """
        for chatbot_id in chatbot_ids:
            chatbot_organization_id = (chatbot_id, organization_id)
            try:
                chatbot_info = app_config.chatbots.get(chatbot_id)
                if not chatbot_info or not chatbot_info.pipeline:
                    logger.warning(f"Pipeline config not found for chatbot `{chatbot_id}`")
                    continue

                pipeline_info = chatbot_info.pipeline
                pipeline_type = pipeline_info["type"]

                supported_models = list(pipeline_info["config"].get("supported_models", {}).values())

                logger.info(f"Storing pipeline config for chatbot `{chatbot_id}`")
                self._chatbot_configs.pop(chatbot_organization_id, None)
                self._chatbot_configs[chatbot_organization_id] = ChatbotConfig(
                    pipeline_type=pipeline_type,
                    pipeline_config=pipeline_info["config"],
                    prompt_builder_catalogs=pipeline_info["prompt_builder_catalogs"],
                    lmrp_catalogs=pipeline_info["lmrp_catalogs"],
                )

                new_pipeline_keys = set()
                for model in supported_models:
                    model_id = model.get("model_id", model.get("name"))
                    new_pipeline_key = (chatbot_id, str(model_id), organization_id)
                    new_pipeline_keys.add(new_pipeline_key)

                for pipeline_key in self._chatbot_pipeline_keys.get(chatbot_organization_id, set()):
                    if pipeline_key not in new_pipeline_keys:
                        self._pipeline_cache.pop(pipeline_key, None)

                self._chatbot_pipeline_keys[chatbot_organization_id] = set()

                pipeline_organization_id = (pipeline_type, organization_id)
                plugin = self._plugins.get(pipeline_organization_id)
                if not plugin:
                    logger.warning(f"Pipeline plugin not found for chatbot `{chatbot_id}`")
                    continue

                self._builders.pop(chatbot_organization_id, None)
                self._builders[chatbot_organization_id] = plugin

                await __class__._build_plugin(self, chatbot_id, supported_models, plugin, organization_id)
            except Exception as e:
                logger.warning(f"Error updating chatbot `{chatbot_id}`: {e}")

    def _prepare_pipelines(self) -> None:
        """Build pipeline configurations from the chatbots configuration."""
        pipeline_types: set[tuple[str, str]] = set()
        chatbot_preset_map: dict[str, dict[str, PipelinePresetConfig]] = {}
        for org_id, org_app_config in self.app_config.items():
            chatbot_preset_map.setdefault(org_id, {})
            for chatbot_id, chatbot_info in org_app_config.chatbots.items():
                if not chatbot_info.pipeline:
                    logger.warning(f"Pipeline config not found for chatbot `{chatbot_id}`")
                    continue

                pipeline_info = chatbot_info.pipeline
                pipeline_type = pipeline_info["type"]

                chatbot_preset_map[org_id][chatbot_id] = PipelinePresetConfig(
                    preset_id=pipeline_info["config"]["pipeline_preset_id"],
                    supported_models=list(pipeline_info["config"].get("supported_models", {}).values()),
                )

                logger.info(f"Storing pipeline config for chatbot `{chatbot_id}`")
                self._chatbot_configs[(chatbot_id, org_id)] = ChatbotConfig(
                    pipeline_type=pipeline_type,
                    pipeline_config=pipeline_info["config"],
                    prompt_builder_catalogs=pipeline_info["prompt_builder_catalogs"],
                    lmrp_catalogs=pipeline_info["lmrp_catalogs"],
                )
                pipeline_types.add((pipeline_type, org_id))

        for pipeline_type, org_id in pipeline_types:
            self._activated_configs[(pipeline_type, org_id)] = ChatbotPresetMapping(
                pipeline_type=pipeline_type,
                chatbot_preset_map=chatbot_preset_map[org_id],
            )

    def _validate_pipeline(self, chatbot_id: str, organization_id: str) -> None:
        """Validate the pipeline configuration exists.

        Args:
            chatbot_id (str): The chatbot ID.
            organization_id (str): The organization ID.

        Raises:
            ValueError: If the chatbot or pipeline configuration is not found.
        """
        chatbot_organization_id = (chatbot_id, organization_id)
        if chatbot_organization_id not in self._chatbot_configs:
            raise ValueError(f"Pipeline configuration for chatbot `{chatbot_organization_id}` not found")

    def _store_pipeline_build_error(
        self, chatbot_id: str, model_id: str, organization_id: str, error_message: str
    ) -> None:
        """Store error message for failed pipeline build.

        Args:
            chatbot_id (str): The chatbot ID.
            model_id (str): The model ID.
            organization_id (str): The organization ID.
            error_message (str): The error message to store.
        """
        pipeline_key = (chatbot_id, str(model_id), organization_id)
        self._pipeline_build_errors[pipeline_key] = error_message

    def get_pipeline_build_error(self, chatbot_id: str, model_id: str, organization_id: str) -> str | None:
        """Get stored error message for failed pipeline build.

        Args:
            chatbot_id (str): The chatbot ID.
            model_id (str): The model ID.
            organization_id (str): The organization ID.

        Returns:
            str | None: The stored error message if available, None otherwise.
        """
        pipeline_key = (chatbot_id, str(model_id), organization_id)
        return self._pipeline_build_errors.get(pipeline_key)

    async def aget_pipeline_builder(self, chatbot_id: str, organization_id: str) -> Plugin:
        """Get a pipeline builder instance for the given chatbot (async version).

        Args:
            chatbot_id (str): The chatbot ID.
            organization_id (str): The organization ID.

        Returns:
            Plugin: The pipeline builder instance.

        Raises:
            ValueError: If the chatbot ID is invalid or the model name is not supported.
        """
        chatbot_organization_id = (chatbot_id, organization_id)
        if chatbot_organization_id not in self._builders:
            logger.warning(
                f"Pipeline builder not found for chatbot `{chatbot_organization_id}`, attempting to rebuild..."
            )
            # Try to rebuild the plugin if it's not found
            await self._async_rebuild_plugin(chatbot_id, organization_id)

        if chatbot_organization_id not in self._builders:
            # Check if there are any stored error messages for this chatbot
            chatbot_errors = []
            for (c_id, m_id, o_id), error_msg in self._pipeline_build_errors.items():
                if c_id == chatbot_id and o_id == organization_id:
                    chatbot_errors.append(f"Model `{m_id}`: {error_msg}")

            if chatbot_errors:
                error_details = "; ".join(chatbot_errors)
                raise ValueError(
                    f"Pipeline builder for chatbot `{chatbot_id}` not found and could not be rebuilt. "
                    f"Previous build errors: {error_details}"
                )
            else:
                raise ValueError(f"Pipeline builder for chatbot `{chatbot_id}` not found and could not be rebuilt")

        return self._builders[chatbot_organization_id]

    async def _async_rebuild_plugin(self, chatbot_id: str, organization_id: str) -> None:
        """Asynchronously rebuild a plugin for the given chatbot.

        Args:
            chatbot_id (str): The chatbot ID.
            organization_id (str): The organization ID.
        """
        try:
            # Check if we have the chatbot configuration
            chatbot_organization_id = (chatbot_id, organization_id)
            if chatbot_organization_id not in self._chatbot_configs:
                logger.warning(f"Chatbot configuration not found for `{chatbot_organization_id}`")
                return

            chatbot_config = self._chatbot_configs[chatbot_organization_id]
            pipeline_type = chatbot_config.pipeline_type
            pipeline_organization_id = (pipeline_type, organization_id)

            # Check if we have the plugin for this pipeline type
            if pipeline_organization_id not in self._plugins:
                logger.warning(f"Plugin not found for pipeline type `{pipeline_organization_id}`")
                return

            plugin = self._plugins[pipeline_organization_id]

            # Get supported models from the configuration
            supported_models = list(chatbot_config.pipeline_config.get("supported_models", {}).values())

            if not supported_models:
                logger.warning(f"No supported models found for chatbot `{chatbot_id}`")
                return

            # Use the existing _build_plugin method to rebuild the plugin
            await __class__._build_plugin(self, chatbot_id, supported_models, plugin, organization_id)

            logger.info(f"Successfully rebuilt pipeline builder for chatbot `{chatbot_id}`")

        except Exception as e:
            error_message = f"Error rebuilding plugin for chatbot `{chatbot_id}`: {e}"
            logger.warning(error_message)

            # Store the error message for later retrieval (using a generic model_id for plugin-level errors)
            self._store_pipeline_build_error(chatbot_id, "__plugin__", organization_id, error_message)
