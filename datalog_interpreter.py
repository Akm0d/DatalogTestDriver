#!/usr/bin/env python3
from ast import literal_eval

from copy import deepcopy

from tokens import TokenError, TYPE, STRING, ID, VALUE
from collections import OrderedDict
import lexical_analyzer
import datalog_parser
import relational_database


class DatalogInterpreter:
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

    def __init__(self, rdbms, rules):
        assert isinstance(rules, datalog_parser.Rules)
        self.rules = rules.rules
        assert isinstance(rdbms, relational_database.RDBMS)
        self.rdbms = rdbms
        self.relations = rdbms.relations
        self.database = rdbms.get_database()
        assert isinstance(self.database, OrderedDict)

        self.passes = 0
        # TODO if no new relations were added then call this again and again
        # While (no new relations):
        #     self.fixed_point()
        #     self.passes += 1
        self.fixed_point()

    def fixed_point(self):
        """
        Each rule potentially adds new facts to a relation.
        The fixed-point algorithm repeatedly performs iterations on the rules adding new facts from each rule as the facts are generated.
        Each iteration may change the database by adding at least one new tuple to at least one relation in the database.
        The fixed-point algorithm terminates when an iteration of the rule expression set does not union a new tuple to any relation in the database.
        """
        for rule in self.rules:
            self.evaluate_rule(rule)

    def evaluate_rule(self, rule):
        """
        For every predicate on the right hand side of a rule,
        evaluate that predicate in the same way queries are evaluated in the previous project.
        The result of the evaluation should be a relation. If there are n predicates on the right hand side of a rule,
        then there should be n intermediate relations from each predicate.
        """
        joined = self.join(rule.head, rule.predicates)

        # DEBUG
        print("RULE: " + str(rule))
        for j in joined:
            assert isinstance(j, relational_database.Relation)
            print("SCHEME:" + j.name[1])
            print(j)
        # END DEBUG

        self.union(rule.head, joined)

    def join(self, head, predicates):
        """
        if there is a single predicate on the right hand side of the rule,
        use the single intermediate result from Step 1 as the result for Step 2.
        If there are two or more predicates on the right-hand side of a rule,
        join all the intermediate results to form the single result for Step 2.
        Thus, if p1, p2, and p3 are the intermediate results from step one;
        you should construct a relation: p1 |x| p2 |x| p3.
        :return: A list of relations
        """
        assert isinstance(head, datalog_parser.Scheme)
        assert isinstance(predicates, list)
        relations = list()
        for predicate in predicates:
            relations.extend(self.rdbms.evaluate_query(predicate))

        facts = list()
        attributes = deepcopy(head.idList)

        # TODO Make it return a single relation, not a list of relations, keep only those relations
        # whose attribute names appear in the head predicate of the new rule
        for r in relations:
            assert isinstance(r, relational_database.Relation)
            for t in r.tuples:
                assert isinstance(t, relational_database.Tuple)
                for p in t.pairs:
                    assert isinstance(p, relational_database.Pair)
                    for i, f in enumerate(attributes):
                        if p.attribute[VALUE] == f[VALUE]:
                            attributes[i] = p.value
                        if all(at[TYPE] == STRING for at in attributes):
                            facts.append(datalog_parser.Fact(name=head.id, attributes=deepcopy(attributes)))
                            attributes.clear()
                            for at in head.idList:
                                attributes.append(at)

        # TODO if part one then print out this fact
        print("FACTS")
        for f in facts:
            print(f)

        # Rename the attributes of thew new relation to match the head predicate

        # return relational_database.Relation(scheme=head, facts=facts)
        # TODO make sure the caller is expecting a single relation
        return relations

    def union(self, head, joined):
        """
        Union the results of the join with the relation in the database whose name is equal to the name of the head of
        the rule. In "join" we called this relation in the database r.
        Add tuples to relation r from the result of the join.
        :param head: A head predicate
        :param joined: Relations
        :return: A single relation
        """
        return head


def main(d_file, part=2, debug=False):
    result = ""
    if not (1 <= part <= 2):
        raise ValueError("Part must be either 1 or 2")

    if debug: result += ("Parsing '%s'" % d_file)

    # Create class objects
    tokens = lexical_analyzer.scan(d_file)

    if debug:
        datalog = datalog_parser.DatalogProgram(tokens)
    else:
        try:
            datalog = datalog_parser.DatalogProgram(tokens)
        except TokenError as t:
            return 'Failure!\n  (%s,"%s",%s)' % tuple(literal_eval(str(t)))

    # Get an initial database, we will add facts to it
    rdbms = relational_database.RDBMS(datalog)

    # Replace the original relations with the ones generated by the interpreter
    interpreter = DatalogInterpreter(rdbms, datalog.rules)
    rdbms.relations = interpreter.relations

    # After adding all the new facts,

    # Evaluate rules as we normally would

    for datalog_query in datalog.queries.queries:
        database = rdbms.get_database()
        assert isinstance(database, OrderedDict)
        for r in rdbms.evaluate_query(datalog_query):
            database[datalog_query] = set()
            if r.tuples:
                for t in r.tuples:
                    database[datalog_query].add(t)
        rdbms.set_database(database)

    for datalog_query in datalog.queries.queries:
        # Each rule returns a new relation
        rdbms.evaluate_query(datalog_query)

    # print number of passes through rules for schemes to be populated
    result += "Schemes populated after %s passes through the Rules.\n" % str(interpreter.passes)
    result += (str(rdbms))

    return result


if __name__ == "__main__":
    """
    For part 1, this will perform single select, project, and rename operations for the file provided.  
    It will select the first query in the list and use it for all 3 operations, in succession
    
    For part 2, all queries will be analyzed and a thorough output will be printed
    """
    from argparse import ArgumentParser

    args = ArgumentParser(description="Run the datalog parser, this will produce output for lab 2")
    args.add_argument('-d', '--debug', action='store_true', default=False)
    args.add_argument('-p', '--part', help='A 1 or a 2.  Defaults to 2', default=2)
    args.add_argument('file', help='datalog file to parse')
    arg = args.parse_args()

    print(main(arg.file, part=int(arg.part), debug=arg.debug))
