#!/usr/bin/env python3
from ast import literal_eval
from tokens import TokenError

import lexical_analyzer
import datalog_parser
import relational_database


def main(d_file, part=2, debug=False):
    result = ""
    if not (1 <= part <= 2):
        raise ValueError("Part must be either 1 or 2")

    if debug: result += ("Parsing '%s'" % d_file)

    # Create class objects
    tokens = lexical_analyzer.scan(d_file)

    if debug:
        datalog = datalog_parser.DatalogProgram(tokens)
    else:
        try:
            datalog = datalog_parser.DatalogProgram(tokens)
        except TokenError as t:
            return 'Failure!\n  (%s,"%s",%s)' % tuple(literal_eval(str(t)))

    # Datalog must exist by now, if not there is an errro
    rdbms = relational_database.RDBMS(datalog)

    return result

if __name__ == "__main__":
    """
    For part 1, this will perform single select, project, and rename operations for the file provided.  
    It will select the first query in the list and use it for all 3 operations, in succession
    
    For part 2, all queries will be analyzed and a thorough output will be printed
    """
    from argparse import ArgumentParser

    args = ArgumentParser(description="Run the datalog parser, this will produce output for lab 2")
    args.add_argument('-d', '--debug', action='store_true', default=False)
    args.add_argument('-p', '--part', help='A 1 or a 2.  Defaults to 2', default=2)
    args.add_argument('file', help='datalog file to parse')
    arg = args.parse_args()

    print(main(arg.file, part=int(arg.part), debug=arg.debug))
