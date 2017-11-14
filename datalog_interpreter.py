#!/usr/bin/env python3
import multiprocessing
import logging
from typing import List

import pandas as pd
from tokens import TokenError, Token
import lexical_analyzer
import datalog_parser
import relational_database

logger = logging.getLogger(__name__)


class DatalogInterpreter(relational_database.RDBMS):
    merge_token = Token(-1)

    def __init__(self, datalog_program: datalog_parser.DatalogProgram, least_fix_point: bool = True):
        super().__init__(datalog_program)
        self.rules = datalog_program.rules.rules
        self.passes = 1

        # Don't evaluate rules yet if we are going to use a better algorithm to find their dependencies
        if least_fix_point:
            logger.info("Evaluating Rules")
            self.passes = self.evaluate_rules()

            logger.info("Evaluating Queries")
            for query in datalog_program.queries.queries:
                self.rdbms[query] = self.evaluate_query(query)

    def evaluate_rule(self, rule: datalog_parser.Rule) -> bool:
        joined = self.join(rule)
        if not joined.empty:
            return self.union(rule.head, joined)
        return False

    def evaluate_rules(self, rules: List[datalog_parser.Rule] = None) -> int:
        """
        Each rule potentially adds new facts to a relation.
        The fixed-point algorithm repeatedly performs iterations on the rules adding new facts from each rule as the facts are generated.
        Each iteration may change the database by adding at least one new tuple to at least one relation in the database.
        The fixed-point algorithm terminates when an iteration of the rule expression set does not union a new tuple to any relation in the database.
        """
        if rules is None:
            rules = self.rules
        passes = 0
        change = True
        while change:
            change = False
            for rule in rules:
                joined = self.join(rule)
                if not joined.empty:
                    change |= self.union(rule.head, joined)
            passes += 1
        return passes

    def join(self, rule: datalog_parser.Rule) -> relational_database.Relation:
        logger.debug("Evaluating '%s'" % str(rule))
        # Evaluate the predicates on the right-hand side of the rule
        relations = [self.evaluate_query(predicate) for predicate in rule.predicates]

        relation = relations.pop()
        # Join the relations that result
        while relations:
            new_rel = relations.pop()
            common_columns = set(list(new_rel)) & set(list(relation))
            logger.debug("Merge A:\n{}".format(relation))
            logger.debug("Merge B:\n{}".format(new_rel))
            if common_columns:
                logger.debug("Relations share a common column: {}".format([str(x) for x in common_columns]))
                relation = pd.merge(relation, new_rel, how='inner').dropna()
            else:
                logger.debug("Adding common column")
                relation[self.merge_token] = 0
                new_rel[self.merge_token] = 0
                relation = pd.merge(relation, new_rel, how='outer').dropna()
                relation = relation.drop(self.merge_token, axis=1)
            logger.debug("Combined:\n{}".format(relation))

        logger.debug("Joined:\n{}".format(relation))

        return relation

    def union(self, head: datalog_parser.headPredicate, relation: relational_database.Relation) -> bool:
        """
        Union the results of the join with the relation in the database whose name is equal to the name of the head of
        the rule. In "join" we called this relation in the database r.
        Add tuples to relation r from the result of the join.
        :param head: A head predicate
        :param relation: A relation
        :return: True if the database increased in size, otherwise false
        """
        logger.debug("Uniting based on '{}'".format(head))
        size = len(self.relations.get(head.id, ""))
        # Project columns that appear in head predicate
        # Rename relation to match the schema of the relation in the database
        try:
            relation = relation[[x for x in head.idList]]
        except KeyError as e:
            logger.warning(e)
            return False
        logger.debug("Project:\n{}".format(relation))
        relation.columns = range(relation.shape[1])

        # Union with the relation in the database
        if isinstance(self.relations.get(head.id, None), relational_database.Relation) and \
                not self.relations[head.id].empty:
            logger.debug("Adding to existing relation: {}".format(head.id))
            relation = self.relations[head.id].append(relation).drop_duplicates()
        else:
            logger.debug("Creeating new relation: {}".format(head.id))

        self.relations[head.id] = relation

        logger.debug("United:\n{}".format(self.relations[head.id]))
        new_size = len(self.relations[head.id])
        logger.debug("Added {} new items".format(new_size - size))
        return bool(new_size - size)

    def __str__(self) -> str:
        """
        This is the same as printing a relational database except we will also print the passes
        :return:
        """
        manager = multiprocessing.Manager()
        results = manager.dict()
        result = "Schemes populated after {} passes through the Rules.\n".format(self.passes)
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

    arg = ArgumentParser(description="Run the datalog parser, this will produce output for lab 2")
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
        datalog = datalog_parser.DatalogProgram(tokens)
    except TokenError as t:
        print("Failure!\n  {}".format(t))
        exit(1)

    print(DatalogInterpreter(datalog))
