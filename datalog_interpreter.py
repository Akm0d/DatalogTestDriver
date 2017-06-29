#!/usr/bin/env python3
from ast import literal_eval
from collections import OrderedDict
from copy import deepcopy
from tokens import TokenError, TYPE, STRING, ID, VALUE

import lexical_analyzer
import datalog_parser
import relational_database

# If part is 1 then more steps will be printed
_part = 2


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
        # if no new relations were added then call this again and again
        # print out which pass we are on if this is part 1
        # This is the fixed point algorithm
        before = -1
        after = sum([len(x.tuples) for x in self.relations])
        # TODO keep going based on whether the queries return any new data
        while before < after:
            before = after
            self.evaluate_rules()
            after = sum([len(x.tuples) for x in self.relations])

    def evaluate_rules(self):
        """
        Each rule potentially adds new facts to a relation.
        The fixed-point algorithm repeatedly performs iterations on the rules adding new facts from each rule as the facts are generated.
        Each iteration may change the database by adding at least one new tuple to at least one relation in the database.
        The fixed-point algorithm terminates when an iteration of the rule expression set does not union a new tuple to any relation in the database.
        """
        self.passes += 1
        if _part == 1:
            print("Pass: " + str(self.passes))
        for rule in self.rules:
            joined = self.join(rule)
            if joined.tuples:
                self.union(rule.head, joined)

    def join(self, rule):
        """
        if there is a single predicate on the right hand side of the rule,
        use the single intermediate result from Step 1 as the result for Step 2.
        If there are two or more predicates on the right-hand side of a rule,
        join all the intermediate results to form the single result for Step 2.
        Thus, if p1, p2, and p3 are the intermediate results from step one;
        you should construct a relation: p1 |x| p2 |x| p3.
        :return: A list of relations
        """
        assert isinstance(rule, datalog_parser.Rule)
        tuples = set()
        # print("Evaluating '%s'" % str(rule))
        for predicate in rule.predicates:
            rels = self.rdbms.evaluate_query(predicate)
            for r in rels:
                assert isinstance(r, relational_database.Relation)
                for x in r.tuples:
                    # print("T: " + str(x))
                    tuples.add(x)

        from itertools import combinations
        s_t_combined = set()
        for x in combinations(tuples, len(rule.predicates)):
            t_combined = relational_database.Tuple()
            for p in x:
                # print("p: "+ str(p) )
                t_combined.union(p.pairs)
            if t_combined:
                s_t_combined.add(t_combined)

        # print("combined")
        # print("\n".join([str(x) for x in s_t_combined]))

        relation = relational_database.Relation()
        relation.tuples.clear()
        relation.name = rule.head.id
        relation.tuples = self.t_reorder_and_select(rule.head.idList, s_t_combined)

        # If this is part one then print out info from this intermediary step
        if _part == 1:
            print("Joining %s" % str(rule))
            print("\n".join([str(x) for x in tuples]))
            print("Result:")
            print(relation)

        return relation

    @staticmethod
    def t_reorder_and_select(schema, tuples):
        good_tuples = set()
        # print(schema)
        # print("\n".join([str(x) for x in tuples]))
        for t in tuples:
            new_tuple = relational_database.Tuple()
            valid = True
            for i in schema:
                new_pair = t.get(i)
                if new_pair:
                    new_tuple.add(new_pair)
                else:
                    valid = False
            if valid:
                good_tuples.add(new_tuple)
        return good_tuples

    @staticmethod
    def join_relations(r1, r2):
        print("Adding %s to %s" % ("\n".join([str(x) for x in r1]), "\n".join([str(y) for y in r2])))
        tuples = set()
        for t1 in r1:
            for t2 in r2:
                print("concatenating %s with %s" % (str(t1), str(t2)))
                new_tuple = relational_database.Tuple()
                for p in t2.pairs:
                    new_tuple.add(p)
                for p in t1.pairs:
                    new_tuple.add(p)
                if new_tuple.pairs:
                    tuples.add(new_tuple)

        print("TUPLES ARE NOW:")
        for t in tuples:
            print(t)
        return tuples

    def union(self, head, joined):
        """
        Union the results of the join with the relation in the database whose name is equal to the name of the head of
        the rule. In "join" we called this relation in the database r.
        Add tuples to relation r from the result of the join.
        :param head: A head predicate
        :param joined: Relations
        :return: True if the database is now larger, False if not
        """
        if head.id[VALUE] not in [x.name[VALUE] for x in self.relations]:
            self.relations.append(joined)
            new_values = True
        else:
            for r in self.relations:
                if r.name[VALUE] == head.id[VALUE]:
                    assert isinstance(r, relational_database.Relation)
                    for t in joined.tuples:
                        r.tuples.add(t)


def main(d_file, part=2, debug=False):
    global _part
    _part = part
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
        if datalog_query not in database:
            database[datalog_query] = set()
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
