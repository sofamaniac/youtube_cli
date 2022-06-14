class AllProperties:
    def __init__(self):
        self.properties = []

    def find_property(self, name):
        for p in self.properties:
            if p.name == name:
                return name

    def add_property(self, prop):
        self.properties.append(prop)


properties_list = AllProperties()


class PropertyTypeError(Exception):
    pass


class Property:
    def __init__(self, name, value=None, on_change=None):
        self.value = value
        self.name = name
        self.on_change = on_change
        properties_list.add_property(self)

    def set(self, new_value):
        """Set the value of the property to [new_value]. If [new_value] is of different type
        than the previous value, raises a PropertyTypeError.
        If the [on_change] attribute was defined, it is called *before* the value of the
        property is changed."""
        if type(new_value) is type(self.value):
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
