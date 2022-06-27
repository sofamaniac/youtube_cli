"""File containing the grammar of the language

program     : commandlist
            | function
            | program program

command     : ACTION
            | ACTION SPACE paramlist
            | var ASSIGN param
            | SET SPACE NAME SPACE param
            | param
            | LET NAME ASSIGN param
            | if
            | block
            | while
            | param binop param
            | MINUS param

commandlist : command CSEP commandlist
            | command NEWLINE commandlist
            | command NEWLINE
            | command

constant    : STRING
            | INT
            | bool

param       : var
            | LPAREN command RPAREN
            | constant

var         : NAME
            | NAME DOT var

bool        : TRUE
            | FALSE

paramlist   : param SPACE paramlist
            | param

block       : BEGIN commandlist END

if          : IF LPAREN command RPAREN block ELSE block
            | IF LPAREN command RPAREN block

while       : WHILE LPAREN command RPAREN block

function    : FUN NAME arglist BEGIN program END

arglist     : NAME SPACE NAME
            | NAME

binop       : a whole bunch of things

Remarks: SET cannot be a function since it does not
its parameter must not be passed by name
"""

from ply.yacc import yacc
import logging
from parser import lex
from parser import datastructures
from parser.datastructures import *
from parser import lex
from parser import primitives
import operator as op

tokens = lex.tokens

log = logging.getLogger(__name__)

# defining precedence of operators
# from lowest to highest
# (inspired by C precedence and associativity)
precedence = (
    ("right", "ASSIGN"),
    ("left", "EQ", "NE"),
    ("left", "PLUS", "MINUS"),
    ("left", "TIMES", "DIVIDE"),
    ("left", "LPAREN", "RPAREN"),
    ("left", "DOT"),
)

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


def p_unit(p):
    """
    unit : LPAREN RPAREN
    """
    p[0] = []


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


def p_param_l_value(p):
    """
    param : constant
          | LPAREN l_val RPAREN
          | var
    """
    if len(p) < 3:
        p[0] = p[1]
    else:
        p[0] = p[2]


def p_arglist(p):
    """
    arglist : NAME arglist
            | NAME
    """
    if len(p) < 3:
        p[0] = [p[1]]
    else:
        p[0] = [p[1], *p[3]]


def p_param_list(p):
    """
    paramlist : param paramlist
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


def p_begin(p):
    """
    begin : BEGIN NEWLINE
          | NEWLINE begin
    """
    p[0] = p[1]


def p_end(p):
    """
    end : END NEWLINE
        | NEWLINE end
    """
    p[0] = p[1]


def p_block(p):
    """
    block : begin commandlist end
    """
    p[0] = CodeBlock(p[2])


def p_if_else(p):
    """
    if : IF LPAREN l_val RPAREN block ELSE block
       | IF LPAREN l_val RPAREN block
    """
    if len(p) < 8:
        else_block = None
    else:
        else_block = p[7]
    p[0] = IfElse(p[3], p[5], else_block)


def p_while(p):
    """
    while : WHILE LPAREN l_val RPAREN block
    """
    p[0] = While(p[3], p[5])


def p_var_decl(p):
    """
    var_decl : LET NAME ASSIGN param
    """
    p[0] = VariableDecleration(p[2], p[4])


def p_var_assign(p):
    """
    var_access : var ASSIGN l_val
    """
    p[1].mode = WRITE
    p[1].value = p[3]
    p[0] = p[1]


def p_var_set(p):
    """
    var_access : SET var param
    """
    p[2].mode = WRITE
    p[2].value = p[3]
    p[0] = p[2]


def p_l_value(p):
    """
    l_val : param
          | var_access
    """
    p[0] = p[1]


def p_l_value_action(p):
    """
    l_val : ACTION unit
          | ACTION paramlist
    """
    p[0] = FunctionCall(p[1], p[2])


def p_l_value_binop(p):
    """
    l_val : l_val binop l_val
    """
    p[2].x = p[1]
    p[2].y = p[3]
    p[0] = p[2]


def p_l_value_uminus(p):
    """
    l_val : MINUS param
    """
    p[1].x = 0
    p[1].y = p[2]
    p[0] = p[1]


def p_command(p):
    """
    command : l_val
            | var_decl
            | if
            | while
            | block
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


def p_var_name(p):
    """
    var : NAME
    """
    p[0] = Variable(p[1])


def p_var_attr(p):
    """
    var : NAME DOT var
    """
    p[0] = Attribute(p[1], p[3])


def p_binop_plus(p):
    """
    binop : PLUS
    """
    p[0] = BinaryOp(op.add)


def p_binop_minus(p):
    """
    binop : MINUS
    """
    p[0] = BinaryOp(op.sub)


def p_binop_times(p):
    """
    binop : TIMES
    """
    p[0] = BinaryOp(op.mul)


def p_binop_divide(p):
    """
    binop : DIVIDE
    """
    p[0] = BinaryOp(op.floordiv)


def p_binop_mod(p):
    """
    binop : MOD
    """
    p[0] = BinaryOp(op.mod)


def p_binop_lt(p):
    """
    binop : LT
    """
    p[0] = BinaryOp(op.lt)


def p_binop_le(p):
    """
    binop : LE
    """
    p[0] = BinaryOp(op.le)


def p_binop_gt(p):
    """
    binop : GT
    """
    p[0] = BinaryOp(op.gt)


def p_binop_ge(p):
    """
    binop : GE
    """
    p[0] = BinaryOp(op.ge)


def p_binop_and(p):
    """
    binop : AND
    """
    p[0] = BinaryOp(op.and_)


def p_binop_or(p):
    """
    binop : OR
    """
    p[0] = BinaryOp(op.or_)


def p_binop_not(p):
    """
    binop : NOT
    """
    p[0] = BinaryOp(op.not_)


def p_binop_eq(p):
    """
    binop : EQ
    """
    p[0] = BinaryOp(op.eq)


def p_binop(p):
    """
    binop : NE
    """
    p[0] = BinaryOp(op.ne)


def p_error(p):
    log.warning(p)
    log.warning(f"Syntax error at {p.value!r}")


_parser = yacc(debug=log)


def parse(command):
    p = _parser.parse(command + "\n")
    return p


def evaluate(command):
    if not command:
        # handles an empty program
        return
    command = parse(command)
    log.debug(str(command))
    if command:
        command.set_scope(global_properties)
        command.execute()
