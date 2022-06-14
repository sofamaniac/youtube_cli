from property import global_properties, AllProperties, Property

functions_list = AllProperties()


class Scope:
    def __init__(self, parent=global_properties):
        self.parent = parent
        self.properties = AllProperties()

    def addProperty(self, property):
        self.properties.append(property)

    def getProperty(self, name):
        pass

    pass


class Node:
    def __init__(self):
        self.scope = None
        pass

    def set_scope(self, scope):
        self.scope = scope
        pass

    def execute(self):
        pass


class Constant(Node):
    def __init__(self, value):
        self.value = value
        super().__init__()

    def execute(self):
        return self.value


class VariableDecleration(Node):
    def __init__(self, name: str, value: Node):

        self.name = name
        self.value = value
        super().__init__()

    def execute(self):
        value = self.value.execute()
        prop = Property(self.name, value)
        self.scope.addProperty(prop)
        return value


class VariableAssignment(Node):
    def __init__(self, name: str, value: Node):

        self.name = name
        self.value = value
        super().__init__()

    def set_scope(self, scope):

        self.scope = scope
        self.value.set_scope(scope)

    def execute(self):

        prop = self.scope.find_property(self.name)
        value = self.value.execute()
        return prop.set(value)


class VariableRead(Node):
    def __init__(self, name):

        self.name = name
        super.__init__()

    def execute(self):

        prop = self.scope.find_property(self.name)
        return prop.get()


class CodeBlock(Node):
    def __init__(self, instructions):
        self.instructions = instructions
        super().__init__()

    def set_scope(self, scope):
        self.scope = Scope(parent=scope)
        for instr in self.instructions:
            instr.set_scope(self.scope)

    def execute(self):
        ret = None
        for instr in self.instructions:
            ret = instr.execute()
        return ret


class FunctionDecleration(Node):
    def __init__(self, name, args, code):
        self.name = name
        self.args = args
        self.code = code
        super().__init__()

    def set_scope(self, scope):
        self.code.set_scope(scope)

    def execute(self):
        # TODO
        functions_list.addProperty(Property(self.name, None))


class FunctionCall(Node):
    def __init__(self, name, args=[]):

        self.name = name
        self.args = args
        super().__init__()

    def execute(self):

        pass


class Program(Node):
    def __init__(self, commands):
        self.commands = commands

    def execute(self):

        for c in self.commands:
            c.execute()

    def set_scope(self, scope):
        self.scope = scope
        for c in self.commands:
            c.set_scope(scope)
