#!/usr/bin/env python3
from argparse import ArgumentParser
from difflib import unified_diff
from lizard import analyze_file, FunctionInfo
from os import path as os_path, name as os_name, listdir
from re import compile as re_compile, MULTILINE
from subprocess import TimeoutExpired, check_output, check_call, CalledProcessError
from sys import argv
from termcolor import cprint
from time import time

from lexical_analyzer import scan as lexical_scan
from datalog_parser import DatalogProgram
from relational_database import RDBMS
# import datalog_interpreter

# This is the cyclomatic complexity threshhold allowed for each function
from tokens import TokenError
import logging

logger = logging.getLogger(__name__)
COMPLEXITY_THRESHHOLD = 8

# If there are no arguments, then print the help text
if len(argv) == 1:
    argv.append("--help")

arg = ArgumentParser(description="Test your binary against a python datalog parser")

arg.add_argument('-b', '--binary', help="Your binary file", default=None)
arg.add_argument('-c', '--compile', help="The directory where your main.cpp can be found. "
                                         "Supplying this argument also allows your code to be analyzed for "
                                         "cyclomatic complexity", default=None
                 )
arg.add_argument('-d', '--debug', help="The logging debug level to use", default=logging.NOTSET, metavar='LEVEL')
arg.add_argument('-l', '--lab', help="The lab number you are testing. Default is 5", default=5)
arg.add_argument('-p', '--part', help="The lab part you are testing. Default is 2", default=2)
arg.add_argument('--sandbox', action='store_true', default=False,
                 help="Run the sandbox utility.")
arg.add_argument("test_files", nargs="*", help="The files that will be used in this test")
args = arg.parse_args()

if args.sandbox:
    print("Starting sandbox command line interface")
    from sandbox import Sandbox
    sandbox = Sandbox(input_files=args.test_files)
    exit(sandbox.run())


logging.basicConfig(level=logging.ERROR)
logger.setLevel(int(args.debug))

lab = int(args.lab)
test_files = args.test_files
if not test_files:
    raise FileNotFoundError("No test files provided")
binary = args.binary
part = int(args.part)
code_directory = args.compile

sources = [os_path.join(code_directory, x) for x in listdir(args.compile) if x.endswith('.cpp') or x.endswith('.h')]

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
        command = "g++ -std=c++11 -o %s -g -Wall %s" % (binary, " ".join(sources))
        logger.debug(command)
        check_call(command, shell=True)
        logger.debug("Creating binary '{}'".format(binary))

tests_total = 0
tests_passed = 0
total_expected_runtime = 0
total_actual_runtime = 0

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
        actual_runtime = time()
        if not binary[0] == '/':
            binary = "./" + binary
        # Wait at most 60 seconds for the binary to run
        actual = ""
        try:
            actual = str(check_output("%s %s" % (binary, test), shell=True, timeout=60), 'utf-8')
        except TimeoutExpired:
            cprint("Failed! Timeout exceeded", 'red')
            timeout = True
        except CalledProcessError:
            cprint("Failed! Non-zero exit status", 'red')
        actual_runtime = time() - actual_runtime
        total_actual_runtime += actual_runtime

    if not timeout:
        expected = ''
        expected_runtime = time()
        # Compute the correct output from the python script
        # TODO save the correct output to a pickle file to lower my runtime?
        if lab == 1:
            lex = lexical_scan(test, ignore_comments=False, ignore_whitespace=True)
            for line in lex:
                expected = expected + str(line) + "\n"
            expected = expected + ("Total Tokens = %s\n" % len(lex))
        elif lab == 2:
            expected = "Success!\n"

            tokens = lexical_scan(test, ignore_comments=True, ignore_whitespace=True)

            # Ignore traces on token errors
            try:
                datalog = DatalogProgram(tokens)
                if part == 2:
                    expected += str(datalog)
            except TokenError as t:
                expected = 'Failure!\n  {}'.format(t)
        elif lab == 3:
            # Create class objects
            tokens = lexical_scan(test)

            try:
                datalog = DatalogProgram(tokens)
                assert isinstance(datalog, DatalogProgram)

                rdbms = RDBMS(datalog)

                for datalog_query in datalog.queries.queries:
                    rdbms.rdbms[datalog_query] = rdbms.evaluate_query(datalog_query)

                expected = str(rdbms)
            except TokenError as t:
                expected = 'Failure!\n  {}'.format(t)

        elif lab == 4:
            expected = datalog_interpreter.main(test, part=part, debug=False)
        elif lab == 5:
            print("Lab %s part %s has not yet been implemented" % (str(lab), str(part)))
        expected_runtime = time() - expected_runtime
        total_expected_runtime += expected_runtime
        logger.info("Student runtime: {}".format(actual_runtime))
        logger.info("Maximum runtime: {}".format(expected_runtime))

        if actual.rstrip() == expected.rstrip():
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
    for file in sources:
        if file.endswith('.cpp'):
            cc = analyze_file(file)
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
        cprint("Passed: {}".format(tests_passed), 'green' if tests_passed else 'red')
        tests_failed = tests_total - tests_passed
        cprint("Failed: {}".format(tests_failed), 'red' if tests_failed else 'green')
    if code_directory:
        cprint('Complex Functions: {}'.format(len(complex_functions)), 'red' if complex_functions else 'green')
    logger.debug("Student Total runtime: {} ms".format(total_actual_runtime))
    logger.debug("Maximum Total runtime: {} ms".format(total_expected_runtime))
    runtime_score = (total_expected_runtime - total_actual_runtime) / total_actual_runtime
    logger.debug("Raw runtime score: {}".format(runtime_score))
    if runtime_score < 0:
        runtime_score = 0
    if runtime_score > 1:
        runtime_score = 1.05

    if runtime_score > 1:
        runtime_grade = 'S+'
    elif runtime_score > 0.97:
        runtime_grade = 'A+'
    elif runtime_score > 0.93:
        runtime_grade = 'A'
    elif runtime_score > 0.89:
        runtime_grade = 'A-'
    elif runtime_score > 0.87:
        runtime_grade = 'B+'
    elif runtime_score > 0.83:
        runtime_grade = 'B'
    elif runtime_score > 0.79:
        runtime_grade = 'B-'
    elif runtime_score > 0.77:
        runtime_grade = 'C+'
    elif runtime_score > 0.73:
        runtime_grade = 'C'
    elif runtime_score > 0.79:
        runtime_grade = 'C-'
    elif runtime_score > 0.67:
        runtime_grade = 'D+'
    elif runtime_score > 0.53:
        runtime_grade = 'D'
    elif runtime_score > 0.49:
        runtime_grade = 'D-'
    elif runtime_score > 0:
        runtime_grade = 'F'
    else:
        runtime_grade = 'E'

    cprint('Runtime Score: {}'.format(runtime_grade), 'red' if runtime_score < 0.5 else 'green')
