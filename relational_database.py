#!/usr/bin/env python3
from collections import OrderedDict
from copy import deepcopy
from itertools import zip_longest
from orderedset._orderedset import OrderedSet
from tokens import VALUE, STRING, TYPE

import lexical_analyzer
import datalog_parser


class Pair:
    """
    The format of a pair is v= 's', where v is the variable and 's' is the string value. 
    """
    # An attribute is the name associated with each data value in a tuple entry.
    attribute = None
    value = None

    def __init__(self, v, s):
        self.attribute = v
        self.value = s

    def __str__(self):
        return "%s=%s" % (self.attribute[VALUE], self.value[VALUE])

    def __hash__(self):
        return hash(str(self))


class Tuple:
    """
    A Tuple is a set of attribute/value pairs.
    """
    pairs = None

    def __init__(self):
        self.pairs = OrderedSet()

    def add(self, pair):
        assert isinstance(pair, Pair)
        self.pairs.add(pair)

    def __str__(self):
        return ", ".join(str(pair) for pair in self.pairs)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return str(self) == str(other)

    def __ne__(self, other):
        return str(self) != str(other)

    def __lt__(self, other):
        return str(self) < str(other)

    def __le__(self, other):
        return str(self) <= str(other)

    def __ge__(self, other):
        return str(self) >= str(other)

    def __gt__(self, other):
        return str(self) > str(other)


class Relation:
    """
    Each scheme in a Datalog Program defines a relation in the Database.
    The scheme defines the name of the relation. 
    The attribute list of the scheme defines the schema of the relation. 
    Each relation has a name, a schema, and a set of tuples. A schema is a set of attributes. 
    """
    name = None
    # A schema is a set of attributes.
    schema = None
    # A tuple is a set of attribute/value pairs.
    tuples = None

    def __init__(self, scheme, facts):
        assert isinstance(scheme, datalog_parser.Scheme)
        self.name = scheme.id
        self.schema = set(scheme.idList)
        assert isinstance(facts, datalog_parser.Facts)
        self.tuples = set()
        for fact in facts.facts:
            if fact.id[VALUE] == scheme.id[VALUE]:
                # Create a new tuple
                new_tuple = Tuple()

                # Iterate over both lists in parallel
                # If one list is longer than the other, then fill the shorter list with None types
                for attribute, value in zip_longest(scheme.idList, fact.stringList, fillvalue=None):
                    # add pairs to the tuple
                    new_tuple.add(Pair(attribute, value))
                    # Add the full tuple to our set
                self.tuples.add(new_tuple)

    def __str__(self):
        """
        Sort the tuples alphabetically based on string values in the tuples' variables 
        (sort with the first sort key as the first variable (in order of appearance in the query),
        the second sort key as the second variable, and so on). 
        """
        result = ""
        tuples = sorted(self.tuples)
        for thing in tuples:
            result += str(thing) + "\n"
        return result

    def __hash__(self):
        return hash(str(self))


class RDBMS:
    """
    The basic data structure is a database consisting of relations, each with their own name, schema, and set of tuples.
    A relational database management system (RDBMS) maintains data sets called relations.
    This builds a relational database system from a Datalog file, and then answers queries using relational algebra. 
    """
    # A query mapped to a set of relations
    # This will be shared amongst all instances of this class
    RelationalDatabase = OrderedDict()
    relations = None
    datalog = None

    def __init__(self, datalog_program):
        self.relations = list()
        assert isinstance(datalog_program, datalog_parser.DatalogProgram)
        self.datalog = datalog_program
        for datalog_scheme in self.datalog.schemes.schemes:
            self.relations.append(Relation(datalog_scheme, self.datalog.facts))
            pass

    def evaluate_query(self, query):
        # Each query contains a set of relations
        self.RelationalDatabase[query] = set()
        relation = self.RelationalDatabase[query]
        assert isinstance(relation, set)
        # select, project, then rename
        print("Evaluating " + str(query))  # TODO REMOVE PRINT
        selected = self.select(self.relations, query)
        for database_relation in selected:
            print("NAME: " + str(database_relation.name[VALUE]))
            print("SCHEMA: " + str(database_relation.schema))
            print("STRING: \n" + str(database_relation))
            print("-" * 80)

    @staticmethod
    def select(relations, query):
        """
        Always do select first, it doesn't mutilate the tuples
        Return all rows that match a certain condition from the table
        """
        assert isinstance(query, datalog_parser.Predicate)
        tuples = set()
        i = 0
        for parameter in query.parameterList:
            if parameter.expression:
                print("I can't handle expressions yet")
            else: # We are dealing with a string or id
                if parameter.string_id[TYPE] == STRING:
                    for relation in relations:
                        if relation.name[VALUE] == query.id[VALUE]:
                            for t in relation.tuples:
                                assert isinstance(t, Tuple)
                                p = t.pairs[i]
                                assert isinstance(p, Pair)
                                if p.value[VALUE] == parameter.string_id[VALUE]:
                                    print(str(t))
                                    tuples.add(t)
            i += 1
        return relations

    @staticmethod
    def project(relations):
        """
        Return (a) column(s) from the table.
        """
        return relations

    @staticmethod
    def rename(relations):
        """
        Always rename all columns at the same time, that way if A,B is being renamed to B,A you don't end up with B,B
        Return a table with the specified columns renamed
        """
        return relations

    def __str__(self):
        """
        For each query, print the query and a space. 
        Then, if the query's resulting relation is empty, output “No”; and if the resulting relation is not empty, 
        output “Yes(n)” where n is the number of tuples in the resulting relation. 
        If there are free variables in the query, print the tuples of the resulting relation, 
        one per line and indented by two spaces, according to the following directions.
        """
        result = ""
        for query in self.RelationalDatabase.keys():
            result += str(query) + "? "
            relations = self.RelationalDatabase[query]
            if not relations:  # The set is empty
                result += "No\n"
            else:  # The set isn't empty
                result += "Yes(" + str(len(relations)) + ")\n"
                for relation in relations:
                    result += "  " + str(relation) + "\n"
        return result.rstrip("\n")


if __name__ == "__main__":
    from argparse import ArgumentParser

    args = ArgumentParser(description="Run the datalog parser, this will produce output for lab 2")
    args.add_argument('-d', '--debug', action='store_true', default=False)
    args.add_argument('-p', '--part', help='A 1 or a 2.  Defaults to 2', default=2)
    args.add_argument('file', help='datalog file to parse')
    arg = args.parse_args()

    debug = arg.debug
    d_file = arg.file
    part = int(arg.part)

    if not (1 <= part <= 2):
        raise ValueError("Part must be either 1 or 2")

    if debug: print("Parsing '%s'" % d_file)

    # Create class objects
    tokens = lexical_analyzer.scan(d_file)
    datalog = datalog_parser.DatalogProgram(tokens)

    rdbms = RDBMS(datalog)

    for datalog_query in datalog.queries.queries:
        rdbms.evaluate_query(datalog_query)

    if part == 1:
        # TODO perform a single project, select, and rename on the input file, one at a time
        # print out something helpful, not what they say to print out, that's lame
        print("Part 1 hasn't yet been implemented")
    else:
        print(str(rdbms))

        # Each fact in the Datalog Program defines a tuple in a relation.
        # The fact name identifies a relation to which the tuple belongs.

    print("\nRELATIONS\n" + "-" * 80)
    for database_relation in rdbms.relations:
        print("NAME: " + str(database_relation.name[VALUE]))
        print("SCHEMA: " + str(database_relation.schema))
        print("STRING: \n" + str(database_relation))
        print("-" * 80)
