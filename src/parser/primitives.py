from parser.datastructures import Scope, Action, Variable, Property
#import youtube

def remap(keys, action):
    print(f"remapping {keys} to {action}")

globalScope = Scope(None)
Action('remap', remap, 2, globalScope)

currentScope = globalScope
def getScope():
    return currentScope

from parser.parser import parse
def init(app):
    Property("volume", app, globalScope)
    Property("muted", app, globalScope)

