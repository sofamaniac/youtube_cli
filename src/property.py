from types import NoneType


class AllProperties:
    def __init__(self):
        self.properties = []

    def find_property(self, name):
        for p in self.properties:
            if p.name == name:
                return p

    def add_property(self, prop):
        self.properties.append(prop)


properties_list = AllProperties()


class PropertyTypeError(Exception):
    pass


class Property:
    def __init__(self, name, value, base_type=NoneType, on_change=None):
        self.value = value
        self.name = name
        self.on_change = on_change
        if base_type != NoneType:
            self.base_type = base_type
        else:
            self.base_type = type(value)
        properties_list.add_property(self)

    def set(self, new_value):
        """Set the value of the property to [new_value]. If [new_value] is of different type
        than the previous value, raises a PropertyTypeError.
        If the [on_change] attribute was defined, it is called *before* the value of the
        property is changed."""
        if isinstance(new_value, self.base_type):
            if self.on_change:
                self.on_change(new_value)
            self.value = new_value
            return self.value
        else:
            raise (
                PropertyTypeError(
                    f"{self.name} : {type(self.value)} was expected but got {type(new_value)}"
                )
            )

    def get(self):
        """Returns the value of the property"""
        return self.value
