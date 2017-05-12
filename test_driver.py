#!/usr/bin/env python3
from argparse import ArgumentParser
from difflib import SequenceMatcher, unified_diff

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
        if not binary[0] == '/':
            binary = "./" + binary
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

    if actual == expected:
        cprint("Passed", "green")
    else:
        # Print the test and the diff
        if binary:
            with open(test) as f:
                for i in f:
                    print(i.rstrip('\n'))
            print('-' * 80)
            diff = unified_diff(expected.splitlines(1), actual.splitlines(1))
            for line in diff:
                line = line.rstrip('\n')
                if (line[-2:] == '@@' and line[:2] == '@@') or line in ['--- ', '+++ ']:
                    pass
                elif line[0] == '-':
                    # This is the expected/correct value
                    cprint(line[1:], 'green')
                elif line[0] == '+':
                    # This is what the user actually produced
                    cprint(line[1:], 'red')
                else:
                    cprint(line.lstrip(' '), 'white')
        else:
            print(expected)
        pass
