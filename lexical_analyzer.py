#!/usr/bin/env python3
from argparse import ArgumentParser
from tokens import Token


def scan(datalog_file):
    """
    :param datalog_file: The example datalog file being parsed
    :return: a list of tokens
    """
    tokens = list()

    with open(datalog_file) as file:
        line_number = 1
        multiline = ''
        multiline_start = line_number
        for line in file:
            line = multiline + line.replace('\n', '')
            while line:
                token = Token(line, multiline_start if multiline else line_number)
                line = line[len(token.value):]
                if token.type == 'MULTILINE':
                    if not multiline:
                        multiline_start = line_number
                    multiline = token.value + '\n'
                    line = ''
                if token.type == 'INVALID':
                    tokens.append('(%s,"%s",%s)' % ('UNDEFINED', token.value[0], token.line_number))
                    line = token.value[1:]
                # If this is a regular, single-line token then add it to the list
                elif not multiline:
                    # Ignore whitespace
                    if not token.type == 'WHITESPACE':
                        tokens.append('(%s,"%s",%s)' % (token.type, token.value, token.line_number))
                # if we are currently building a multiline token, and it was identified as something new, then add it
                elif not token.type == 'MULTILINE':
                    tokens.append('(%s,"%s",%s)' % (token.type, token.value, token.line_number))
                    multiline = ''
            line_number += 1
        if multiline:
            token = Token(multiline[:-1], multiline_start)
            tokens.append('(%s,"%s",%s)' % ('UNDEFINED', token.value, token.line_number))

        tokens.append('(EOF,"",%s)' % str(line_number - 1))
    return tokens


if __name__ == "__main__":
    """
    Run the lexical analyzer by itself and produce the proper output
    """
    args = ArgumentParser(description="Run the lexical analyzer, this will produce output for lab 1")
    args.add_argument('-d', '--debug', action='store_true', default=False)
    args.add_argument('file', help='datalog file to lexically analyze')
    arg = args.parse_args()

    debug = arg.debug
    d_file = arg.file
    if debug:print("Analyzing '%s'" % d_file)

    all_tokens = scan(d_file)
    for single_token in all_tokens:
        print(single_token)

    print("Total Tokens = %s" % len(all_tokens))

    pass
