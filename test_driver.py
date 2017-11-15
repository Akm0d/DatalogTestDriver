#!/usr/bin/env python3

from argparse import ArgumentParser
from enum import Enum

from lizard import analyze_file, FunctionInfo
from os import path as os_path, name as os_name, listdir
from subprocess import TimeoutExpired, check_output, check_call, CalledProcessError, PIPE
from sys import argv, exit as sys_exit
from tempfile import NamedTemporaryFile

from datalog_interpreter import DatalogInterpreter
from lexical_analyzer import scan as lexical_scan
from datalog_parser import DatalogProgram
from relational_database import RDBMS
from rule_optimizer import RuleOptimizer
from tokens import TokenError

import unittest
import logging

logger = logging.getLogger(__name__)


class Message(Enum):
    TIMEOUT = "Timeout"
    CRASHED = "Crashed"
    INVALID_LAB = "Invalid lab number"


class TestDriver(unittest.TestCase):
    complexity_threshold = 8
    timeout = 60

    @classmethod
    def setUpClass(cls):

        arg = ArgumentParser(description="Test your binary against a python datalog parser")
        # TODO combine the binary/compile options
        arg.add_argument('student_code', help="Your binary file or the directory where your main.cpp can be found.")
        arg.add_argument('-d', '--debug', help="The logging debug level to use", default=logging.NOTSET,
                         metavar='LEVEL')
        arg.add_argument('-l', '--lab', help="The lab number you are testing. Default is 5", default=0, type=int)
        arg.add_argument('--sandbox', action='store_true', default=False, help="Run the sandbox utility.")
        arg.add_argument("test_files", nargs="*", help="The files that will be used in this test")
        args = arg.parse_args()

        # Set up the logger
        logging.basicConfig(level=logging.ERROR)
        logger.setLevel(int(args.debug))

        # Make sure test files are provided
        cls.test_files = args.test_files

        if not cls.test_files:
            raise FileNotFoundError("No test files provided")

        cls.lab = args.lab

        if os_path.isdir(args.student_code):
            # COMPILE Their code
            cls.sources = [os_path.join(args.student_code, x)
                           for x in listdir(args.student_code) if x.endswith('.cpp') or x.endswith('.h')]
            cls.binary = cls.compileCode(cls)
        elif os_path.exists(args.student_code):
            cls.sources = list()
            cls.binary = args.student_code
        else:
            raise FileNotFoundError("Could not find student code at {}".format(args.student_code))

        # Get the lab Number
        if not args.lab:
            cls.lab = cls.getLabNumber(cls)
        else:
            cls.lab = args.lab
        if not (1 <= cls.lab <= 5):
            raise ValueError("Lab number must be an integer from 1 to 5")

    def test_cyclomatic_complexity(self):
        logger.debug("Testing cyclomatic complexity")
        for c in [s for s in self.sources if s.endswith('.cpp')]:
            cc = analyze_file(c)
            for f in cc.function_list:
                function_complexity = f.cyclomatic_complexity
                assert isinstance(f, FunctionInfo)
                with self.subTest(source=c, hunction=f.name):
                    self.assertLessEqual(function_complexity, self.complexity_threshold)

    def test_all(self):
        """
        Run unittest against all of the test files
        """
        for t in self.test_files:
            with self.subTest(test_file=t):
                logger.info("Lab {} on Test {}".format(self.lab, t))

                # Grab the student output from their binary
                student_output = self.student_output(t)
                self.assertNotIsInstance(student_output, Message)
                expected = self.driver_output(t)
                self.assertEqual(student_output.strip(),  expected.strip())
                # TODO assert runtime

    def student_output(self, test_file: str) -> str or Message:
        command = "./{} {}".format(self.binary, test_file)
        logger.debug("Student run command {}".format(command))
        logger.debug("Student run command {}".format(command))
        try:
            return str(check_output(command, shell=True, timeout=self.timeout, stderr=PIPE), 'utf-8')
        except TimeoutExpired:
            return Message.TIMEOUT
        except CalledProcessError:
            return Message.CRASHED

    def driver_output(self, test_file: str) -> str or Message:
        result = ""
        # TODO Compute the correct output from the python script, detect change by including hash of file in pickle
        # TODO save the correct output to a pickle file to lower my runtime?
        if self.lab == 1:
            lex = lexical_scan(test_file, ignore_comments=False, ignore_whitespace=True)
            for line in lex:
                result += str(line) + "\n"
            result += "Total Tokens = {}\n".format(len(lex))
            return result

        # The rest of the labs will need tokens with no comments or whitespace
        tokens = lexical_scan(test_file, ignore_comments=True, ignore_whitespace=True)
        # Ignore traces on token errors
        try:
            datalog = DatalogProgram(tokens)
            if self.lab == 2:
                result = "Success!\n{}".format(datalog)
        except TokenError as t:
            return 'Failure!\n  {}'.format(t)

        if self.lab == 3:
            rdbms = RDBMS(datalog)
            for datalog_query in datalog.queries.queries:
                rdbms.rdbms[datalog_query] = rdbms.evaluate_query(datalog_query)
            return str(rdbms)
        elif self.lab == 4:
            return str(DatalogInterpreter(datalog))
        elif self.lab == 5:
            return str(RuleOptimizer(datalog))
        else:
            return Message.INVALID_LAB

    @classmethod
    def tearDownClass(cls):
        pass

    def compileCode(self) -> str:
        file_name = "lab{}.{}".format(self.lab, "exe" if os_name == 'nt' else "bin")
        if os_name == 'nt':
            # TODO compile using cl
            logger.error(
                "Unable to compile {}, make sure you are using a unix based operating system".format(file_name))
        else:
            command = "g++ -std=c++11 -o %s -g -Wall %s" % (file_name, " ".join(self.sources))
            logger.debug(command)
            check_call(command, shell=True)
            logger.debug("Creating binary '{}'".format(file_name))
        return file_name

    def getLabNumber(self) -> int:
        logger.debug("No lab number given")
        temp_file = NamedTemporaryFile()
        # Create a bare minimum datalog program
        temp_file.write("Schemes:a(a)Facts:a('a').Rules:Queries:a('a')?".encode())
        temp_file.flush()
        output = str(check_output("./{} {}".format(self.binary, temp_file.name), shell=True, timeout=60), 'utf-8')
        if output.splitlines()[-1].startswith("Total Tokens ="):
            lab = 1
        elif output.startswith("Success!"):
            lab = 2
        elif output.startswith("Schemes populated after"):
            lab = 4
        elif output.startswith("Dependency Graph"):
            lab = 5
        else:
            # Lab 3 doesn't have any unique strings
            lab = 3
        logger.debug("Detected lab {}".format(lab))
        return lab


if __name__ == "__main__":
    # If there are no arguments, then print the help text
    if len(argv) == 1:
        argv.append("--help")

    if '--sandbox' in argv:
        logger.info("Starting sandbox command line interface")
        from sandbox import Sandbox

        sandbox = Sandbox()
        sys_exit(sandbox.run())
    else:
        unittest.main(argv=[argv[0]])
