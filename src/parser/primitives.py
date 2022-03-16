from parser.datastructures import Scope, Action, Variable, Property, globalScope
from parser import parser
import youtube

def remap(keys, action):
    print(f"remapping {keys} to {action}")

Action('remap', remap, 2, globalScope)

def init(app):
    Property("volume", app)
    Property("muted", app)
    Property("useSponsorBlock", youtube)

def evaluate(command):
    parser.evaluate(command)

