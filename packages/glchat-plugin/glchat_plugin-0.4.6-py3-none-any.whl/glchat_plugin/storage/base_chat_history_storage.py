"""Interface for Chat History Storage.

Authors:
    Hermes Vincentius Gani (hermes.v.gani@gdplabs.id)

References:
    None
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import StrEnum
from typing import Any

from typing_extensions import TypeVar

from glchat_plugin.storage.base_anonymizer_storage import AnonymizerMapping

Conversation = TypeVar("Conversation")
Message = TypeVar("Message")
ConversationDocument = TypeVar("ConversationDocument")


class MessageRole(StrEnum):
    """Enum for Message Type."""

    USER = "USER"
    AI = "AI"


class DocumentStatus(StrEnum):
    """Enum for ConversationDocument Status."""

    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class BaseChatHistoryStorage(ABC):
    """Interface for chat history storage that defines methods for managing chat conversations and messages."""

    @abstractmethod
    def create_conversation(
        self, user_id: str, conversation_title: str, chatbot_id: str, **kwargs: Any
    ) -> Conversation:
        """Create a new conversation.

        Args:
            user_id (str): The ID of the user.
            conversation_title (str): The title of the conversation.
            chatbot_id (str): The ID of the chatbot.
            kwargs (Any): Additional arguments.

        Returns:
            Conversation: The created conversation.
        """
        pass

    @abstractmethod
    def get_conversation(self, user_id: str, conversation_id: str, **kwargs: Any) -> Conversation | None:
        """Retrieve a specific conversation by its ID.

        Args:
            user_id (str): The ID of the user.
            conversation_id (str): The ID of the conversation.
            kwargs (Any): Additional arguments.

        Returns:
            Conversation | None: The conversation if found, otherwise None.
        """
        pass

    @abstractmethod
    def get_conversations(
        self,
        user_id: str,
        query: str = "",
        chatbot_ids: list[str] | None = None,
        cursor: str | None = None,
        limit: int | None = None,
        **kwargs: Any,
    ) -> list[Conversation]:
        """Retrieve a list of conversations for a user.

        Args:
            user_id (str): The ID of the user.
            query (str, optional): A search query to filter conversations. Defaults to "".
            chatbot_ids (list[str] | None, optional): A list of chatbot IDs to filter conversations. Defaults to None.
            cursor (str | None, optional): A cursor for pagination. Defaults to None.
            limit (int | None, optional): The maximum number of conversations to retrieve. Defaults to None.
            kwargs (Any): Additional arguments.

        Returns:
            list[Conversation]: A list of conversations.
        """
        pass

    @abstractmethod
    def rename_conversation(self, user_id: str, conversation_id: str, new_title: str, **kwargs: Any) -> Conversation:
        """Rename an existing conversation.

        Args:
            user_id (str): The ID of the user.
            conversation_id (str): The ID of the conversation.
            new_title (str): The new title of the conversation.
            kwargs (Any): Additional arguments.

        Returns:
            Conversation: The updated conversation.
        """
        pass

    @abstractmethod
    def delete_conversation(self, user_id: str, conversation_id: str, **kwargs: Any) -> None:
        """Delete a conversation by its ID.

        Args:
            user_id (str): The ID of the user.
            conversation_id (str): The ID of the conversation.
            kwargs (Any): Additional arguments.

        Returns:
            None
        """
        pass

    @abstractmethod
    def delete_conversations(self, user_id: str, chatbot_id: str, **kwargs: Any) -> None:
        """Delete all conversations associated with a chatbot.

        Args:
            user_id (str): The ID of the user.
            chatbot_id (str): The ID of the chatbot.
            kwargs (Any): Additional arguments.

        Returns:
            None
        """
        pass

    @abstractmethod
    def save_message(
        self,
        user_id: str,
        conversation_id: str,
        message_list: list[Any],
        attachments: dict[str, Any] | None,
        **kwargs: Any,
    ) -> list[Message]:
        """Save a list of messages to a conversation.

        Args:
            user_id (str): The ID of the user.
            conversation_id (str): The ID of the conversation.
            message_list (list[Any]): A list of messages to save.
            attachments (dict[str, Any] | None): Attachments associated with the messages.
            kwargs (Any): Additional arguments.

        Returns:
            list[Message]: The saved messages.
        """
        pass

    @abstractmethod
    def get_message_by_id(self, message_id: str, **kwargs: Any) -> Message:
        """Retrieve a specific message by its ID.

        Args:
            message_id (str): The ID of the message.
            kwargs (Any): Additional arguments.

        Returns:
            Message: The message.
        """
        pass

    @abstractmethod
    def get_messages_by_ids(self, message_ids: list[str], **kwargs: Any) -> list[Message]:
        """Retrieve messages by their IDs.

        Args:
            message_ids (list[str]): A list of message IDs.
            kwargs (Any): Additional arguments.

        Returns:
            list[Message]: A list of messages.
        """
        pass

    @abstractmethod
    def get_messages(
        self,
        user_id: str,
        conversation_id: str,
        limit: int | None = None,
        max_timestamp: datetime | None = None,
        **kwargs: Any,
    ) -> list[Message]:
        """Retrieve messages from a conversation.

        Args:
            user_id (str): The ID of the user.
            conversation_id (str): The ID of the conversation.
            limit (int | None, optional): The maximum number of messages to retrieve. Defaults to None.
            max_timestamp (datetime | None, optional): The maximum timestamp for the messages. Defaults to None.
            kwargs (Any): Additional arguments.

        Returns:
            list[Message]: A list of messages.
        """
        pass

    @abstractmethod
    def update_message_metadata(self, message_id: str, metadata_: dict[str, Any], **kwargs: Any) -> Message:
        """Update the metadata of a message.

        Args:
            message_id (str): The ID of the message.
            metadata_ (dict[str, Any]): The metadata to update.
            kwargs (Any): Additional arguments.

        Returns:
            Message: The updated message.
        """
        pass

    @abstractmethod
    def delete_messages(self, user_id: str, message_ids: list[str], chatbot_ids: list[str], **kwargs: Any) -> None:
        """Delete messages by their IDs.

        Args:
            user_id (str): The ID of the user.
            message_ids (list[str]): A list of message IDs to delete.
            chatbot_ids (list[str]): A list of chatbot IDs associated with the messages.
            kwargs (Any): Additional arguments.

        Returns:
            None
        """
        pass

    @abstractmethod
    def create_conversation_document(
        self, conversation_id: str, status: str = DocumentStatus.PROCESSING.value, file_hash: str = "", **kwargs: Any
    ) -> ConversationDocument:
        """Create a new conversation document.

        Args:
            conversation_id (str): The ID of the conversation.
            status (str, optional): The status of the document. Defaults to DocumentStatus.PROCESSING.value.
            file_hash (str, optional): The hash of the file. Defaults to "".
            kwargs (Any): Additional arguments.

        Returns:
            ConversationDocument: The created conversation document.
        """
        pass

    @abstractmethod
    def get_conversation_document(self, document_id: str, **kwargs: Any) -> ConversationDocument:
        """Retrieve a conversation document by its ID.

        Args:
            document_id (str): The ID of the document.
            kwargs (Any): Additional arguments.

        Returns:
            ConversationDocument: The conversation document.
        """
        pass

    @abstractmethod
    def update_conversation_document(  # noqa: PLR0913
        self,
        document_id: str,
        status: str,
        number_of_chunks: int,
        message: str | None,
        error_type: str | None,
        object_key: str | None,
        **kwargs: Any,
    ) -> ConversationDocument:
        """Update a conversation document.

        Args:
            document_id (str): The ID of the document.
            status (str): The status of the document.
            number_of_chunks (int): The number of chunks in the document.
            message (str | None, optional): A message associated with the document. Defaults to None.
            error_type (str | None, optional): The type of error associated with the document. Defaults to None.
            object_key (str | None, optional): The object key of the document. Defaults to None.
            kwargs (Any): Additional arguments.

        Returns:
            ConversationDocument: The updated conversation document.
        """
        pass

    @abstractmethod
    def save_feedback(self, user_id: str, message_id: str, feedback: str, **kwargs: Any) -> None:
        """Save feedback for a message.

        Args:
            user_id (str): The ID of the user.
            message_id (str): The ID of the message.
            feedback (str): The feedback content.
            kwargs (Any): Additional arguments.

        Returns:
            None
        """
        pass

    @abstractmethod
    def get_deanonymized_message(
        self,
        user_id: str,
        conversation_id: str,
        message_id: str,
        is_anonymized: bool,
        mappings: list[AnonymizerMapping],
        **kwargs: Any,
    ) -> Message:
        """Retrieve a deanonymized message.

        Args:
            user_id (str): The ID of the user.
            conversation_id (str): The ID of the conversation.
            message_id (str): The ID of the message.
            is_anonymized (bool): Whether the message is anonymized.
            mappings (list[AnonymizerMapping]): A list of anonymizer mappings.
            kwargs (Any): Additional arguments.

        Returns:
            Message: The deanonymized message.
        """
        pass

    @abstractmethod
    def get_deanonymized_messages(
        self,
        messages: list[Message],
        is_anonymized: bool,
        mappings: list[AnonymizerMapping] | None = None,
        **kwargs: Any,
    ) -> list[Message]:
        """Retrieve a list of deanonymized messages.

        Args:
            messages (list[Message]): A list of messages.
            is_anonymized (bool): Whether the messages are anonymized.
            mappings (list[AnonymizerMapping] | None, optional): A list of anonymizer mappings. Defaults to None.
            kwargs (Any): Additional arguments.

        Returns:
            list[Message]: A list of deanonymized messages.
        """
        pass
