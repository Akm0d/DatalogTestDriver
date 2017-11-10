#!/usr/bin/env python3
import logging

import multiprocessing

import lexical_analyzer
from datalog_interpreter import DatalogInterpreter
from datalog_parser import DatalogProgram
from tokens import TokenError

logger = logging.getLogger(__name__)


class RuleOptimizaer(DatalogInterpreter):
    def __init__(self, datalog_program: DatalogProgram):
        super().__init__(datalog_program, least_fix_point=False)

        # TODO Evaluate the rules in the order described by the rule optimizer

        logger.info("Evaluating Queries")
        for query in datalog_program.queries.queries:
            self.rdbms[query] = self.evaluate_query(query)

    def graph_dependencies(self) -> str:
        pass

    def evaluate_rule(self) -> str:
        pass


if __name__ == "__main__":
    from argparse import ArgumentParser

    arg = ArgumentParser(description="Run the Rule Optimizer.  This consumes the previous labs.")
    arg.add_argument('-d', '--debug', help="The logging debug level to use", default=logging.NOTSET, metavar='LEVEL')
    arg.add_argument('file', help='datalog file to parse')
    args = arg.parse_args()

    logging.basicConfig(level=logging.ERROR)
    logger.setLevel(int(args.debug))

    logger.info("Detected {} CPUs".format(multiprocessing.cpu_count()))
    logger.debug("Parsing '%s'" % args.file)

    # Create class objects
    tokens = lexical_analyzer.scan(args.file)
    datalog = None
    try:
        datalog = DatalogProgram(tokens)
    except TokenError as t:
        print("Failure!\n  {}".format(t))
        exit(1)

    print(RuleOptimizaer(datalog))
