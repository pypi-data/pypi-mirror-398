"""Interface for Anonymizer Storage.

Authors:
    Hermes Vincentius Gani (hermes.v.gani@gdplabs.id)

References:
    None
"""

from abc import ABC, abstractmethod
from typing import TypeVar

AnonymizerMapping = TypeVar("AnonymizerMapping")
MappingDataType = TypeVar("MappingDataType")


class BaseAnonymizerStorage(ABC):
    """Interface for anonymizer storage that defines methods for managing anonymizer mappings."""

    @abstractmethod
    def get_mappings_by_conversation_id(self, conversation_id: str) -> list[AnonymizerMapping]:
        """Retrieve anonymizer mappings by conversation ID.

        Args:
            conversation_id (str): The ID of the conversation.

        Returns:
            list[AnonymizerMapping]: A list of anonymizer mappings associated with the conversation ID.
        """
        pass

    @abstractmethod
    def create_mapping(
        self, conversation_id: str, pii_type: str, anonymized_value: str, pii_value: str
    ) -> AnonymizerMapping:
        """Create a new anonymizer mapping.

        Args:
            conversation_id (str): The ID of the conversation.
            pii_type (str): The type of personally identifiable information (PII).
            anonymized_value (str): The anonymized value of the PII.
            pii_value (str): The original PII value.

        Returns:
            AnonymizerMapping: The created anonymizer mapping.
        """
        pass

    @abstractmethod
    def update_mapping(self, conversation_id: str, is_anonymized: bool, mapping_data_type: MappingDataType) -> None:
        """Update the mappings for a specific conversation with new anonymizer mappings.

        Args:
            conversation_id (str): The unique identifier for the conversation.
            is_anonymized (bool): The flag to determine if the message is anonymized.
            mapping_data_type (MappingDataType): A dictionary of new anonymizer mappings to update for deanonymization.
        """
        pass
