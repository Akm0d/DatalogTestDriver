#!/usr/bin/env python3

from argparse import ArgumentParser
import lexical_analyzer
import subprocess

args = ArgumentParser(description="Test your binary against a python datalog parser")

args.add_argument('-l', '--lab-number', help="The lab number you are testing. Default is 1", default=1)
args.add_argument('binary', help="Your binary file")
args.add_argument("test_files", nargs="+", help="The files that will be used in this test")
arg = args.parse_args()

lab = int(arg.lab_number)
test_files = arg.test_files
binary = arg.binary

if not (1 <= lab <= 6):
    raise ValueError("Lab number must be an integer from 1 to 6")

for test in test_files:
    # Grab the user output from their binary
    actual = str(subprocess.check_output("%s %s" % (binary, test), shell=True), 'utf-8')

    expected = ''
    # Compute the correct output from the python script
    if lab == 1:
        lex = lexical_analyzer.scan(test)
        for line in lex:
            expected = expected + line + "\n"
        expected = expected + ("Total Tokens = %s\n" % len(lex))
    elif lab == 2:
        print("Lab %s has not yet been implemented" % str(lab))
    elif lab == 3:
        print("Lab %s has not yet been implemented" % str(lab))
    elif lab == 4:
        print("Lab %s has not yet been implemented" % str(lab))
    elif lab == 5:
        print("Lab %s has not yet been implemented" % str(lab))
    elif lab == 6:
        print("Lab %s has not yet been implemented" % str(lab))


    with open("temp_file_1.tmp", 'w') as temp:
        temp.write(actual)

    with open("temp_file_2.tmp", 'w') as temp:
        temp.write(expected)

    if actual == expected:
        print("Success while comparing output from %s" % test)
    else:
        # Print the diff
        # TODO make this pretty
        print(actual)
        print(expected)
        pass

