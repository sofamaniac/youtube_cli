"""
The language used by youtube_cli

program     : commandlist
            | function
            | program program

command     : ACTION
            | ACTION SPACE paramlist
            | NAME ASSIGN param
            | param

commandlist : command CSEP command
            | command NEWLINE

param       : NAME
            | STRING
            | INT
            | ACTION
            | LPAREN commandlist RPAREN

paramlist   : param SPACE paramlist
            | param

block       : BEGIN commandlist END

if          : IF LPAREN command RPAREN block ELSE block

function    : FUN NAME arglist BEGIN program END

arglist     : NAME SPACE NAME
            | NAME
"""

from ply.yacc import yacc
import parser.lex as lex
from parser.datastructures import *
from parser.primitives import globalScope

tokens = lex.tokens
currentScope = globalScope

def p_program(p):
    '''
    program : commandlist
            | function
            | program program
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[1]
        p[0].continuation = p[2]

def p_commad_list(p):
    '''
    commandlist : command CSEP commandlist
                | command NEWLINE
    '''
    continuation = None if len(p) < 4 else p[3]
    p[1].continuation = continuation
    p[0] = p[1]

def p_command_action_param(p):
    '''
    command : ACTION SPACE paramlist
            | ACTION
    '''
    args = [] if len(p) < 4 else p[3]
    p[0] = Command(currentScope.findFun(p[1]), args=args, scope=currentScope)

def p_command_param(p):
    '''
    command : param
    '''
    p[0] = p[1]

def p_command_assign(p):
    '''
    command : NAME ASSIGN param
    '''
    p[0] = Assignment(currentScope.findVar(p[1]), command=p[3])

def p_paramlist_rec(p):
    '''
    paramlist : param SPACE paramlist
    '''
    p[0] = p[3]
    p[0].insert(0, p[1])   

def p_paramlist_base(p):
    '''
    paramlist : param
    '''
    p[0] = [p[1]]

def p_param_string(p):
    '''
    param : STRING
    '''
    p[0] = Constante(p[1], currentScope)

def p_param_int(p):
    '''
    param : INT
    '''
    p[0] = Constante(p[1], currentScope)

def p_param_var(p):
    '''
    param : NAME
    '''
    p[0] = currentScope.findVar(p[1])

def p_param_action(p):
    '''
    param : ACTION
    '''
    p[0] = currentScope.findFun(p[1])

def p_param_command_list(p):
    '''
    param : LPAREN commandlist RPAREN
    '''
    p[0] = p[2]

def p_block(p):
    '''
    block : BEGIN commandlist END
    '''
    p[0] = p[2]

def p_function(p):
    '''
    function : FUN NAME arglist BEGIN program END
    '''
    pass

def p_arglist(p):
    '''
    arglist : NAME arglist
            | NAME
    '''
    pass

def p_error(p):
    print(p)
    print(f'Syntax error at {p.value!r}')

parser = yacc(debug=True)

def parse(command):
    p = parser.parse(command+'\n')
    return p

def evaluate(command):
    parse(command).evaluate()
