import ply.lex as lex
from parser.primitives import getScope

reserved = {
        'if'    : 'IF',
        'else'  : 'ELSE',
        '{'     : 'BEGIN',
        '}'     : 'END',
        'let'   : 'LET',
        'true'  : 'TRUE',
        'false' : 'FALSE',
        'fun'   : 'FUN',
        }
tokens = list(reserved.values()) + [
        'NAME', 'INT', 'STRING', 'ACTION', 
        'CSEP', 'SPACE', 'COMMENT',
        'LPAREN', 'RPAREN', 'ASSIGN', 'NEWLINE',
        
        # operators
        'PLUS', 'MINUS', 'TIMES', 'DIVID', 'MOD',
        'OR', 'AND', 'NOT', 'XOR',
        'LT', 'LE', 'GT', 'GE', 'EQ', 'NE',
        'LOR', 'LAND', 'LNOT', 'LSHIFT', 'RSHIFT',
        ]

t_ignore = '\t'  # Ignored chars

t_NAME = r'[a-zA-Z_][a-zA-Z0-9_]*'
t_STRING =  r'\"([^\\\n]|(\\.))*?\"'
t_CSEP = r'[ ]*;[ ]*'
t_SPACE = r'[ ]+'
t_ASSIGN = r'[ ]*=[ ]*'

def t_INT(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")
    return t

def t_ACTION(t):
    r'[a-zA-Z_]+'
    if getScope().containsFun(t.value):
        t.type = "ACTION"
    else:
        for r in reserved:
            if t.value == r:
                t.type = reserved[r]
                return t
        t.type = "NAME"
    return t

def t_COMMENT(t):
    r'\#(.)*?\n'
    t.lexer.lineno += 1

def t_error(t):
    print(f"Illegal character {t.value[0]!r}")
    t.lexer.skip(1)
    return t

from logger import log
lexer = lex.lex(debug=True, debuglog=log)
