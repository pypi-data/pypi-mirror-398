import inspect

from synalinks.src import backend
from synalinks.src.api_export import synalinks_export
from synalinks.src.initializers.empty_initializer import Empty
from synalinks.src.initializers.initializer import Initializer
from synalinks.src.saving import serialization_lib
from synalinks.src.utils.naming import to_snake_case

ALL_OBJECTS = {
    Initializer,
    Empty,
}

ALL_OBJECTS_DICT = {cls.__name__: cls for cls in ALL_OBJECTS}
ALL_OBJECTS_DICT.update({to_snake_case(cls.__name__): cls for cls in ALL_OBJECTS})


@synalinks_export("synalinks.initializers.serialize")
def serialize(initializer):
    """Returns the initializer configuration as a Python dict."""
    return serialization_lib.serialize_synalinks_object(initializer)


@synalinks_export("synalinks.initializers.deserialize")
def deserialize(config, custom_objects=None):
    """Returns a Synalinks initializer object via its configuration."""
    return serialization_lib.deserialize_synalinks_object(
        config,
        module_objects=ALL_OBJECTS_DICT,
        custom_objects=custom_objects,
    )


@synalinks_export("synalinks.initializers.get")
def get(identifier):
    """Retrieves a Syanlinks initializer object via an identifier.

    The `identifier` may be the string name of a initializers function or class
    (case-sensitively).

    >>> identifier = 'Empty'
    >>> synalinks.initializers.get(identifier)
    <...synalinks.initializers.Empty...>

    You can also specify `config` of the initializer to this function by passing
    dict containing `class_name` and `config` as an identifier. Also note that
    the `class_name` must map to a `Initializer` class.

    >>> cfg = {'class_name': 'Empty', 'config': {...}}
    >>> synalinks.initializers.get(cfg)
    <...synalinks.initializers.Empty...>

    In the case that the `identifier` is a class, this method will return a new
    instance of the class by its constructor.

    Args:
        identifier (str | dict): A string, or dict specifying
            the initializer. If a string, it should be the name of an
            initializer. If a dict, it should contain the configuration of an
            initializer.

    Returns:
        Initializer instance base on the input identifier.
    """
    if identifier is None:
        return None
    if isinstance(identifier, dict):
        obj = deserialize(identifier)
    elif isinstance(identifier, str):
        config = {"class_name": str(identifier), "config": {}}
        obj = deserialize(config)
    else:
        obj = identifier
    if callable(obj):
        if inspect.isclass(obj):
            obj = obj()
        return obj
    else:
        raise ValueError(f"Could not interpret initializer identifier: {identifier}")
