#!/usr/bin/env python3
from argparse import ArgumentParser
from difflib import unified_diff
from lexical_analyzer import scan as lexical_scan
from lizard import analyze_file, FunctionInfo
from os import path as os_path, name as os_name, listdir
from re import compile as re_compile, MULTILINE
from subprocess import TimeoutExpired, check_output, check_call
from sys import argv
from termcolor import cprint

import datalog_parser
import relational_database
import datalog_interpreter

# This is the cyclomatic complexity threshhold allowed for each function
COMPLEXITY_THRESHHOLD = 8

# If there are no arguments, then print the help text
if len(argv) == 1:
    argv.append("--help")

args = ArgumentParser(description="Test your binary against a python datalog parser")

args.add_argument('-b', '--binary', help="Your binary file", default=None)
args.add_argument('-c', '--compile', help="The directory where your main.cpp can be found. "
                                          "Supplying this argument also allows your code to be analyzed for "
                                          "cyclomatic complexity",
                  default=None
                  )
args.add_argument('-l', '--lab', help="The lab number you are testing. Default is 5", default=5)
args.add_argument('-p', '--part', help="The lab part you are testing. Default is 2", default=2)
args.add_argument("test_files", nargs="+", help="The files that will be used in this test")
arg = args.parse_args()

lab = int(arg.lab)
test_files = arg.test_files
binary = arg.binary
part = int(arg.part)
code_directory = arg.compile

if not (1 <= lab <= 5):
    raise ValueError("Lab number must be an integer from 1 to 6")

if not (1 <= part <= 2):
    raise ValueError("Part must be either 1 or 2")

# If a code directory was given, then try to compile it
if code_directory:
    # If they gave a code directory but not a binary name, then name the binary now
    if not binary:
        binary = "lab%sp%s.%s" % (str(lab), str(part), "exe" if os_name == 'nt' else "bin")
    if os_name == 'nt':
        # TODO compile using cl
        print("Unable to compile %s, make sure you are using a unix based operating system" % binary)
        pass
    else:
        # Compile using g++
        check_call("g++ -std=c++14 -o %s -g -Wall %s" % (binary, os_path.join(code_directory, "*.cpp")), shell=True)
        pass

tests_total = 0
tests_passed = 0
for test in test_files:
    tests_total += 1
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
            actual = str(check_output("%s %s" % (binary, test), shell=True, timeout=60), 'utf-8')
        except TimeoutExpired:
            cprint("Failed! Timeout exceeded", 'red')
            timeout = True

    if not timeout:
        expected = ''
        # Compute the correct output from the python script
        if lab == 1:
            lex = lexical_scan(test)
            for line in lex:
                expected = expected + '(%s,"%s",%s)' % line + "\n"
            expected = expected + ("Total Tokens = %s\n" % len(lex))
        elif lab == 2:
            expected = datalog_parser.main(test, part=part, debug=False)
        elif lab == 3:
            expected = relational_database.main(test, part=part, debug=False)
        elif lab == 4:
            print("Lab %s part %s has not yet been implemented" % (str(lab), str(part)))
        elif lab == 5:
            print("Lab %s part %s has not yet been implemented" % (str(lab), str(part)))

        if actual == expected:
            tests_passed += 1
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
                            tokex = re_compile("^\(\w+,(.*),(\d+)\)", MULTILINE)
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
                line_number_width = 0
                with open(test) as f:
                    line_number_width = len(str(len(f.readlines())))
                with open(test) as f:
                    line_count = 1
                    i = 1
                    for line in f:
                        line = line.rstrip('\n')
                        if lab == 1:
                            # If this line of the file has an offending token, then print the misinterpreted value red
                            if i in [x[1] for x in offending_tokens]:
                                strings = [x[0] for x in offending_tokens if x[1] == i]
                                # print(strings)
                                cprint("%{}s ".format(line_number_width) % str(line_count), 'red', end='')
                                print(line)
                            else:
                                print("%{}s ".format(line_number_width) % str(line_count), end='')
                                print(line)
                            i += 1
                        else:
                            # Print line numbers in color with a fixed width equal to that of the last line number
                            cprint("%{}s ".format(line_number_width) % str(line_count), 'yellow', end='')
                            print(line)
                        line_count += 1
            else:
                # Print all but last new line
                print(expected.rstrip('\n'))
                pass
            pass

# Now we are printing test results

# Check code cyclomatic complexity
complex_functions = list()
simple = True
if code_directory:
    for file in listdir(code_directory):
        if file.endswith('.cpp'):
            cc = analyze_file(os_path.join(code_directory, file))
            for func in cc.function_list:
                assert isinstance(func, FunctionInfo)
                if func.cyclomatic_complexity > COMPLEXITY_THRESHHOLD:
                    simple = False
                    complex_functions.append(func)

# Print out only the complex functions
if complex_functions:
    padding = 0
    # Find the longest function name
    for func in complex_functions:
        if len(func.name) > padding:
            padding = len(func.name)
    padding += 1

    print('=' * 80)
    print("Function".ljust(padding) + "Cyclomatic Complexity")
    print("--------" + " " * (padding - len("Function")) + "---------------------")
    for func in complex_functions:
        assert isinstance(func, FunctionInfo)
        cprint("%s %s" % (str(func.name).ljust(padding), func.cyclomatic_complexity), "red")

if binary:
    print('=' * 80)
    print("Tests Run: %s" % str(tests_total))
    if tests_passed == tests_total and simple:
        cprint("All tests passed", 'green')
    else:
        cprint("Passed: %s" % str(tests_passed), 'green')
        cprint("Failed: %s" % str((tests_total - tests_passed) + len(complex_functions)), 'red')
