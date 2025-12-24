from abc import ABC, abstractmethod


class BaseConnector(ABC):
    """
    Abstract base class defining the interface for data storage connectors.

    Acts as a contract for all concrete connector implementations
    (e.g., CSV, SQLite), ensuring they provide methods to create a data source
    and append data to it.

    Attributes:
        config (dict): Config dict containing connection details (e.g., file 
                       paths, connection strings, etc.).
    """
    def __init__(self, config):
        """
        Initializes the connector with a config.

        Args:
            config (dict): A dict containing necessary configuration
                           parameters for the specific child connector class 
                           (e.g., 'data_source_location', 'output_data_type').
        """
        self.config = config


    @abstractmethod
    def append_data(self, data: list | dict):
        """
        Appends a single record or batch of data to the data source.

        Args:
            data (list | dict): The data record to append. Format depends 
                                      the specific implementation (e.g., list 
                                      for CSV, dict for SQL).
        """
        pass


    @abstractmethod
    def create_new_data_source(self, headers: list):
        """
        Creates a new data source (e.g., CSV file, table, etc).

        Args:
            headers (list): A list of column names or schema definitions
                            required to initialize the data source.
        """
        pass

    @abstractmethod
    def close(self):
        """Clean up connection/file handler."""
        pass
