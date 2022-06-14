"""File containing the grammar of the language

program     : commandlist                                   o
            | function                                      o
            | program program                               o

command     : ACTION                                        o
            | ACTION SPACE paramlist                        o
            | NAME ASSIGN param                             o
            | SET SPACE NAME SPACE param
            | param
            | LET NAME ASSIGN param                         o
            | LPAREN command RPAREN
            | param BINOP param
            | if
            | block

commandlist : command CSEP commandlist                      o
            | command NEWLINE commandlist                   o
            | command NEWLINE                               o

constant    : STRING                                        o
            | INT                                           o
            | bool                                          o

param       : NAME                                          o
            | LPAREN command RPAREN                         o
            | constant                                      o

bool        : TRUE                                          o
            | FALSE                                         o

paramlist   : param SPACE paramlist                         o
            | param                                         o

block       : BEGIN commandlist END

if          : IF LPAREN command RPAREN block ELSE block

function    : FUN NAME arglist BEGIN program END            o

arglist     : NAME SPACE NAME                               o
            | NAME                                          o
"""

from ply.yacc import yacc
import logging
from parser import lex
from parser import datastructures
from parser.datastructures import *
from parser import lex

tokens = lex.tokens

log = logging.getLogger(__name__)

# in order to compile the parser properly,
# the program token must be the first
def p_program_commands(p):
    """
    program : commandlist
    """
    p[0] = Program(p[1])


def p_program_function(p):
    """
    program : function
    """
    p[0] = Program([p[1]])


def p_program_rec(p):
    """
    program : program program
    """
    p[0] = Program(p[1].commands + p[2].commands)


def p_constant_str(p):
    """
    constant : STRING
    """
    p[0] = Constant(str(p[1]))


def p_constant_int(p):
    """
    constant : INT
    """
    p[0] = Constant(int(p[1]))


def p_constant_bool(p):
    """
    constant : bool
    """
    p[0] = Constant(p[1])


def p_bool_true(p):
    """
    bool : TRUE
    """
    p[0] = True


def p_bool_false(p):
    """
    bool : FALSE
    """
    p[0] = False


def p_param_var(p):
    """
    param : NAME
    """
    p[0] = VariableRead(p[1])


def p_param_command(p):
    """
    param : constant
          | LPAREN command RPAREN
    """
    if len(p) < 3:
        p[0] = p[1]
    else:
        p[0] = p[2]


def p_arglist(p):
    """
    arglist : NAME SPACE arglist
            | NAME
    """
    if len(p) < 3:
        p[0] = [p[1]]
    else:
        p[0] = [p[1], *p[3]]


def p_param_list(p):
    """
    paramlist : param SPACE paramlist
              | param
    """
    if len(p) < 3:
        p[0] = [p[1]]
    else:
        p[0] = [p[1], *p[3]]


def p_function_decl(p):
    """
    function : FUN NAME arglist BEGIN program END
    """
    p[0] = FunctionDecleration(p[2], p[3], p[5])


def p_command_decl(p):
    """
    command : LET NAME ASSIGN param
    """
    p[0] = VariableDecleration(p[2], p[4])


def p_command_assign(p):
    """
    command : NAME ASSIGN param
    """
    p[0] = VariableAssignment(p[1], p[3])


def p_command_set(p):
    """
    command : SET SPACE NAME SPACE param
    """
    p[0] = VariableAssignment(p[3], p[5])


def p_command_action(p):
    """
    command : ACTION
            | ACTION SPACE paramlist
    """
    if len(p) < 3:
        p[0] = FunctionCall(p[1])
    else:
        p[0] = FunctionCall(p[1], p[3])


def p_command_list(p):
    """
    commandlist : command CSEP commandlist
                | command NEWLINE commandlist
                | command NEWLINE
    """
    if len(p) < 4:
        p[0] = [p[1]]
    else:
        p[0] = [p[1], *p[3]]


def p_error(p):
    log.warning(p)
    log.warning(f"Syntax error at {p.value!r}")


_parser = yacc(debug=log)


def parse(command):
    p = _parser.parse(command + "\n")
    return p


def evaluate(command):
    command = parse(command)
    if command:
        command.set_scope(global_properties)
        command.execute()
