"""Base Pipeline Preset Config.

Authors:
    Ryan Ignatius Hadiwijaya (ryan.i.hadiwijaya@gdplabs.id)

References:
    NONE
"""

from typing import Any

from pydantic import BaseModel, Field

from glchat_plugin.config.constant import (
    GUARDRAIL_ERR_MSG,
    GuardrailMode,
    SearchType,
    TopicSafetyMode,
)


class BasePipelinePresetConfig(BaseModel):
    """A Pydantic model representing the base preset configuration of all pipelines.

    Attributes:
        pipeline_preset_id (str): The pipeline preset id.
        supported_models (dict[str, Any]): The supported models.
        supported_agents (list[str]): The supported agents.
        support_pii_anonymization (bool): Whether the pipeline supports pii anonymization.
        support_multimodal (bool): Whether the pipeline supports multimodal.
        use_docproc (bool): Whether to use the document processor.
        search_types (list[SearchType]): The supported search types.
        enable_guardrails (bool): Whether to enable guardrails.
        guardrail_mode (GuardrailMode): The guardrail mode.
        banned_phrases (str): The banned phrases.
        topic_safety_mode (TopicSafetyMode): The topic safety mode.
        allowed_topics (str): The allowed topics.
        guardrail_fallback_message (str): The guardrail fallback message.
        retrieve_memory_threshold (float): The retrieve memory threshold.
        retrieve_memory_top_k (int): The retrieve memory top k.
        enable_memory (bool): Whether to enable memory.
        enable_live_chat (bool): Whether to enable live chat.
        use_cache (bool): Whether to use cache.
        chat_history_limit (int): The chat history limit.
        anonymize_em (bool): Whether to anonymize before using the embedding model.
        anonymize_lm (bool): Whether to anonymize before using the language model.
        prompt_context_char_threshold (int): The character limit above which the prompt is assumed
            to have contained the context.
        enable_standalone_query (bool): Whether to enable standalone query.
    """

    pipeline_preset_id: str
    supported_models: dict[str, Any]
    supported_agents: list[str]
    support_pii_anonymization: bool
    support_multimodal: bool
    use_docproc: bool
    search_types: list[SearchType]
    enable_guardrails: bool = False
    guardrail_mode: GuardrailMode = Field(default=GuardrailMode.INPUT_ONLY)
    banned_phrases: str = "[]"
    topic_safety_mode: TopicSafetyMode = TopicSafetyMode.HYBRID
    allowed_topics: str = "[]"
    guardrail_fallback_message: str = Field(default=GUARDRAIL_ERR_MSG)
    retrieve_memory_threshold: float = Field(default=0.3, ge=0, le=1)
    retrieve_memory_top_k: int = Field(default=10, ge=1)
    enable_memory: bool = False
    enable_live_chat: bool = False
    use_cache: bool
    chat_history_limit: int
    anonymize_em: bool
    anonymize_lm: bool
    prompt_context_char_threshold: int
    enable_standalone_query: bool = True
