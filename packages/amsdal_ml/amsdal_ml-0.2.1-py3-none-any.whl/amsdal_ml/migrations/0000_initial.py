from amsdal_models.migration import migrations
from amsdal_utils.models.enums import ModuleType


class Migration(migrations.Migration):
    operations: list[migrations.Operation] = [
        migrations.CreateClass(
            module_type=ModuleType.CONTRIB,
            class_name="EmbeddingModel",
            new_schema={
                "title": "EmbeddingModel",
                "required": ["data_object_class", "data_object_id", "chunk_index", "raw_text", "embedding"],
                "properties": {
                    "data_object_class": {"type": "string", "title": "Linked object class"},
                    "data_object_id": {"type": "string", "title": "Linked object ID"},
                    "chunk_index": {"type": "integer", "title": "Chunk index"},
                    "raw_text": {"type": "string", "title": "Raw text used for embedding"},
                    "embedding": {
                        "type": "array",
                        "items": {"type": "number"},
                        "title": "Embedding",
                        "additional_type": "vector",
                        "dimensions": 1536,
                    },
                    "tags": {"type": "array", "items": {"type": "string"}, "title": "Embedding tags"},
                    "ml_metadata": {"type": "anything", "title": "ML metadata"},
                },
                "storage_metadata": {
                    "table_name": "embedding_model",
                    "db_fields": {},
                    "primary_key": ["partition_key"],
                    "foreign_keys": {},
                },
            },
        ),
    ]
