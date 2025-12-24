import csv
import os
from typing import List, Any

from jenerationutils.data_connections.base_connector import BaseConnector
from jenerationutils.data_connections.registry import register

@register("csv")
class CSVConnector(BaseConnector):
    """
    Concrete connector implementation for appending data to CSV files.

    Handles creating new CSV files with headers and appending rows of 
    data to existing files.
    """
    def __init__(self, config):
        """
        Initializes the CSV connector.

        Args:
            config (dict): Must contain 'data_source_location' (str), which
                           is the file path to the CSV.
        """
        super().__init__(config)


    def append_data(self, data):
        """
        Appends a row of data to the CSV file indicated in the config.

        Args:
            data (List[Any]): A list of values representing a single row.
                              Order must match the CSV headers.

        Raises:
            FileNotFoundError: If the file at 'data_source_location' does not exist.
            IOError: If there is an issue opening or writing to the file.
        """
        path = self.config.get("data_source_location")
        
        if not path or not os.path.exists(path):
            raise FileNotFoundError(f"The file at '{path}' could not be found.")

        with open(path, "a", newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(data)


    def create_new_data_source(self, headers: List[str]):
        """
        Creates a new CSV file and writes the header row.

        Args:
            headers (List[str]): List of strings of column headers.

        Raises:
            FileExistsError: If the file already exists (due to mode 'x').
            IOError: If the file cannot be created.
        """
        path = self.config.get("data_source_location")

        with open(path, "x", newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)


    def close():
        """
        Implementation not needed for CSV files.
        """
        pass
