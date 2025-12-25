import importlib


def import_class(class_path: str) -> type:
    """Import class from module path.

    Args:
        class_path (str): Path to the class.

    Returns:
        type: Imported class.
    """
    module_path, class_name = class_path.rsplit('.', 1)
    module = importlib.import_module(module_path)

    return getattr(module, class_name)
