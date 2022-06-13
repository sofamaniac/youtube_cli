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


class PropertyErrorType(Exception):
    pass


class Property:
    def __init__(self, name, value=None):
        self.value = value
        self.name = name
        properties_list.add_property(self)

    def set(self, new_value):
        if type(new_value) is type(self.value):
            self.value = new_value
            return self.value
        else:
            # TODO: maybe make failure silent ?
            raise (
                PropertyErrorType(
                    f"{self.name} : {type(self.value)} was expected but got {type(new_value)}"
                )
            )

    def get(self):
        return self.value
