"""Configuration schema for the GLLM backend.

Authors:
    Anggara Setiawan (anggara.t.setiawan@gdplabs.id)
    Hermes Vincentius Gani (hermes.v.gani@gdplabs.id)

References:
    None
"""

from typing import TypeVar

from pydantic import BaseModel

Chatbot = TypeVar("Chatbot")


class AppConfig(BaseModel):
    """Application configuration model."""

    chatbots: dict[str, Chatbot]
    user_chatbots: dict[str, list[str]]
