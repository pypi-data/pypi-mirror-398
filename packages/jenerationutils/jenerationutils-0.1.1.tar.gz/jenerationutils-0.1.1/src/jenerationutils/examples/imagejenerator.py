import datetime
import copy

from pydantic import BaseModel

from imagejenerator.models import registry as model_registry
from jenerationutils.jenerationrecord import registry as recorder_registry
from jenerationutils.data_connections import registry as data_connections_registry
from jenerationutils.benchmarker.benchmarker import Benchmarker

config = {
    "model": "stable-diffusion-v1-5",
    "model_path": "runwayml/stable-diffusion-v1-5",

    "device": "cuda",
    "enable_attention_slicing": True,
    "scheduler": "EulerDiscreteScheduler",

    "height": 512,
    "width": 512,
    "num_inference_steps": 40,
    "guidance_scale": 10,
    "images_to_generate": 1,
    "seeds": [],
    "dtype": "bfloat16",

    "image_save_folder": "./images/",

    "output_data_type": "csv",
    "save_image_gen_stats": True,
    "data_source_location": f"./stats/image_gen_stats.csv",

    "prompts": [
        "A high-tech cyberpunk greenhouse inside a glass dome on Mars, lush bioluminescent alien plants glowing neon blue and purple, dusty red Martian landscape visible through the glass, cinematic lighting, hyper-detailed, 8k, synthwave aesthetic."
    ]
}

image_generator = model_registry.get_model_class(config)
image_generator.create_pipeline()

# Timing the inference
with Benchmarker() as benchmarker:
    image_generator.run_pipeline()

image_generator.save_image()

# Your app must define the schema used by its data source as a Pydantic class
class Schema(BaseModel):
    filename: str = ""
    timestamp: str = ""
    model: str = ""
    device: str = ""
    dtype: str = ""
    prompt: str = ""
    seed: int = 0
    height: int = 0
    width: int = 0
    inf_steps: int = 0
    guidance_scale: float = 0
    batch_generation_time: float | None = None
    image_generation_time: float | None = None
    image_rating: int = -1

# Import the generation record class according to your data source (csv, later SQLite etc.)
GenerationRecordClass = recorder_registry.get_class("csv")

# Because this used imagejenerator, we get an interable of images, even if you only generated one image.
# imagejenerator has a helper function that collates the generation metadata for each image
# We just add the inference time to it, and then instantiate a GenerationRecord with the metadata, and the
# schema we defined above. The Generation record will then validate the metadata against the schema.
image_generation_records = []
for metadata_record in image_generator.get_metadata():
    metadata_record["batch_generation_time"] = benchmarker.execution_time
    metadata_record["image_generation_time"] = benchmarker.execution_time / image_generator.batch_size
    image_generation_record = GenerationRecordClass(
        schema = Schema,
        generation_metadata = metadata_record
    )

    image_generation_records.append(image_generation_record)

# Create a connector to your data source. Your config just need a "data_source_location" property with the path to the CSV.
csv_connector = data_connections_registry.get_object(config)
# In this example, we're creating a new datasource. The CSVGenerationRecord has a helper function that creates a header row for
# the CSV file, but you can do this any way you like.
csv_connector.create_new_data_source(image_generation_records[0].create_header_row())

# Now we just loop through our list of CSVGenerationRecords and call the `create_data_row()` method to create a string to add to the CSV
# and use the CSVConnector's `append_data()` method to save it to the CSV.
for image_generation_record in image_generation_records:
    data_row = image_generation_record.create_data_row()
    csv_connector.append_data(data_row)