#!/usr/bin/env python3
import logging
import multiprocessing

import lexical_analyzer
from datalog_interpreter import DatalogInterpreter
from datalog_parser import DatalogProgram, Rules, Rule
from tokens import TokenError

logger = logging.getLogger(__name__)


class Vertex(Rule):
    def __init__(self, rule: Rule, index: int, rules: Rules):
        super().__init__(head=rule.head, predicates=rule.predicates)
        self.rule = rule
        self.id = index
        self.rules = rules
        self.edges = self._adjacency()
        self.reverse = self._reverse_edges()

    def _adjacency(self) -> set:
        """
        For the given rule, calculate the rules that it affects
        """
        adjacent = set()
        for i, r in enumerate(self.rules.rules):
            if r.head.id in [p.id for p in self.rule.predicates]:
                adjacent.add(i)
                continue
        return adjacent

    def _reverse_edges(self) -> set:
        """
        Calculate the reverse edges for this vertex
        """
        reverse = set()
        for i, r in enumerate(self.rules.rules):
            if self.rule.head.id in [p.id for p in r.predicates]:
                reverse.add(i)
                continue
        return reverse

    def __str__(self):
        return "R{}:{}".format(self.id, ",".join("R{}".format(r) for r in sorted(self.edges)))


class DependencyGraph(dict):
    def __init__(self, rules: Rules):
        super().__init__()
        logger.debug("{}\n".format(rules))

        # Each rule is assigned a unique ID
        for i, rule in enumerate(rules.rules):
            self[i] = Vertex(rule, index=i, rules=rules)

        logger.debug("Dependency Graph:\n{}".format(self))
        logger.debug("Reverse Forest:\n{}".format(self.reverse()))

    def reverse(self) -> str:
        """
        :return: A string representation of the reverse forest
        """
        return "\n".join(
            "R{}:{}".format(self[i].id, ",".join("R{}".format(r) for r in sorted(self[i].reverse)))
            for i in sorted(self.keys())
        ) + "\n"

    def __str__(self):
        return "\n".join(str(self[i]) for i in sorted(self.keys())) + "\n"


class RuleOptimizer(DatalogInterpreter):
    def __init__(self, datalog_program: DatalogProgram):
        super().__init__(datalog_program, least_fix_point=False)

        # TODO Evaluate the rules in the order described by the rule optimizer
        self.dependency_graph = DependencyGraph(datalog_program.rules)
        self.rule_evaluation = self.evaluate_optimized_rules(order=self.dependency_graph)

        logger.info("Evaluating Queries")
        for query in datalog_program.queries.queries:
            self.rdbms[query] = self.evaluate_query(query)

    def evaluate_optimized_rules(self, order: DependencyGraph) -> str:
        return ""

    def __str__(self):
        result = "Dependency Graph\n{}\n".format(self.dependency_graph)
        result += "Rule Evaluation\n{}\n".format(self.rule_evaluation)

        manager = multiprocessing.Manager()
        results = manager.dict()
        jobs = []
        for i, query in enumerate(self.rdbms.keys()):
            p = multiprocessing.Process(target=self._str_worker, args=(i, query, results))
            jobs.append(p)
            p.start()
        for proc in jobs:
            proc.join()
        for i, _ in enumerate(self.rdbms.keys()):
            result += results[i]
        return result


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

    print(RuleOptimizer(datalog))
