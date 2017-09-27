#!/usr/bin/env python3
import logging
import re

from enum import Enum

logger = logging.getLogger(__name__)


class TokenError(Exception):
    """Token Error occurred"""


class TokenType(Enum):
    # Associate each token with a regular expression
    COMMA = re.compile('^(,)')
    PERIOD = re.compile('^(\.)')
    Q_MARK = re.compile('^(\?)')
    LEFT_PAREN = re.compile('^(\()')
    RIGHT_PAREN = re.compile('^(\))')
    COLON = re.compile('^(:)[^-]?')
    COLON_DASH = re.compile('^(:-)')
    MULTIPLY = re.compile('^(\*)')
    ADD = re.compile('^(\+)')
    SCHEMES = re.compile('^(Schemes)(?:[^a-zA-z\d]|$)')
    FACTS = re.compile('^(Facts)(?:[^a-zA-z\d]|$)')
    RULES = re.compile('^(Rules)(?:[^a-zA-z\d]|$)')
    QUERIES = re.compile('^(Queries)(?:[^a-zA-z\d]|$)')
    ID = re.compile('^([a-zA-Z][a-zA-Z0-9]*)')
    STRING = re.compile("^(\'(?:\'\'|[^\'])+\'|\'\')", re.MULTILINE)
    COMMENT = re.compile('((?:^#[^|][^\n]*)|(?:^#\|(?:.|\n)*?\|#))', re.MULTILINE)
    WHITESPACE = re.compile('^(\s+)', re.MULTILINE)
    UNDEFINED = re.compile('((?:^#\|(?:.|\n)*?\Z)|(?:^\'(?:\'\'|[^\'])+\Z))', re.MULTILINE)
    INVALID = re.compile('')
    # This is a temporary token to make parsing easier
    EOF = re.compile('\Z')

    def match(self, string) -> bool:
        match = self.value.match(string)
        logger.debug("'{}' {} {}".format(string, "matched" if match else "did not match", self.name))
        return match

    def __str__(self) -> str:
        return self.name


class Token:
    def __init__(self, line_number: int, s_input: str = "", value: str = None, t_type: TokenType = None):
        """
        Choose the token that best matches the input using a certain priority
        :param s_input: 
        """
        self.line_number = line_number
        if value is not None and t_type is not None:
            self.value = value
            self.type = t_type
        elif TokenType.EOF.match(s_input):
            self.type = TokenType.EOF
            self.value = ""
        elif TokenType.COMMENT.match(s_input):
            self.type = TokenType.COMMENT
            self.value = TokenType.COMMENT.match(s_input).group(1)
        elif TokenType.UNDEFINED.match(s_input):
            self.type = TokenType.UNDEFINED
            self.value = TokenType.UNDEFINED.match(s_input).group(1)
        elif TokenType.STRING.match(s_input):
            self.type = TokenType.STRING
            self.value = TokenType.STRING.match(s_input).group(1)
        elif TokenType.WHITESPACE.match(s_input):
            self.type = TokenType.WHITESPACE
            self.value = TokenType.WHITESPACE.match(s_input).group(1)
        elif TokenType.SCHEMES.match(s_input):
            self.type = TokenType.SCHEMES
            self.value = 'Schemes'
        elif TokenType.FACTS.match(s_input):
            self.type = TokenType.FACTS
            self.value = 'Facts'
        elif TokenType.QUERIES.match(s_input):
            self.type = TokenType.QUERIES
            self.value = 'Queries'
        elif TokenType.RULES.match(s_input):
            self.type = TokenType.RULES
            self.value = 'Rules'
        elif TokenType.ID.match(s_input):
            self.type = TokenType.ID
            self.value = TokenType.ID.match(s_input).group(1)
        elif TokenType.COLON_DASH.match(s_input):
            self.type = TokenType.COLON_DASH
            self.value = ':-'
        elif TokenType.COLON.match(s_input):
            self.type = TokenType.COLON
            self.value = ':'
        elif TokenType.COMMA.match(s_input):
            self.type = TokenType.COMMA
            self.value = ','
        elif TokenType.PERIOD.match(s_input):
            self.type = TokenType.PERIOD
            self.value = '.'
        elif TokenType.Q_MARK.match(s_input):
            self.type = TokenType.Q_MARK
            self.value = '?'
        elif TokenType.LEFT_PAREN.match(s_input):
            self.type = TokenType.LEFT_PAREN
            self.value = '('
        elif TokenType.RIGHT_PAREN.match(s_input):
            self.type = TokenType.RIGHT_PAREN
            self.value = ')'
        elif TokenType.ADD.match(s_input):
            self.type = TokenType.ADD
            self.value = '+'
        elif TokenType.MULTIPLY.match(s_input):
            self.type = TokenType.MULTIPLY
            self.value = '*'
        else:
            self.type = TokenType.INVALID
            self.value = s_input[0]
        logger.debug("Created token: {}".format(self).replace('\n', '\\n'))

    def __str__(self) -> str:
        return '({},"{}",{})'.format(
            self.type,
            self.value,  # .replace('\'\'', '\''),
            self.line_number)

    def __hash__(self) -> int:
        # This is so that we can have sets of tokens
        return hash(self.value)

    def __lt__(self, other) -> bool:
        return self.value < other.value

    def __gt__(self, other) -> bool:
        return self.value > other.value

    def __name__(self) -> bool:
        return self.type

    def __eq__(self, other) -> bool:
        return (self.type == other.type) and (self.value == other.value)

    def __bool__(self) -> bool:
        return True if self.value  else False


if __name__ == "__main__":
    from argparse import ArgumentParser

    arg = ArgumentParser(description="Pass in strings on the command line to test their interpretation")
    arg.add_argument("tokens", nargs='+')
    arg.add_argument('-d', '--debug', help="The logging debug level to use", default=logging.NOTSET, metavar='LEVEL')
    args = arg.parse_args()

    logging.basicConfig(level=logging.ERROR)
    logger.setLevel(int(args.debug))
    tokens = args.tokens

    line = 0
    for line, s in enumerate(tokens):
        token = Token(line_number=line, s_input=s)
        print("\nValue: %s" % token.value)
        print("Type: %s" % token.type)
        print("Line: %s" % str(token.line_number))
