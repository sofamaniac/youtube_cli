""" File containing the datastructures used by the parser"""


class UndefinedFunction(Exception):
    pass
class WrongArity(Exception):
    pass
class UnknowIdentifier(Exception):
    pass


class Scope:
    def __init__(self, parent=None):

        self.functions = {}
        self.variables = {}
        self.parent = parent

    def find(self, name):
        if name in self.functions.keys():
            return self.functions[name]
        elif self.parent:
            return self.parent.find(name)
        raise UnknowIdentifier

    def findVar(self, name):
        if name in self.variables.keys():
            return self.variables[name]
        elif self.parent:
            return self.parent.findVar(name)
        raise UnknowIdentifier(f"{name} not found")

    def findFun(self, name):
        if name in self.functions.keys():
            return self.functions[name]
        elif self.parent:
            return self.parent.findFun(name)
        raise UnknowIdentifier(f"{name} not found")

    def containsFun(self, name):
        if not self.parent:
            return name in self.functions.keys()
        else:
            return name in self.functions.keys() or self.parent.containsFun(name)

    def addVar(self, var):
        self.variables[var.name] = var

    def addFun(self, fun):
        self.functions[fun.name] = fun

globalScope = Scope(None)

class Command:
    def __init__(self, action, args=[], continuation=None, scope=None):
        self.action = action
        self.args = args
        self.continuation = continuation
        self.scope = scope

    def __str__(self):
        s_args = ""
        for a in self.args:
            s_args += str(a) + ' '
        if self.continuation:
            return f"{self.action} {s_args};\n{self.continuation}"
        else:
            return f"{self.action} {s_args};\n"

    def evaluate(self):
        if len(self.args) != self.action.arity:
            raise WrongArity(f"got {len(self.args)} argument(s) instead of {self.action.arity}")

        if self.continuation:
            self.action.function(*self.args)
            return self.continuation.evaluate()
        return self.action.function(*self.args)

    def setScope(self, scope):
        self.scope = scope
        if self.continuation:
            self.continuation.setScope(scope)

class Action:

    def __init__(self, name, function, arity, scope=None):
        self.function = function
        self.arity = arity
        self.scope = scope
        self.name = name
        if scope:
            self.scope.addFun(self)

    def evaluate(self):
        return self.function

class Function:
    def __init__(self, name, argsName, block, scope=None, continuation=None):

        self.name = name
        self.args = argsName
        self.scope = Scope(parent=scope)
        self.arity = len(self.args)
        self.continuation = continuation
        self.block = block
        self.block.scope = self.scope
        self.vars = []

        for arg in argsName:
            self.vars.append(Variable(arg, scope=self.scope))

        if scope:
            scope.addFun(self)

    def function(self, *args):
        for i, arg in enumerate(args):
            self.vars[i].assign(arg.evaluate())
        self.block.evaluate()

    def evaluate(self):
        return self.function

    def setScope(self, scope):
        self.scope = scope
        self.scope.addFun(self)
        self.block.setScope(Scope(parent=self.scope))


class Constante:
    def __init__(self, value=None, scope=None):
        self.value = value
        self.scope = scope

    def evaluate(self):
        return self.value

    def __str__(self):
        return f"{self.value}"

    def setScope(self, scope):
        self.scope = scope

class Variable:
    
    def __init__(self, name="", value=None, scope=None):
        self.value = value
        self.scope = scope
        self.name = name
        if scope:
            self.scope.addVar(self)

    def evaluate(self):
        return self.value

    def assign(self, newValue):
        self.value = newValue
        return self.value

    def __str__(self):
        return f"{self.name} = {self.value}"

    def setScope(self, scope):
        self.scope = scope
        1/0
        self.scope.addVar(self)

class Property(Variable):
    """
    Provides a way to interact with variables of the actual youtube_cli program
    """
    def __init__(self, name, object):
        Variable.__init__(self, name, None, globalScope)
        self.getter = lambda: getattr(object, name)
        self.setter = lambda v: setattr(object, name, v)

    def evaluate(self):
        return self.getter()

    def assign(self, newValue):
        self.setter(newValue)
        return newValue

    def __str__(self):
        return f"{self.name} = {self.getter()}"

    def setScope(self):
        pass


class Assignment:
    def __init__(self, targetName, command, continuation=None, scope=None):
        self.targetName = targetName
        self.command = command
        self.continuation = continuation
        self.scope = scope

    def __str__(self):
        return f"{self.target} := {self.command}"

    def evaluate(self):
        r = self.command.evaluate()
        self.target.assign(r)
        if self.continuation:
            return self.continuation.evaluate()
        return r

    def setScope(self, scope):
        self.scope = scope
        self.target = self.scope.findVar(self.targetName)
        self.continuation.setScope(scope)

class Block:
    def __init__(self, commands=[], continuation=None, scope=None):
        self.commands = commands
        self.continuation = continuation
        self.scope = scope

    def __str__(self):
        s = ""
        for c in self.commands:
            s += str(c)
        return "{\n" + s +"}\n"

    def evaluate(self):
        last_return = None
        for command in self.commands:
            command.scope = self.scope
            last_return = command.evaluate()

        if self.continuation:
            return self.continuation.evaluate()
        return last_return

    def setScope(self, scope):
        self.scope = scope
        for c in self.commands:
            c.setScope(scope)
        self.continuation.setScope(scope.parent)

class Conditional:
    def __init__(self, condition, if_block, else_block=None, scope=None, continuation=None):

        self.condition = condition
        self.if_block = if_block
        self.else_block = else_block

        self.scope = scope
        self.continuation = continuation

    def evaluate(self):
        if self.condition.evaluate():
            return self.if_block.evaluate()
        else:
            return self.else_block.evaluate()

    def setScope(self, scope):
        self.scope = scope
        self.if_block.setScope(Scope(parent=self.scope))
        if self.else_block:
            self.else_block.setScope(Scope(parent=self.scope))
        if self.continuation:
            self.continuation.setScope(scope)


class Loop:
    def __init__(self, condition, block, scope=None, continuation=None):
        
        self.condition = condition
        self.block = block
        self.scope = scope
        self.continuation = continuation

    def evaluate(self):
        while self.condition.evaluate():
            self.block.evaluate()

    def setScope(self, scope):
        self.scope = scope
        self.block.setScope(Scope(parent=self.scope))
        if self.continuation:
            self.continuation.setScope(scope)
