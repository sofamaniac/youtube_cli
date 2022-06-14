from property import global_properties, AllProperties, Property


class Scope:
    def __init__(self, parent=global_properties):
        self.parent = parent
        self.properties = AllProperties()

    def add_property(self, property):
        self.properties.add_property(property)

    def find_property(self, name):
        prop = self.properties.find_property(name)
        if not prop and self.parent:
            return self.parent.find_property(name)
        return prop


functions_list = Scope(parent=None)


class Node:
    def __init__(self):
        self.scope = None
        pass

    def set_scope(self, scope):
        self.scope = scope

    def execute(self):
        pass


class Constant(Node):
    def __init__(self, value):
        self.value = value
        super().__init__()

    def execute(self):
        return self.value

    def __str__(self):
        return str(self.value)


class VariableDecleration(Node):
    def __init__(self, name: str, value: Node):

        self.name = name
        self.value = value
        super().__init__()

    def execute(self):
        value = self.value.execute()
        prop = Property(self.name, value)
        self.scope.add_property(prop)
        return value

    def __str__(self):
        return f"let {self.name} = {self.value}"


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

    def __str__(self):
        return f"{self.name} = {self.value}"


class VariableRead(Node):
    def __init__(self, name):

        self.name = name
        super().__init__()

    def execute(self):

        prop = self.scope.find_property(self.name)
        return prop.get()

    def __str__(self):
        return self.name


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

    def __str__(self):
        code = "\n".join([str(c) for c in self.instructions])
        return "{\n" + code + "\n}"


class IfElse(Node):
    def __init__(self, condition, if_block, else_block=None):

        self.condition = condition
        self.if_block = if_block
        self.else_block = else_block
        super().__init__()

    def set_scope(self, scope):
        self.scope = scope
        self.condition.set_scope(scope)
        self.if_block.set_scope(scope)
        if self.else_block:
            self.else_block.set_scope(scope)

    def execute(self):
        if self.condition.execute():
            return self.if_block.execute()
        elif self.else_block:
            return self.else_block.execute()

    def __str__(self):
        l1 = f"if ({self.condition})"
        l2 = str(self.if_block)
        l3 = ("else\n" + str(self.else_block)) if self.else_block else ""
        return "\n".join([l1, l2, l3])


class While(Node):
    def __init__(self, condition, block):
        self.condition = condition
        self.loop = block
        super().__init__()

    def set_scope(self, scope):
        self.scope = scope
        self.condition.set_scope(scope)
        self.loop.set_scope(scope)

    def execute(self):
        while self.condition.execute():
            self.loop.execute()

    def __str__(self):
        l1 = f"while ({self.condition})"
        l2 = str(self.loop)
        return l1 + "\n" + l2


class FunctionDecleration(Node):
    def __init__(self, name, args, code):
        self.name = name
        self.args = args
        self.code = code
        super().__init__()

    def set_scope(self, scope):
        self.code.set_scope(scope)

    def run(self, *args):
        if len(*args) != len(self.args):
            raise Exception
        scope = self.code.get_scope()
        if not scope:
            raise Exception
        for name, value in zip(self.args, *args):
            scope.add_property(name, value)
        self.code.set_scope(scope)
        self.code.execute()

    def execute(self):
        functions_list.add_property(Property(self.name, self.run))


class FunctionCall(Node):
    def __init__(self, name, args=[]):

        self.name = name
        self.args = args
        super().__init__()

    def execute(self):
        fun = functions_list.find_property(self.name)
        args = [p.execute() for p in self.args]
        if fun:
            fun.get()(*args)

    def __str__(self):
        return f"{self.name}" + " ".join([str(a) for a in self.args])


class Program(Node):
    def __init__(self, commands):
        self.commands = commands
        super().__init__()

    def execute(self):

        for c in self.commands:
            c.execute()

    def set_scope(self, scope):
        self.scope = scope
        for c in self.commands:
            c.set_scope(scope)

    def __str__(self):
        return "\n".join([str(c) for c in self.commands])


class BinaryOp(Node):
    def __init__(self, op):
        self.op = op
        self.x = None
        self.y = None
        super().__init__()

    def execute(self):
        self.op(self.x, self.y)

    def __str__(self):
        return f"{self.x} binop {self.y}"
