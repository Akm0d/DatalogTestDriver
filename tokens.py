#!/usr/bin/env python3
import re

# For accessing a token tuple
TYPE        = 0
VALUE       = 1
LINE        = 2

# Token strings
COMMA       = 'COMMA'
PERIOD      = 'PERIOD'
Q_MARK      = 'Q_MARK'
LEFT_PAREN  = 'LEFT_PAREN'
RIGHT_PAREN = 'RIGHT_PAREN'
COLON       = 'COLON'
COLON_DASH  = 'COLON_DASH'
MULTIPLY    = 'MULTIPLY'
ADD         = 'ADD'
SCHEMES     = 'SCHEMES'
FACTS       = 'FACTS'
RULES       = 'RULES'
QUERIES     = 'QUERIES'
ID          = 'ID'
STRING      = 'STRING'
COMMENT     = 'COMMENT'
WHITESPACE  = 'WHITESPACE'
MULTILINE   = 'MULTILINE'
INVALID     = 'INVLAID'
UNDEFINED   = 'UNDEFINED'
EOF         = 'EOF'


class TokenError(Exception):
    def __init__(self, token):
        assert isinstance(token, tuple)
        print("Failure!")
        print('  (%s,"%s",%s)' % token)


class Token:

    # Associate each token with a regular expression
    TYPE = {
        COMMA: re.compile('^(,)'),
        PERIOD: re.compile('^(\.)'),
        Q_MARK: re.compile('^(\?)'),
        LEFT_PAREN: re.compile('^(\()'),
        RIGHT_PAREN: re.compile('^(\))'),
        COLON: re.compile('^(:)[^-]?'),
        COLON_DASH: re.compile('^(:-)'),
        MULTIPLY: re.compile('^(\*)'),
        ADD: re.compile('^(\+)'),
        SCHEMES: re.compile('^(Schemes)(?:[^a-zA-z\d]|$)'),
        FACTS: re.compile('^(Facts)(?:[^a-zA-z\d]|$)'),
        RULES: re.compile('^(Rules)(?:[^a-zA-z\d]|$)'),
        QUERIES: re.compile('^(Queries)(?:[^a-zA-z\d]|$)'),
        ID: re.compile('^([a-zA-Z][a-zA-Z0-9]*)'),
        STRING: re.compile("^(\'(?:\'\'|[^\'])+\')", re.MULTILINE),
        COMMENT: re.compile('((?:^#[^|][^\n]*)|(?:^#\|(?:))[^(?:#|)]*\|#)', re.MULTILINE),
        WHITESPACE: re.compile('^(\s+)', re.MULTILINE),
        # This is a temporary token to make parsing easier
        EOF: re.compile('\Z')
    }
    type = 'UNDEFINED'
    value = None
    line_number = None

    def __init__(self, s_input, line_number=None):
        """
        Choose the token that best matches the input using a certain priority
        :param s_input: 
        :param line_number: 
        """
        self.value = s_input
        self.line_number = line_number
        if self.TYPE[EOF].match(s_input):
            self.type = EOF
        elif self.TYPE[STRING].match(s_input):
            self.type = STRING
            self.value = self.TYPE[STRING].match(s_input).group(1)
        elif self.TYPE[COMMENT].match(s_input):
            self.type = COMMENT
            self.value = self.TYPE[COMMENT].match(s_input).group(1)
        elif self.TYPE[WHITESPACE].match(s_input):
            self.type = WHITESPACE
            self.value = self.TYPE[WHITESPACE].match(s_input).group(1)
        elif self.TYPE[SCHEMES].match(s_input):
            self.type = SCHEMES
            self.value = 'Schemes'
        elif self.TYPE[FACTS].match(s_input):
            self.type = FACTS
            self.value = 'Facts'
        elif self.TYPE[QUERIES].match(s_input):
            self.type = QUERIES
            self.value = 'Queries'
        elif self.TYPE[RULES].match(s_input):
            self.type = RULES
            self.value = 'Rules'
        elif self.TYPE[ID].match(s_input):
            self.type = ID
            self.value = self.TYPE[ID].match(s_input).group(1)
        elif self.TYPE[COLON_DASH].match(s_input):
            self.type = COLON_DASH
            self.value = ':-'
        elif self.TYPE[COLON].match(s_input):
            self.type = COLON
            self.value = ':'
        elif self.TYPE[COMMA].match(s_input):
            self.type = COMMA
            self.value = ','
        elif self.TYPE[PERIOD].match(s_input):
            self.type = PERIOD
            self.value = '.'
        elif self.TYPE[Q_MARK].match(s_input):
            self.type = Q_MARK
            self.value = '?'
        elif self.TYPE[LEFT_PAREN].match(s_input):
            self.type = LEFT_PAREN
            self.value = '('
        elif self.TYPE[RIGHT_PAREN].match(s_input):
            self.type = RIGHT_PAREN
            self.value = ')'
        elif self.TYPE[ADD].match(s_input):
            self.type = ADD
            self.value = '+'
        elif self.TYPE['MULTIPLY'].match(s_input):
            self.type = 'MULTIPLY'
            self.value = '*'
        else:
            self.type = 'INVALID'
        pass

if __name__ == "__main__":
    from argparse import ArgumentParser
    arg = ArgumentParser(description="Pass in strings on the command line to test their interpretation")
    arg.add_argument("tokens", nargs='+')
    arg.add_argument('-d', '--debug', action='store_true', default=False)
    args = arg.parse_args()

    debug = args.debug
    tokens = args.tokens
    if debug: print("Parsing tokens: %s" % str(tokens))

    line = 0
    for token in tokens:
        full_token = Token(token, line)
        print("\nValue: %s" % full_token.value)
        print("Type: %s" % full_token.type)
        print("Line: %s" % str(full_token.line_number))
        line += 1
    pass
