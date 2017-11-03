#!/usr/bin/env python3

import logging

import pandas as pd

from tokens import TokenError
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
    database = None
    relations = None
    rdbms = None
    rules = None
    passes = None

    def __init__(self, datalog_program: datalog_parser.DatalogProgram):
        super().__init__(datalog_program)
        self.rules = datalog_program.rules.rules
        self.passes = 0

    def evaluate_rules(self):
        """
        Each rule potentially adds new facts to a relation.
        The fixed-point algorithm repeatedly performs iterations on the rules adding new facts from each rule as the facts are generated.
        Each iteration may change the database by adding at least one new tuple to at least one relation in the database.
        The fixed-point algorithm terminates when an iteration of the rule expression set does not union a new tuple to any relation in the database.
        """
        self.passes += 1
        logger.debug("Pass: " + str(self.passes))
        # TODO can I evaluate each rule in it's own thread and get the same results?
        for rule in self.rules:
            joined = self.join(rule)
            if not joined.empty:
                self.union(rule.head, joined)

    def join(self, rule: datalog_parser.Rule) -> relational_database.Relation:
        """
        if there is a single predicate on the right hand side of the rule,
        use the single intermediate result from Step 1 as the result for Step 2.
        If there are two or more predicates on the right-hand side of a rule,
        join all the intermediate results to form the single result for Step 2.
        Thus, if p1, p2, and p3 are the intermediate results from step one;
        you should construct a relation: p1 |x| p2 |x| p3.
        :return: A single relation
        """
        logger.debug("Evaluating '%s'" % str(rule))
        concat = relational_database.Relation(
            pd.concat([self.evaluate_query(predicate) for predicate in rule.predicates], join='outer', axis=1)
        )

        logger.debug("Concat relation:\n{}".format(concat))
        joined = self.inner_join(concat)
        logger.debug("Joined relation:\n{}".format(joined))

        return joined.drop_duplicates()

    def union(self, head: datalog_parser.headPredicate, joined: relational_database.Relation):
        """
        Union the results of the join with the relation in the database whose name is equal to the name of the head of
        the rule. In "join" we called this relation in the database r.
        Add tuples to relation r from the result of the join.
        :param head: A head predicate
        :param joined: A relation
        :return: True if the database is now larger, False if not
        """
        logger.debug("Uniting based on '{}'".format(head))
        # print("Column values: {}".format(joined.columns.values))
        # united = joined[head.idList]
        # print(united)


if __name__ == "__main__":
    """
    For part 1, this will perform single select, project, and rename operations for the file provided.  
    It will select the first query in the list and use it for all 3 operations, in succession

    For part 2, all queries will be analyzed and a thorough output will be printed
    """
    from argparse import ArgumentParser

    arg = ArgumentParser(description="Run the datalog parser, this will produce output for lab 2")
    arg.add_argument('-d', '--debug', help="The logging debug level to use", default=logging.NOTSET, metavar='LEVEL')
    arg.add_argument('-p', '--part', help='A 1 or a 2.  Defaults to 2', default=2)
    arg.add_argument('file', help='datalog file to parse')
    args = arg.parse_args()

    logging.basicConfig(level=logging.ERROR)
    logger.setLevel(int(args.debug))

    logger.debug("Parsing '%s'" % args.file)

    # Create class objects
    tokens = lexical_analyzer.scan(args.file)

    datalog = None
    if args.debug:
        datalog = datalog_parser.DatalogProgram(tokens)
    else:
        try:
            datalog = datalog_parser.DatalogProgram(tokens)
        except TokenError as t:
            print('Failure!\n  {}'.format(t))
            exit(1)

    assert isinstance(datalog, datalog_parser.DatalogProgram)
    main_interpreter = DatalogInterpreter(datalog)

    # TODO Call this from __init__?
    main_interpreter.evaluate_rules()

"""
    # Get an initial database, we will add facts to it
    rdbms = relational_database.RDBMS(datalog)

    # Replace the original relations with the ones generated by the interpreter
    interpreter = DatalogInterpreter(rdbms, datalog.rules)
    # if no new relations were added then call this again and again
    # print out which pass we are on if this is part 1
    # This is the fixed point algorithm
    interpreter.evaluate_rules()
    rdbms.relations = interpreter.relations
    before = ""
    after = rdbms.evaluate_queries(datalog.queries.queries)
    while before != after:
        before = after
        interpreter.evaluate_rules()
        after = rdbms.evaluate_queries(datalog.queries.queries)
        rdbms.relations = interpreter.relations

    # After adding all the new facts,
    result += "Schemes populated after %s passes through the Rules.\n" % str(interpreter.passes)

    # Evaluate rules as we normally would
    result += rdbms.evaluate_queries(datalog.queries.queries)

    return result
    """
