"""
The language used by youtube_cli

program     : commandlist
            | function
            | program program
            | if

command     : ACTION
            | ACTION SPACE paramlist
            | NAME ASSIGN param
            | param
            | LET NAME ASSIGN param
            
            TODO
            | LPAREN command RPAREN
            | param BINOP param


commandlist : command CSEP command
            | command NEWLINE

constant    : STRING
            | INT
            | bool

param       : NAME
            | ACTION
            | LPAREN command RPAREN
            | constant

bool        : TRUE
            | FALSE

paramlist   : param SPACE paramlist
            | param

block       : BEGIN commandlist END

if          : IF LPAREN command RPAREN block ELSE block

function    : FUN NAME arglist BEGIN program END

arglist     : NAME SPACE NAME
            | NAME
"""

from ply.yacc import yacc
from parser import lex
from parser.datastructures import *

tokens = lex.tokens


def p_program_base(p):
    """
    program : commandlist
            | function
            | if
    """
    p[0] = p[1]


def p_program_rec(p):
    """
    program : program program
    """
    p[1].continuation = p[2]
    p[0] = p[1]


def p_commad_list(p):
    """
    commandlist : command CSEP commandlist
                | command NEWLINE
    """
    continuation = None if len(p) < 4 else p[3]
    p[1].continuation = continuation
    p[0] = p[1]


def p_command_action_param(p):
    """
    command : ACTION SPACE paramlist
            | ACTION
    """
    args = [] if len(p) < 4 else p[3]
    p[0] = Command(globalScope.findFun(p[1]), args=args, scope=None)


def p_command_param(p):
    """
    command : param
    """
    p[0] = p[1]


def p_command_declaration(p):
    """
    command : LET NAME ASSIGN param
    """
    Variable(p[2], None, scope=None)
    p[0] = Assignment(p[2], command=p[4])


def p_command_assign(p):
    """
    command : NAME ASSIGN param
    """
    p[0] = Assignment(p[1], command=p[3])


def p_paramlist_rec(p):
    """
    paramlist : param SPACE paramlist
    """
    p[0] = p[3]
    p[0].insert(0, p[1])


def p_paramlist_base(p):
    """
    paramlist : param
    """
    p[0] = [p[1]]


def p_param_string_bool(p):
    """
    param : STRING
          | bool
    """
    p[0] = Constante(p[1], None)


def p_param_int(p):
    """
    param : INT
    """
    p[0] = Constante(int(p[1]), None)


def p_param_var(p):
    """
    param : NAME
    """
    p[0] = currentScope.findVar(p[1])


def p_param_action(p):
    """
    param : ACTION
    """
    p[0] = globalScope.findFun(p[1])


def p_param_command_list(p):
    """
    param : LPAREN command RPAREN
    """
    p[0] = p[2]


def p_bool(p):
    """
    bool : TRUE
         | FALSE
    """
    p[0] = Constante(p[1] == "true", None)


def p_block(p):
    """
    block : BEGIN commandlist END
    """
    p[0] = p[2]


def p_function(p):
    """
    function : FUN NAME arglist BEGIN program END
    """
    p[0] = Function(p[2], p[3], p[5], scope=globalScope)


def p_arglist(p):
    """
    arglist : NAME arglist
            | NAME
    """
    p[2].insert(0, p[1])
    p[0] = p[2]


def p_if(p):
    """
    if : IF LPAREN command RPAREN block ELSE block
    """
    p[0] = Conditional(p[3], p[5], p[7], scope=None)


def p_while(p):
    """
    while : WHILE LPAREN command RPAREN block
    """
    p[0] = Loop(p[3], p[5], scope=None)


def p_error(p):
    print(p)
    print(f"Syntax error at {p.value!r}")


from logger import log

_parser = yacc(debug=log)


def parse(command):
    p = _parser.parse(command + "\n")
    return p


def evaluate(command):
    command = parse(command)
    command.setScope(globalScope)
    command.evaluate()
