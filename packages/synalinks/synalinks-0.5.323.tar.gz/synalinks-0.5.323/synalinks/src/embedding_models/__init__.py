from synalinks.src.api_export import synalinks_export
from synalinks.src.embedding_models.embedding_model import EmbeddingModel
from synalinks.src.saving import serialization_lib

ALL_OBJECTS = {
    EmbeddingModel,
}

ALL_OBJECTS_DICT = {cls.__name__.lower(): cls for cls in ALL_OBJECTS}


@synalinks_export("synalinks.embedding_models.serialize")
def serialize(embedding_model):
    """Returns the optimizer configuration as a Python dict.

    Args:
        optimizer: An `EmbeddingModel` instance to serialize.

    Returns:
        Python dict which contains the configuration of the language model.
    """
    return serialization_lib.serialize_synalinks_object(embedding_model)


@synalinks_export("synalinks.embedding_models.deserialize")
def deserialize(config, custom_objects=None):
    """Returns a Synalinks language model object via its configuration.

    Args:
        config: EmbeddingModel configuration dictionary.
        custom_objects: Optional dictionary mapping names (strings) to custom
            objects (classes and functions) to be considered during
            deserialization.

    Returns:
        A Synalinks EmbeddingModel instance.
    """
    # Make deserialization case-insensitive for built-in embedding model.
    if config["class_name"].lower() in ALL_OBJECTS_DICT:
        config["class_name"] = config["class_name"].lower()

    return serialization_lib.deserialize_synalinks_object(
        config,
        module_objects=ALL_OBJECTS_DICT,
        custom_objects=custom_objects,
    )
