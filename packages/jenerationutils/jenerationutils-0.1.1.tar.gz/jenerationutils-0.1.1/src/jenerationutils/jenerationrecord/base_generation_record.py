from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Type, List, Dict
from pydantic import BaseModel

@dataclass
class BaseGenerationRecord(ABC):
    """
    Abstract base class for a validated generation record.

    This class acts as a wrapper around a Pydantic schema. It validates
    raw dictionary input against that schema, and defines the interface
    for serializing that data for specific storage formats (e.g., CSV).

    Attributes:
        schema (Type[BaseModel]): The Pydantic model class used for validation.
        generation_metadata (Dict[str, Any]): The data dictionary to be validated.
        completed_generation_record (BaseModel): The validated Pydantic model instance.
    """
    schema: Type[BaseModel]
    generation_metadata: dict[str: any] = None


    def __post_init__(self):
        """
        Validates the raw metadata against the provided Pydantic schema.
        
        Raises:
            pydantic.ValidationError: If the metadata does not match the schema.
        """
        self.completed_generation_record = self.schema(**self.generation_metadata)


    @abstractmethod
    def create_data_row(self) -> Any:
        """
        Serializes the validated data into a format suitable for the connector.

        Returns:
            Any: The formatted data (e.g., a list for CSV, a dict for JSON/SQL).
        """
        pass


    @abstractmethod
    def create_header_row(self) -> Any:
        """
        Generates the headers/keys for the data source.

        Returns:
            Any: The headers (e.g., list of strings for CSV).
        """
        pass
        
