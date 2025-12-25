from synalinks.src.api_export import synalinks_export
from synalinks.src.language_models.language_model import LanguageModel
from synalinks.src.saving import serialization_lib

ALL_OBJECTS = {
    LanguageModel,
}

ALL_OBJECTS_DICT = {cls.__name__.lower(): cls for cls in ALL_OBJECTS}


@synalinks_export("synalinks.language_models.serialize")
def serialize(language_model):
    """Returns the optimizer configuration as a Python dict.

    Args:
        optimizer: An `LanguageModel` instance to serialize.

    Returns:
        Python dict which contains the configuration of the language model.
    """
    return serialization_lib.serialize_synalinks_object(language_model)


@synalinks_export("synalinks.language_models.deserialize")
def deserialize(config, custom_objects=None):
    """Returns a Synalinks language model object via its configuration.

    Args:
        config: LanguageModel configuration dictionary.
        custom_objects: Optional dictionary mapping names (strings) to custom
            objects (classes and functions) to be considered during
            deserialization.

    Returns:
        A Synalinks LanguageModel instance.
    """
    # Make deserialization case-insensitive for built-in language model.
    if config["class_name"].lower() in ALL_OBJECTS_DICT:
        config["class_name"] = config["class_name"].lower()

    return serialization_lib.deserialize_synalinks_object(
        config,
        module_objects=ALL_OBJECTS_DICT,
        custom_objects=custom_objects,
    )
