#!/usr/bin/env python3
import logging

from os import path

from tokens import Token, TokenType
from typing import List

logger = logging.getLogger("Lexical Analyzer")


def scan(datalog_file: str = None, ignore_whitespace: bool =True, ignore_comments: bool=True, input_data: str = None) -> List[Token]:
    """
    :param ignore_comments: 
    :param ignore_whitespace:
    :param datalog_file: The example datalog file being parsed
    :return: a list of tokens
    """
    tokens = list()

    file_string = ""
    if input_data is None and path.exists(str(datalog_file)):
        with open(datalog_file) as datalog_file_stream:
            file_string = "".join([line for line in datalog_file_stream])
    elif input_data is not None:
        file_string = input_data

    line_number = 1
    while file_string:
        token = Token(s_input=file_string, line_number=line_number)
        file_string = file_string[len(token.value):]
        if token.type == TokenType.INVALID:
            logger.debug('Token was invalid %s' % token.value.replace('\n', '\\n'))
            tokens.append(Token(t_type=TokenType.UNDEFINED, value=token.value[0], line_number=line_number))
            # file_string = token.value[1:]
        elif ignore_whitespace and token.type == TokenType.WHITESPACE:
            logger.debug('Ignoring whitespace "%s"' % token.value.replace('\n', '\\n'))
        elif ignore_comments and token.type == TokenType.COMMENT:
            logger.debug('Ignoring Comment "%s"' % token.value.replace('\n', '\\n'))
        else:
            logger.debug('Adding Token %s' % str(token).replace('\n', '\\n'))
            tokens.append(token)

        # Increment line number after adding tokens
        token_lines = token.value.count('\n')
        line_number += token_lines
        logger.log(logging.DEBUG - 5, "Added {} Lines to Line counter.  Current line is: {}".format(token_lines, line_number))
    tokens.append(Token(t_type=TokenType.EOF, value="", line_number=line_number))
    logger.debug("Adding EOF Token at line {}".format(line_number))
    return tokens


if __name__ == "__main__":
    """
    Run the lexical analyzer by itself and produce the proper output
    """
    from argparse import ArgumentParser

    args = ArgumentParser(description="Run the lexical analyzer, this will produce output for lab 1")
    args.add_argument('-d', '--debug', help="The logging debug level to use", default=logging.NOTSET, metavar='LEVEL')
    args.add_argument('file', help='datalog file to lexically analyze')
    arg = args.parse_args()

    # Set all other loggers to ERROR only and then set this file's logging level
    logging.basicConfig(level=logging.ERROR)
    logger.setLevel(int(arg.debug))
    d_file = arg.file

    all_tokens = scan(d_file, ignore_whitespace=True, ignore_comments=False)
    for single_token in all_tokens:
        print(single_token)

    print("Total Tokens = %s" % len(all_tokens))
