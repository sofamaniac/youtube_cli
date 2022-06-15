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
