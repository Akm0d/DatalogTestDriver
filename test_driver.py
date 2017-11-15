#!/usr/bin/env python3
import multiprocessing
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
from time import time
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
        arg.add_argument('-d', '--debug', help="The logging debug level to use", default=logging.INFO,
                         metavar='LEVEL')
        arg.add_argument('-l', '--lab', help="The lab number you are testing. Default is 30", default=0, type=int)
        arg.add_argument('--sandbox', action='store_true', default=False, help="Run the sandbox utility.")
        arg.add_argument('-s', '--student', type=str, default="Student", help="Student name or ID")
        arg.add_argument("test_files", nargs="*", help="The files that will be used in this test")
        args = arg.parse_args()

        # Set up the logger
        logging.basicConfig(level=logging.ERROR)
        logger.setLevel(int(args.debug))

        cls.maxDiff = None
        cls.threading = multiprocessing.Manager()
        cls.student = args.student
        cls.lab = args.lab

        # Make sure test files are provided
        cls.test_files = args.test_files
        if not cls.test_files:
            raise FileNotFoundError("No test files provided")

        if os_path.isdir(args.student_code):
            # Compile Their code
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
        # TODO Rename the bin file if we learned the name of the lab

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
            with self.subTest(test=t):
                logger.info("Lab {}: {}".format(self.lab, t))
                results = self.threading.dict()
                jobs = []

                # Start cpu thread getting student output
                p = multiprocessing.Process(target=self.student_output, args=(t, results))
                jobs.append(p)
                p.start()

                # Start cpu thread getting test driver output
                p = multiprocessing.Process(target=self.driver_output, args=(t, results))
                jobs.append(p)
                p.start()
                for proc in jobs:
                    proc.join()

                # Grab the student output from their binary
                self.assertNotIsInstance(results[self.student], Message,
                                         "Runtime exceeded {} Seconds".format(self.timeout))
                self.assertEqual(results[self.student].strip(),  results[self.__class__].strip())
                student_runtime = results[self.student + "Runtime"]
                driver_runtime = results[str(self.__class__) + "Runtime"]
                self.assertLessEqual(
                    student_runtime, driver_runtime, "{}'s code runs {}% slower than the test driver".format(
                        self.student, int(100 * (driver_runtime/student_runtime))
                    )
                )
                logger.info("Test Passed")

    def student_output(self, test_file: str, results: dict):
        start_time = time()
        command = "./{} {}".format(self.binary, test_file)
        logger.debug("Student run command {}".format(command))
        try:
            results[self.student] = str(check_output(command, shell=True, timeout=self.timeout, stderr=PIPE), 'utf-8')
        except TimeoutExpired:
            results[self.student] = Message.TIMEOUT
        except CalledProcessError:
            results[self.student] = Message.CRASHED
        results[self.student + "Runtime"] = time() - start_time

    def driver_output(self, test_file: str, results: dict):
        start_time = time()
        logger.debug("Running test driver on {}".format(test_file))
        result = ""
        # TODO Compute the correct output from the python script, detect change by including hash of file in pickle
        # TODO save the correct output to a pickle file to lower my runtime?
        if self.lab == 1:
            lex = lexical_scan(test_file, ignore_comments=False, ignore_whitespace=True)
            for line in lex:
                result += str(line) + "\n"
            result += "Total Tokens = {}\n".format(len(lex))
            results[self.__class__] = result
            return

        # The rest of the labs will need tokens with no comments or whitespace
        tokens = lexical_scan(test_file, ignore_comments=True, ignore_whitespace=True)
        # Ignore traces on token errors
        try:
            datalog = DatalogProgram(tokens)
            if self.lab == 2:
                results[self.__class__] = "Success!\n{}".format(datalog)
                return
        except TokenError as t:
            results[self.__class__] = 'Failure!\n  {}'.format(t)
            results[str(self.__class__) + "Runtime"] = time() - start_time
            return

        if self.lab == 3:
            rdbms = RDBMS(datalog)
            for datalog_query in datalog.queries.queries:
                rdbms.rdbms[datalog_query] = rdbms.evaluate_query(datalog_query)
            results[self.__class__] = str(rdbms)
        elif self.lab == 4:
            results[self.__class__] = str(DatalogInterpreter(datalog))
        elif self.lab == 5:
            results[self.__class__] = str(RuleOptimizer(datalog))
        else:
            results[self.__class__] = Message.INVALID_LAB

        results[str(self.__class__) + "Runtime"] = time() - start_time

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
        print("Starting sandbox command line interface")
        from sandbox import Sandbox

        sandbox = Sandbox()
        sys_exit(sandbox.run())
    else:
        unittest.main(argv=[argv[0]])
