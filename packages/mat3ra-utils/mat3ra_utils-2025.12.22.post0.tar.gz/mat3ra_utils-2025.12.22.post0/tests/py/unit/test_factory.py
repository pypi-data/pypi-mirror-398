from mat3ra.utils import factory as factory


def test_BaseFactory():
    """
    Test the factory method
    """

    class ObjectFactory(factory.BaseFactory):
        __class_registry__ = {
            "object_name_1": "mat3ra.utils.factory.BaseFactory",
        }

    class_reference = ObjectFactory.get_class_by_name("object_name_1")
    class_instance = class_reference()
    assert class_instance.__class__.__name__ == "BaseFactory"
