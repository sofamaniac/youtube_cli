"""File containing the grammar of the language

program     : commandlist                                   o
            | function                                      o
            | program program                               o

command     : ACTION                                        o
            | ACTION SPACE paramlist                        o
            | NAME ASSIGN param                             o
            | SET SPACE NAME SPACE param                    o
            | param                                         o
            | LET NAME ASSIGN param                         o
            | if                                            o
            | block                                         o
            | while                                         o
            | param BINOP param                             x

commandlist : command CSEP commandlist                      o
            | command NEWLINE commandlist                   o
            | command NEWLINE                               o
            | command                                       o

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

block       : BEGIN commandlist END                         o

if          : IF LPAREN command RPAREN block ELSE block     o
            | IF LPAREN command RPAREN block                o

while       : WHILE LPAREN command RPAREN block             o

function    : FUN NAME arglist BEGIN program END            o

arglist     : NAME SPACE NAME                               o
            | NAME                                          o

Remarks: SET needs cannot be a function since it does not
its parameter must not be passed by name
"""

from ply.yacc import yacc
import logging
from parser import lex
from parser import datastructures
from parser.datastructures import *
from parser import lex
from parser import primitives

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
    function : FUN NAME arglist block
    """
    p[0] = FunctionDecleration(p[2], p[3], p[4])


def p_block(p):
    """
    block : BEGIN commandlist END
    """
    p[0] = CodeBlock(p[2])


def p_if_else(p):
    """
    if : IF LPAREN command RPAREN block ELSE block
       | IF LPAREN command RPAREN block
    """
    if len(p) < 8:
        else_block = None
    else:
        else_block = p[7]
    p[0] = IfElse(p[3], p[5], else_block)


def p_while(p):
    """
    while : WHILE LPAREN command RPAREN block
    """
    p[0] = While(p[3], p[5])


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


def p_command_param(p):
    """
    command : param
    """
    p[0] = p[1]


def p_command_if(p):
    """
    command : if
    """
    p[0] = p[1]


def p_command_while(p):
    """
    command : while
    """
    p[0] = p[1]


def p_command_block(p):
    """
    command : block
    """
    p[0] = p[1]


def p_command_list(p):
    """
    commandlist : command CSEP commandlist
                | command NEWLINE commandlist
                | command NEWLINE
                | command
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
