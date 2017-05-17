#!/usr/bin/env python3
from argparse import ArgumentParser
from difflib import unified_diff

import re
import sys
from termcolor import cprint
from tokens import TokenError
import lexical_analyzer
import datalog_parser
import subprocess

args = ArgumentParser(description="Test your binary against a python datalog parser")

args.add_argument('-l', '--lab', help="The lab number you are testing. Default is 5", default=5)
args.add_argument('-p', '--part', help="The lab part you are testing. Default is 2", default=2)
args.add_argument('-b', '--binary', help="Your binary file", default=None)
args.add_argument("test_files", nargs="+", help="The files that will be used in this test")
arg = args.parse_args()

lab = int(arg.lab)
test_files = arg.test_files
binary = arg.binary
part = int(arg.part)

if not (1 <= lab <= 5):
    raise ValueError("Lab number must be an integer from 1 to 6")

if not (1 <= part <= 2):
    raise ValueError("Part must be either 1 or 2")


for test in test_files:
    print('-' * 80)
    if lab == 1:
        print("Testing %s on Lab %s" % (test, str(lab)))
    else:
        print("Testing %s on Lab %s Part %s" % (test, str(lab), str(part)))
    print('-' * 80)

    # Grab the user output from their binary
    actual = None
    timeout = False
    if binary:
        if not binary[0] == '/':
            binary = "./" + binary
        # Wait at most 60 seconds for the binary to run
        actual = ""
        try:
            actual = str(subprocess.check_output("%s %s" % (binary, test), shell=True, timeout=60), 'utf-8')
        except subprocess.TimeoutExpired:
            cprint("Failed! Timeout exceeded", 'red')
            timeout = True

    if not timeout:
        expected = ''
        # Compute the correct output from the python script
        if lab == 1:
            lex = lexical_analyzer.scan(test)
            for line in lex:
                expected = expected + '(%s,"%s",%s)' % line + "\n"
            expected = expected + ("Total Tokens = %s\n" % len(lex))
        elif lab == 2:
            command = "%s/%s --part %s %s" % (sys.path[0], "datalog_parser.py", str(part), test)
            expected = str(subprocess.check_output(command, shell=True), 'utf-8')
        elif lab == 3:
            print("Lab %s part %s has not yet been implemented" % (str(lab), str(part)))
        elif lab == 4:
            print("Lab %s part %s has not yet been implemented" % (str(lab), str(part)))
        elif lab == 5:
            print("Lab %s part %s has not yet been implemented" % (str(lab), str(part)))

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
                        # If this is lab 1 then I will build a list of offending tokens
                        if lab == 1:
                            tokex = re.compile("^\(\w+,(.*),(\d+)\)", re.MULTILINE)
                            match = tokex.match(line[1:])
                            if match:
                                offending_tokens.append((str(match.group(1)), int(match.group(2))))
                    elif line[0] == '+':
                        # This is what the user actually produced
                        cprint(line[1:], 'red')
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
                # Print all but last new line
                print(expected[:-1])
                pass
            pass
