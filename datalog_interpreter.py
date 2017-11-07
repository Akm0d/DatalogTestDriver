#!/usr/bin/env python3

import logging

import pandas as pd
from tokens import TokenError, Token
import lexical_analyzer
import datalog_parser
import relational_database

logger = logging.getLogger(__name__)


class DatalogInterpreter(relational_database.RDBMS):
    """
    The most direct way to evaluate a rule is to use the mental model of an expression tree.
    Each predicate in the rule is evaluated as a query to return a relation.
    That relation returned by the predicate is then natural joined with the relations for other predicates in the rule.
    This process is best understood as a simple traversal of the rule, evaluating each predicate as a query,
    and then gathering the results with a natural join.
    """
    merge_token = Token(-1)
    database = None
    relations = None
    rdbms = None
    rules = None
    passes = None

    def __init__(self, datalog_program: datalog_parser.DatalogProgram):
        super().__init__(datalog_program)
        self.rules = datalog_program.rules.rules
        self.passes = 1
        logger.info("Evaluating Rules")
        while self.evaluate_rules():
            self.passes += 1
        logger.info("Evaluating Queries")
        for query in datalog_program.queries.queries:
            self.rdbms[query] = self.evaluate_query(query)

    def evaluate_rules(self) -> bool:
        """
        Each rule potentially adds new facts to a relation.
        The fixed-point algorithm repeatedly performs iterations on the rules adding new facts from each rule as the facts are generated.
        Each iteration may change the database by adding at least one new tuple to at least one relation in the database.
        The fixed-point algorithm terminates when an iteration of the rule expression set does not union a new tuple to any relation in the database.
        """
        change = False
        logger.debug("Pass: " + str(self.passes))
        # TODO can I evaluate each rule in it's own thread and get the same results?
        for rule in self.rules:
            joined = self.join(rule)
            if not joined.empty:
                change |= self.union(rule.head, joined)
                logger.debug("Yay change" if change else "Nothing changed")
        return change

    def join(self, rule: datalog_parser.Rule) -> relational_database.Relation:
        """
        if there is a single predicate on the right hand side of the rule,
        use the single intermediate result from Step 1 as the result for Step 2.
        If there are two or more predicates on the right-hand side of a rule,
        join all the intermediate results to form the single result for Step 2.
        Thus, if p1, p2, and p3 are the intermediate results from step one;
        you should construct a relation: p1 |x| p2 |x| p3.
        :return:
        """
        logger.debug("Evaluating '%s'" % str(rule))
        relations = [self.evaluate_query(predicate) for predicate in rule.predicates]

        relation = relations.pop()
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
        size = len(self.relations[head.id])
        relation = relation[[x for x in head.idList]]
        logger.debug("Project:\n{}".format(relation))

        relation.columns = range(relation.shape[1])
        if isinstance(self.relations[head.id], relational_database.Relation):
            logger.debug("Adding to existing relation: {}".format(head.id))
            self.relations[head.id] = self.relations[head.id].append(relation).drop_duplicates()
        else:
            logger.debug("Creeating new relation: {}".format(head.id))
            self.relations[head.id] = relation

        logger.debug("United:\n{}".format(self.relations[head.id]))
        new_size = len(self.relations[head.id])
        logger.debug("Added {} new items".format(new_size - size))
        return bool(new_size - size)

    def __str__(self)->str:
        """
        This is the same as printing a relational database except we will also print the passes
        :return:
        """
        result = "Schemes populated after {} passes through the Rules.\n".format(self.passes)
        for query in self.rdbms.keys():
            result += str(query) + "? "

            if self.rdbms[query] is relational_database.SINGLE_MATCH:
                result += "Yes(1)\n"
            elif self.rdbms[query] is None or self.rdbms[query].empty:
                result += "No\n"
            else:
                result += "Yes({})\n{}\n".format(len(self.rdbms[query]), self.print_relation(self.rdbms[query]))
        return result


if __name__ == "__main__":
    from argparse import ArgumentParser

    arg = ArgumentParser(description="Run the datalog parser, this will produce output for lab 2")
    arg.add_argument('-d', '--debug', help="The logging debug level to use", default=logging.NOTSET, metavar='LEVEL')
    arg.add_argument('file', help='datalog file to parse')
    args = arg.parse_args()

    logging.basicConfig(level=logging.ERROR)
    logger.setLevel(int(args.debug))

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
