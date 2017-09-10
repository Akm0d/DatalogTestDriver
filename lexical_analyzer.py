#!/usr/bin/env python3
from tokens import Token, TokenType


def scan(datalog_file):
    """
    :param datalog_file: The example datalog file being parsed
    :return: a list of tokens
    """
    tokens = list()

    with open(datalog_file) as file:
        line_number = 1
        file_string = ""
        for line in file:
            file_string = file_string + line

        while file_string:
            token = Token(s_input=file_string, line_number=line_number)
            file_string = file_string[len(token.value):]
            if token.type == TokenType.INVALID:
                tokens.append(Token(t_type=TokenType.UNDEFINED, value=token.value[0], line_number=line_number))
                file_string = token.value[1:]
            else:
                if token.type != TokenType.WHITESPACE:
                    tokens.append(token)
                # Increment line number after adding tokens
                line_number += token.value.count('\n')
        tokens.append(Token(t_type=TokenType.EOF, value="", line_number=line_number))
    return tokens


if __name__ == "__main__":
    """
    Run the lexical analyzer by itself and produce the proper output
    """
    from argparse import ArgumentParser
    args = ArgumentParser(description="Run the lexical analyzer, this will produce output for lab 1")
    args.add_argument('-d', '--debug', action='store_true', default=False)
    args.add_argument('file', help='datalog file to lexically analyze')
    arg = args.parse_args()

    debug = arg.debug
    d_file = arg.file
    if debug: print("Analyzing '%s'" % d_file)

    all_tokens = scan(d_file)
    for single_token in all_tokens:
        print('(%s,"%s",%s)' % single_token)

    print("Total Tokens = %s" % len(all_tokens))

    pass
