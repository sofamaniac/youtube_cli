from datastructures import Scope, Action, Variable, Property
#import youtube

def set(target, value):
    with open('debug', 'w') as f:
        print(target, value, file=f)
    target.assign(value)

def remap(keys, action):
    print(f"remapping {keys} to {action}")

globalScope = Scope(None)
Action('remap', remap, 2, globalScope)

currentScope = globalScope
def getScope():
    return currentScope

from parser import parse
def init(app):
    Property("volume", lambda : getattr(app, "volume"), lambda v : setattr(app, "volume", v), globalScope)
    Property("muted", lambda : getattr(app, "muted"), lambda v : setattr(app, "muted", v), globalScope)

