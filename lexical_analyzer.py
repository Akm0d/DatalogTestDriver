#!/usr/bin/env python3
from tokens import Token


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
            token = Token(file_string)
            file_string = file_string[len(token.value):]
            if token.type == 'INVALID':
                tokens.append(('UNDEFINED', token.value[0], line_number))
                file_string = token.value[1:]
            else:
                line_number += token.value.count('\n')
                if token.type != 'WHITESPACE':
                    tokens.append((token.type, token.value, line_number))
        # If it was an empty file then we want the line number to be 1
        if line_number == 1: line_number += 1
        tokens.append(('EOF', "", str(line_number)))
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
