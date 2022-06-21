from types import NoneType


class AllProperties:
    def __init__(self):
        self.properties = []

    def find_property(self, name):
        for p in self.properties:
            if p.name == name:
                return p
        return None

    def add_property(self, prop):
        if p := self.find_property(prop.name):
            p.set(prop.value)
        else:
            self.properties.append(prop)


global_properties = AllProperties()


class PropertyTypeError(Exception):
    pass


class PropertyDoNotApplyChange(Exception):
    pass


class Property:
    def __init__(
        self, name, value, base_type=NoneType, on_change=None, custom_get=None
    ):
        self.value = value
        self.name = name
        self.on_change = on_change
        if base_type != NoneType:
            self.base_type = base_type
        else:
            self.base_type = type(value)
        global_properties.add_property(self)
        self.custom_get = custom_get

    def set(self, new_value):
        """Set the value of the property to [new_value]. If [new_value] is of different type
        than the previous value, raises a PropertyTypeError.
        If the [on_change] attribute was defined, it is called *before* the value of the
        property is changed."""
        if isinstance(new_value, self.base_type):
            try:
                if self.on_change:
                    self.on_change(new_value)
                self.value = new_value
            except PropertyDoNotApplyChange:
                pass
            return self.value
        else:
            raise (
                PropertyTypeError(
                    f"{self.name} : {type(self.value)} was expected but got {type(new_value)}"
                )
            )

    def get(self):
        """Returns the value of the property"""
        if self.custom_get:
            return self.custom_get()
        return self.value


class PropertyObject:
    """Class to inherit from when an object has properties"""

    def __init__(self):
        self.property_list = []

    def _add_property(self, name, value, base_type=NoneType, on_change=None):
        self.__dict__[name] = Property(
            name, value, base_type=base_type, on_change=on_change
        )
        self.property_list.append(name)

    def __set_property(self, name, value):
        if name in self.property_list:
            self.__dict__[name].set(value)

    def __getattribute__(self, name):
        if name == "property_list" or not name in self.property_list:
            return super().__getattribute__(name)
        return self.__dict__[name].get()

    def __setattr__(self, name, value):
        if name == "property_list" or not name in self.property_list:
            super().__setattr__(name, value)
        else:
            self.__set_property(name, value)
