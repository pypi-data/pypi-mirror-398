from dataclasses import dataclass
from typing import List, Any

from jenerationutils.jenerationrecord.base_generation_record import BaseGenerationRecord
from jenerationutils.jenerationrecord.registry import register

@dataclass()
@register("csv")
class CSVGenerationRecord(BaseGenerationRecord):
    """
    A specific record implementation for CSV storage.

    This class handles the serialization of a Pydantic model into a flat
    list of values, suitable for use with the CSVConnector.
    """

    def create_data_row(self) -> List[Any]:
        """
        Flattens the Pydantic model into a list of values.

        Rounds floats to 2 decimal places.

        Returns:
            List[Any]: A list of values in the order defined by the schema.
        """
        row = []
        for name in self.completed_generation_record.model_fields:
            value = getattr(self.completed_generation_record, name)

            if isinstance(value, float):
                value = round(value, 2)

            row.append(value)

        return row


    def create_header_row(self):
        """
        Extracts field names from the schema to create CSV headers.

        Returns:
            List[str]: A list of column names.
        """
        return list(self.schema.model_fields.keys())
