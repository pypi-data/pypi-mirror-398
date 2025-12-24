"""
Implements a lightweight, decorator-based registry pattern.

This module allows decoupling of class instantiation from the main application
logic. Classes register themselves via the @register decorator, and the
application creates instances at runtime based on string keys in a config.
"""

REGISTRY = {}

def register(name):
    """
    A decorator factory used to register a subclass.

    The decorated class is stored in the global REGISTRY dictionary
    under the provided `name`.

    Args:
        name (str): The unique key to identify this class (e.g., 'csv', 
                    'stable-diffusion-v1-5', 'llama-cpp', etc.).

    Returns:
        Callable: A decorator function that takes a class and registers it.
    """
    def decorator(cls):
        REGISTRY[name] = cls
        return cls
    return decorator


def get_class(type_):
    return REGISTRY[type_]


def get_object(config):
    """
    Retrieves and instantiates the correct class based on the config 
    dictionary.

    It looks up the class in REGISTRY using the key found in
    `config['output_data_type']`.

    Args:
        config (dict): The configuration dictionary, which must contain a
                       'output_data_type' key corresponding to a registered 
                       class name.

    Returns:
        An instantiated object of the registered generator class.

    Raises:
        KeyError: If the value of `config['output_data_type']` is not found 
                  in the REGISTRY.
    """
    Class_ = REGISTRY[config["output_data_type"]]
    object_ = Class_(config)

    return object_