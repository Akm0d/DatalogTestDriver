#!/usr/bin/env python3
from argparse import ArgumentParser
from termcolor import colored, cprint
from tokens import TokenError
import lexical_analyzer
import datalog_parser
import subprocess

args = ArgumentParser(description="Test your binary against a python datalog parser")

args.add_argument('-l', '--lab-number', help="The lab number you are testing. Default is 1", default=1)
args.add_argument('-b', '--binary', help="Your binary file", default=None)
args.add_argument("test_files", nargs="+", help="The files that will be used in this test")
arg = args.parse_args()

lab = int(arg.lab_number)
test_files = arg.test_files
binary = arg.binary

if not (1 <= lab <= 6):
    raise ValueError("Lab number must be an integer from 1 to 6")

for test in test_files:
    print('-' * 80)
    print("Testing %s" % test)
    print('-' * 80)

    # Grab the user output from their binary
    actual = None
    if binary:
        actual = str(subprocess.check_output("%s %s" % (binary, test), shell=True), 'utf-8')

    expected = ''
    # Compute the correct output from the python script
    if lab == 1:
        lex = lexical_analyzer.scan(test)
        for line in lex:
            expected = expected + '(%s,"%s",%s)' % line + "\n"
        expected = expected + ("Total Tokens = %s\n" % len(lex))
    elif lab == 2:
        lex = lexical_analyzer.scan(test)
        # Ignore traces on token errors
        try:
            datalog = datalog_parser.DatalogProgram(lex)
            expected = "Success!\n" + str(datalog)
        except TokenError:
            pass
    elif lab == 3:
        print("Lab %s has not yet been implemented" % str(lab))
    elif lab == 4:
        print("Lab %s has not yet been implemented" % str(lab))
    elif lab == 5:
        print("Lab %s has not yet been implemented" % str(lab))
    elif lab == 6:
        print("Lab %s has not yet been implemented" % str(lab))

    if binary:
        with open("temp_file_1.tmp", 'w') as temp:
            temp.write(actual)

    with open("temp_file_2.tmp", 'w') as temp:
        temp.write(expected)

    if actual == expected:
        cprint("Passed", "green")
    else:
        # Print the diff
        if binary:
            print(actual)
        print(expected)
        pass
