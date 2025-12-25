import importlib
from collections.abc import Callable


class BaseFactory(object):
    """
    Base Factory class.
    """

    __class_registry__ = {
        "object_name1": "module.reference.to.ObjectName1",
        "object_name2": "module.reference.to.ObjectName2",
    }

    def __init__(self):
        pass

    @classmethod
    def get_class_by_name(cls, name: str) -> Callable:
        """
        Returns class by name.

        Args:
            name (str): class name.

        Returns:
             class
        """
        reference = cls.__class_registry__[name]
        return cls.get_class_by_module_reference(reference)

    @staticmethod
    def get_class_by_module_reference(reference: str) -> Callable:
        """
        Returns class by reference.

        Args:
            reference (str): reference, e.g. module.submodule.subsubmodule.ClassName

        Returns:
             class
        """
        modules = reference.split(".")
        class_name = modules[-1]
        module_name = ".".join(modules[:-1])
        return getattr(importlib.import_module(module_name), class_name)
