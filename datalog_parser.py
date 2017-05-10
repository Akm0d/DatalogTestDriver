#!/usr/bin/env python3


if __name__ == "__main__":
    """
    Run the datalog parser by itself and produce the proper output
    """
    args = ArgumentParser(description="Run the datalog parser, this will produce output for lab 2")
    args.add_argument('-d', '--debug', action='store_true', default=False)
    args.add_argument('file', help='datalog file to parse')
    arg = args.parse_args()

    debug = arg.debug
    d_file = arg.file

    if debug:print("Parsing '%s'" % d_file)


    pass
