import ply.lex as lex

tokens = (
    'STATE',
    'MOVE',
    'LETTER',
    'COMMA',
    'PIPE',
    'START',
    'END',
    'UNDEFINED',
    'STRING',
    'NEW',
    'INT',
    'FROM'
)

t_COMMA = r','
t_PIPE = r'\|'


def t_STRING(t):
    r'"[^"]*"'
    t.value = t.value[1:-1]
    return t


def t_INT(t):
    r'[1-9][0-9]*'
    t.value = int(t.value)
    return t


def t_START(t):
    r'START'
    return t


t_END = r'END'
t_UNDEFINED = r'UNDEFINED'
t_NEW = r'NEW'
t_FROM = r'FROM'


def t_STATE(t):
    r'@\w+'
    t.value = t.value[1:]
    return t


def t_MOVE(t):
    r'L|S|R'
    t.value = {'L': -1, 'S': 0, 'R': 1}[t.value]
    return t


def t_LETTER(t):
    r"'[^ ]"
    t.value = t.value[1:]
    return t


# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


# A string containing ignored characters (spaces and tabs)
t_ignore = ' \t'


def t_ignore_comment(t):
    r'\#[^\n]*'


# Error handling rule
def t_error(t):
    print("Illegal character '%s' at line %d" % (t.value[0], lexer.lineno))
    t.lexer.skip(1)


# Build the lexer
lexer = lex.lex()


def test(s):
    lexer.input(s)
    for tok in lexer: print(tok)
