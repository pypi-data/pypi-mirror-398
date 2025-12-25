"""Constants for the API.

Authors:
    Ryan Ignatius Hadiwijaya (ryan.i.hadiwijaya@gdplabs.id)

References:
    None
"""

import warnings
from enum import StrEnum


class SearchType(StrEnum):
    """The type of search to perform.

    Attributes:
        NORMAL: Get answer from chatbot knowledge.
        SEARCH: Get answer from various connectors.
        SQL_SEARCH: Get answer from SQL-based database.
        WEB: Get more relevant information from the web. (DEPRECATED)
            Web Search uses real-time data. Agent selection isn't available in this mode.
        DEEP_RESEARCH: Get answer from Deep Research Agent.
        ESSENTIALS_DEEP_RESEARCH: Get answer from Deep Research with Essentials mode.
            Provides key points and core insights without noise, optimized for speed and clarity.
            Ideal for quick decision-making support and fast orientation.
        COMPREHENSIVE_DEEP_RESEARCH: Get answer from Deep Research with Comprehensive mode.
            Delivers the full picture with depth and thoroughness, covering all relevant angles,
            details, and supporting data. Suitable for professional research tasks where
            precision matters more than speed.
    """

    NORMAL = "normal"
    SEARCH = "search"
    SQL_SEARCH = "sql_search"
    _WEB = "web"  # Underscore to hide it from normal use
    _DEEP_RESEARCH = "deep_research"
    ESSENTIALS_DEEP_RESEARCH = "essentials_deep_research"
    COMPREHENSIVE_DEEP_RESEARCH = "comprehensive_deep_research"

    @property
    def WEB(cls) -> "SearchType":
        """Deprecated: Use SEARCH instead.

        Will be removed in version 0.3.0
        """
        warnings.warn(
            "SearchType.WEB is deprecated and will be removed in a future version. Use SearchType.SEARCH instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return cls._WEB

    # ruff: noqa: E501
    @property
    def DEEP_RESEARCH(cls) -> "SearchType":
        """Deprecated: Use ESSENTIALS_DEEP_RESEARCH or COMPREHENSIVE_DEEP_RESEARCH instead.

        Will be removed in version 0.3.0
        """
        warnings.warn(
            "SearchType.DEEP_RESEARCH is deprecated and will be removed in a future version. Use SearchType.ESSENTIALS_DEEP_RESEARCH or SearchType.COMPREHENSIVE_DEEP_RESEARCH instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return cls._DEEP_RESEARCH


class ReferenceFormatterType(StrEnum):
    """The type of reference formatter to use.

    Attributes:
        SIMILARITY: Use similarity based reference formatter.
        LM: Use LM based reference formatter.
        NONE: No reference formatter is used.
    """

    SIMILARITY = "similarity"
    LM = "lm"
    NONE = "none"


class TopicSafetyMode(StrEnum):
    """Topic safety mode enumeration for guardrail configuration."""

    ALLOWLIST = "allowlist"
    DENYLIST = "denylist"
    HYBRID = "hybrid"
    DISABLED = "disabled"


class GuardrailMode(StrEnum):
    """Guardrail mode enumeration for guardrail configuration."""

    DISABLED = "disabled"
    INPUT_ONLY = "input_only"
    OUTPUT_ONLY = "output_only"
    BOTH = "both"


GUARDRAIL_ERR_MSG = (
    "I apologize, but I cannot process your request as it appears to violate our content guidelines. "
    "This could be due to:\n"
    "- Inappropriate or harmful content\n"
    "- Requests that go against our safety policies\n"
    "- Content that may violate legal or ethical standards\n\n"
    "Please rephrase your question or ask about a different topic that complies with our guidelines."
)

DEFAULT_ORGANIZATION_ID = "-"
