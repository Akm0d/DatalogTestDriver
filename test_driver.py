#!/usr/bin/env python3
from argparse import ArgumentParser
from difflib import unified_diff

import re
from termcolor import cprint
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
            offending_tokens = list()
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
                    # If this is lab 1 then I will build a list of offending tokens
                    if lab == 1:
                        tokex = re.compile("^\(\w+,(.*),(\d+)\)", re.MULTILINE)
                        match = tokex.match(line[1:])
                        if match:
                            offending_tokens.append((str(match.group(1)), int(match.group(2))))
                else:
                    cprint(line.lstrip(' '), 'white')
            print('-' * 80)
            # Print out the test file
            with open(test) as f:
                i = 1
                for line in f:
                    line = line.rstrip('\n')
                    if lab == 1:
                        # If this line of the file has an offending token, then print the misinterpreted value in red
                        if i in [x[1] for x in offending_tokens]:
                            strings = [x[0] for x in offending_tokens if x[1] == i]
                            # print(strings)
                            cprint(line, 'yellow')
                        else:
                            print(line)
                        i += 1
                    else:
                        print(line)
        else:
            print(expected)
        pass
