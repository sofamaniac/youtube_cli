import ply.lex as lex
import logging
from parser import datastructures
from parser.datastructures import functions_list

log = logging.getLogger(__name__)

reserved = {
    "if": "IF",
    "else": "ELSE",
    "let": "LET",
    "true": "TRUE",
    "false": "FALSE",
    "fun": "FUN",
    "while": "WHILE",
    "set": "SET",
}
tokens = list(reserved.values()) + [
    "NAME",
    "INT",
    "STRING",
    "ACTION",
    "CSEP",
    "SPACE",
    "COMMENT",
    "BEGIN",
    "END",
    "LPAREN",
    "RPAREN",
    "ASSIGN",
    "NEWLINE",
    # operators
    "PLUS",
    "MINUS",
    "TIMES",
    "DIVIDE",
    "MOD",
    "OR",
    "AND",
    "NOT",
    "XOR",
    "LT",
    "LE",
    "GT",
    "GE",
    "EQ",
    "NE",
    "LOR",
    "LAND",
    "LNOT",
    "LSHIFT",
    "RSHIFT",
]
t_PLUS = r"[ ]*\+[ ]*"
t_MINUS = r"[ ]*-[ ]*"
t_TIMES = r"[ ]*\*[ ]*"
t_DIVIDE = r"[ ]*/[ ]*"
t_MOD = r"[ ]*%[ ]*"
t_OR = r"[ ]*\|\|[ ]*"
t_AND = r"[ ]*&&[ ]*"
t_NOT = r"[ ]*![ ]*"
t_LE = r"[ ]*<=[ ]*"
t_GE = r"[ ]*>=[ ]*"
t_GT = r"[ ]*>[ ]*"
t_EQ = r"[ ]*==[ ]*"
t_NE = r"[ ]*!=[ ]*"

t_ignore = "\t"  # Ignored chars

t_NAME = r"[a-zA-Z_][a-zA-Z0-9_]*"
t_STRING = r"\"([^\\\n]|(\\.))*?\""
t_CSEP = r"[ ]*;[ ]*"
t_SPACE = r"[ ]+"
t_ASSIGN = r"[ ]*=[ ]*"
t_BEGIN = r"[ ]*\{[ ]*"
t_END = r"[ ]*\}[ ]*"
t_LPAREN = r"[ ]*\([ ]*"
t_RPAREN = r"[ ]*\)[ ]*"


def t_INT(t):
    r"\d+"
    t.value = int(t.value)
    return t


def t_NEWLINE(t):
    r"\n+"
    t.lexer.lineno += t.value.count("\n")
    return t


def t_ACTION(t):
    r"[a-zA-Z_]+"
    for r in reserved:
        if t.value == r:
            t.type = reserved[r]
            return t
    if functions_list.find_property(t.value):
        t.type = "ACTION"
    else:
        t.type = "NAME"
    return t


def t_COMMENT(t):
    r"\#(.)*?\n"
    t.lexer.lineno += 1


def t_error(t):
    print(f"Illegal character {t.value[0]!r}")
    t.lexer.skip(1)
    return t


lexer = lex.lex(debug=True, debuglog=log)
