from parser.datastructures import Scope, Action, Variable, Property
import youtube

def remap(keys, action):
    print(f"remapping {keys} to {action}")

globalScope = Scope(None)
Action('remap', remap, 2, globalScope)

currentScope = globalScope
def getScope():
    return currentScope

def init(app):
    Property("volume", app, globalScope)
    Property("muted", app, globalScope)
    Property("useSponsorBlock", youtube, globalScope)

import parser.parser as parser
def evaluate(command):
    parser.evaluate(command)

