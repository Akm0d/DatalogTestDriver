#!/usr/bin/env python3
import logging
import multiprocessing

from collections import defaultdict
from tarjan import tarjan as SCC
from typing import Iterator
from orderedset._orderedset import OrderedSet

import lexical_analyzer
from datalog_interpreter import DatalogInterpreter
from datalog_parser import DatalogProgram, Rules, Rule
from tokens import TokenError

logger = logging.getLogger(__name__)


class Vertex(Rule, set):
    def __init__(self, rule: Rule, index: int, rules: Rules):
        Rule.__init__(self, head=rule.head, predicates=rule.predicates)
        set.__init__(self)
        self.rule = rule
        self.id = index
        self.rules = rules
        self.update(self._adjacency())

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

    def __reversed__(self):
        reverse = Vertex(self.rule, 0 - self.id, self.rules)
        reverse.clear()
        for i, r in enumerate(self.rules.rules):
            if self.rule.head.id in [p.id for p in r.predicates]:
                reverse.add(i)
                continue
        return reverse

    def __str__(self):
        return "R{}:{}".format(self.id, ",".join("R{}".format(r) for r in sorted(self)))


class DependencyGraph(defaultdict):
    def __init__(self, rules: Rules):
        super().__init__(list)
        logger.debug("Rules:\n" + str("\n".join(str(x) for x in rules.rules)) + "\n")
        post_order_traversal = OrderedSet()

        # Each rule is assigned a unique ID
        for i, rule in enumerate(rules.rules):
            self[i] = Vertex(rule, index=i, rules=rules)
            for x in reversed(sorted(self[i])):
                post_order_traversal.add(x)

        logger.debug("Dependency Graph:\n{}".format(self))
        logger.debug("Reverse Forest:\n{}".format(reversed(self)))
        logger.debug("Post Order Traversal:\n{}\n".format(
            "\n".join("POTN(R{}) = {}".format(p, i) for i, p in enumerate(post_order_traversal)))
        )
        scc = SCC(self)
        logger.debug("Strongly Connected Components:\n{}\n".format(
            "\n".join(",".join("R{}".format(v) for v in x) for x in scc))
        )

        logger.debug("Evaluation Order:\n")
        self.evaluation_order = list()
        # TODO Compute the evaluation order

    def __reversed__(self) -> str:
        """
        :return: A string representation of the reverse forest
        """
        return "\n".join(
            "R{}:{}".format(self[i].id, ",".join("R{}".format(r) for r in reversed(self[i])))
            for i in sorted(self.keys())
        ) + "\n"

    def __str__(self):
        return "\n".join(str(self[i]) for i in sorted(self.keys())) + "\n"


class RuleOptimizer(DatalogInterpreter):
    def __init__(self, datalog_program: DatalogProgram):
        super().__init__(datalog_program, least_fix_point=False)

        # TODO Evaluate the rules in the order described by the rule optimizer
        self.dependency_graph = DependencyGraph(datalog_program.rules)
        self.rule_evaluation = self.evaluate_optimized_rules(order=list(self.dependency_graph))

        logger.info("Evaluating Queries")
        for query in datalog_program.queries.queries:
            self.rdbms[query] = self.evaluate_query(query)

    def evaluate_optimized_rules(self, order: Iterator[Vertex]) -> str:
        # TODO This will be the SCC not POT
        # logger.debug("Evaluation order: {}".format(",".join("R{}".format(o.id) for o in order)))
        return ""

    def __str__(self):
        logger.debug("Generating String from Rule Optimizer")
        result = "Dependency Graph\n{}\n".format(self.dependency_graph)
        result += "Rule Evaluation\n{}\n".format(self.rule_evaluation)
        result += "Query Evaluation\n"
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
            result += str(results[i])
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
