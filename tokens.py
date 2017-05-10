#!/usr/bin/env python3
from re import compile, MULTILINE


class Token:
    # Associate each token with a regular expression
    TYPE = {
        'COMMA': compile('^(,)'),
        'PERIOD': compile('^(\.)'),
        'Q_MARK': compile('^(\?)'),
        'LEFT_PAREN': compile('^(\()'),
        'RIGHT_PAREN': compile('^(\))'),
        'COLON': compile('^(:)[^-]?'),
        'COLON_DASH': compile('^(:-)'),
        'MULTIPLY': compile('^(\*)'),
        'ADD': compile('^(\+)'),
        'SCHEMES': compile('^(Schemes)(?:[^a-zA-z\d]|$)'),
        'FACTS': compile('^(Facts)(?:[^a-zA-z\d]|$)'),
        'RULES': compile('^(Rules)(?:[^a-zA-z\d]|$)'),
        'QUERIES': compile('^(Queries)(?:[^a-zA-z\d]|$)'),
        'ID': compile('^([a-zA-Z][a-zA-Z0-9]*)'),
        'STRING': compile("^(\'(?:(?:[^\']|\'\')*[^\'])?\')(?:[^\']|$)", MULTILINE),
        'COMMENT': compile('((?:^#$)|(?:^#[^|].*)|(?:^#\|(?:.|\n)*\|#))', MULTILINE),
        'WHITESPACE': compile('^(\s+)', MULTILINE),
        # This is a temporary token to make parsing easier
        'MULTILINE': compile('((?:^\'(?:[^\']|\'\')*$)|(?:^#\|[^|#]*$))', MULTILINE),
        'EOF': compile('\Z')
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
        if self.TYPE['EOF'].match(s_input):
            self.type = 'EOF'
        elif self.TYPE['STRING'].match(s_input):
            self.type = 'STRING'
            self.value = self.TYPE['STRING'].match(s_input).group(1)
        elif self.TYPE['COMMENT'].match(s_input):
            self.type = 'COMMENT'
            self.value = self.TYPE['COMMENT'].match(s_input).group(1)
        elif self.TYPE['MULTILINE'].match(s_input):
            self.type = 'MULTILINE'
        elif self.TYPE['WHITESPACE'].match(s_input):
            self.type = 'WHITESPACE'
            self.value = self.TYPE['WHITESPACE'].match(s_input).group(1)
        elif self.TYPE['SCHEMES'].match(s_input):
            self.type = 'SCHEMES'
            self.value = 'Schemes'
        elif self.TYPE['FACTS'].match(s_input):
            self.type = 'FACTS'
            self.value = 'Facts'
        elif self.TYPE['QUERIES'].match(s_input):
            self.type = 'QUERIES'
            self.value = 'Queries'
        elif self.TYPE['RULES'].match(s_input):
            self.type = 'RULES'
            self.value = 'Rules'
        elif self.TYPE['ID'].match(s_input):
            self.type = 'ID'
            self.value = self.TYPE['ID'].match(s_input).group(1)
        elif self.TYPE['COLON_DASH'].match(s_input):
            self.type = 'COLON_DASH'
            self.value = ':-'
        elif self.TYPE['COLON'].match(s_input):
            self.type = 'COLON'
            self.value = ':'
        elif self.TYPE['COMMA'].match(s_input):
            self.type = 'COMMA'
            self.value = ','
        elif self.TYPE['PERIOD'].match(s_input):
            self.type = 'PERIOD'
            self.value = '.'
        elif self.TYPE['Q_MARK'].match(s_input):
            self.type = 'Q_MARK'
            self.value = '?'
        elif self.TYPE['LEFT_PAREN'].match(s_input):
            self.type = 'LEFT_PAREN'
            self.value = '('
        elif self.TYPE['RIGHT_PAREN'].match(s_input):
            self.type = 'RIGHT_PAREN'
            self.value = ')'
        elif self.TYPE['ADD'].match(s_input):
            self.type = 'ADD'
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
