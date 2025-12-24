# Jeneration Record

A validation and serialisation layer for GenAI project metadata.

## Overview

This package acts as an adapter between your raw application generation metadata (dictionaries) and your storage connectors. It uses **Pydantic** to enforce strict schema validation and then serializes that data into the specific format required by your storage backend (e.g., flattening to a list for CSVs).

## Features

* **Schema Validation:** Ensures all data adheres to your defined Pydantic models before attempting to save.
* **Format Adaptation:** Automatically converts complex objects into storage-ready formats (e.g., rounding floats, flattening structures).
* **Extensible:** Uses a registry pattern to support different output formats.

## Installation

Ensure this package and `pydantic` are installed in your environment.

## Usage

### 1. Define Your Schema

Define the data structure you expect using Pydantic in your main application, e.g.:

```py
from pydantic import BaseModel

class ImageLogSchema(BaseModel):
    prompt: str
    seed: int
    duration: float
```

### 2. Instantiate the Record

1) Use `get_class()` from the registry to return the *Class* for your data source (e.g., "csv")
2) Pass your Schema *Class* (not instance) and your raw data dictionary to the class.
3) Default values will be applied for any entry in your schema that is not present in your raw data dict. Type mismatches with result in errors.
4) call the generation record's `create_data_row()` method to serialise the data, ready to be appended to your data source.

```py
from metadata_record.registry import get_class

# 1. Get the class responsible for CSV formatting
GenerationRecordClass = get_class("csv")

# 2. Define your schema:
class Schema(BaseModel):
    prompt: str = ""
    seed: int = -1
    duration: float = 0
    num_inference_steps: int = -1
    dtype: str = ""

# 3. Collate the raw generation metadata collected from your app
raw_data = {
    "prompt": "A futuristic city",
    "seed": 12345,
    "duration": 4.56789,
    "num_inference_steps": 30,
}

# 4. Create the Generation Record (Validation happens here automatically)
record = RecordClass(
    schema=Schema,
    generation_metadata=raw_data
)

# 5. Generate Output for Connector

# If creating a new file/table, get the headers/schema (based on your Pydantic model)
headers = record.create_header_row() 
# Output: ['prompt', 'seed', 'duration', 'num_inference_steps']

# Get the data row (for appending)
row = record.create_data_row()
# Output: ['A futuristic city', 12345, 4.57, 30, ""]  <-- Note the float rounding, and the addition of the default value for dtype
```

## Integration with Data Connections

This package is designed to feed directly into the `Data Connections` package, e.g.:

```py
connector.create_new_data_source(record.create_header_row())
connector.append_data(record.create_data_row())
```