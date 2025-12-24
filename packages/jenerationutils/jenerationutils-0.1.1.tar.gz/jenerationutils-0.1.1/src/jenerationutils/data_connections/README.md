# README.md for the 'data_connections' package

# Data Connections

A lightweight, extensible library for connecting to and writing data to various storage backends.

## Overview

`Data Connections` provides a unified interface (`BaseConnector`) for saving data records. It uses a registry pattern (a Factory pattern) to dynamically select the storage backend (e.g., CSV, SQL) based on a configuration dictionary. 

## Features

* **Unified API:** Switch between storage backends without changing your application code.
* **Dynamic Loading:** Uses a registry system to load connectors at runtime.
* **Lightweight:** Minimal dependencies.

## Installation

Ensure this package is available in your Python environment or path.

## Usage

### 1. Configuration

Prepare your configuration dictionary. This must include:
* `output_data_type`: Matches the registered name of the connector (e.g., `"csv"`).
* `data_source_location`: The path or connection string to the resource.

```py
config = {
    "output_data_type": "csv",
    "data_source_location": "./output/results.csv"
}
```

### 2. Instantiating a Connector

Use the `get_object` factory to create the correct connector instance.

```py
from data_connections.registry import get_object

connector = get_object(config)
```

### 3. Creating a Data Source

If you are starting a new run and need to initialize the file or database table:

```py
headers = ["timestamp", "prompt", "duration", "image_path"]
try:
    connector.create_new_data_source(headers)
except FileExistsError:
    print("File already exists, skipping creation.")
```

### 4. Appending Data

Pass a list (for CSV) or dict (depending on the specific implementation) to append data.

```py
data_row = ["2023-10-27", "A cat in space", 4.5, "./images/cat.png"]
connector.append_data(data_row)
```

## Extending

To add a new data source (e.g., SQLite), subclass `BaseConnector` and decorate it:

```py
from .base_connector import BaseConnector
from .registry import register

@register("sqlite")
class SQLiteConnector(BaseConnector):
    def append_data(self, data):
        # Implementation here

    
    def create_new_data_source(self, headers):
        # Implementation here

```