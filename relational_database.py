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

    def __init__(self, scheme=None, facts=None, tuples=None, name=None, schema=None):
        if scheme and facts:
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
        elif tuples and name:# and schema:
            self.name = name
            self.tuples = tuples
            self.schema = schema

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
            self.relations.append(Relation(scheme=datalog_scheme, facts=self.datalog.facts))
            pass

    def evaluate_query(self, query):
        assert isinstance(query, datalog_parser.Predicate)
        # Each query contains a set of relations
        self.RelationalDatabase[query] = set()
        relation = self.RelationalDatabase[query]
        assert isinstance(relation, set)
        # select, project, then rename
        selected = self.relations
        i = 0
        for p in query.parameterList:
            assert isinstance(p, datalog_parser.Parameter)
            if p.expression:
                print("I can't evaluate expressions yet")
            else:  # It is a string or id
                if p.string_id[TYPE] == STRING:
                    if selected[0].name:
                        selected = self.select(relations=selected, index=i, name=query.id, value=p.string_id)
            i += 1

        # Make sure relations were found before iterating over them
        if selected[0].tuples:
            for item in selected[0].tuples:
                self.RelationalDatabase[query].add(item)

    @staticmethod
    def select(relations, name, index, value):
        """
        Always do select first, it doesn't mutilate the tuples
        Return all rows that match a certain condition from the table
        """
        assert isinstance(relations, list)
        tuples = set()
        for relation in relations:
            assert isinstance(relation, Relation)
            if relation.name[VALUE] == name[VALUE]:
                for t in relation.tuples:
                    assert isinstance(t, Tuple)
                    p = t.pairs[index]
                    assert isinstance(p, Pair)
                    if p.value[VALUE] == value[VALUE]:
                        tuples.add(t)
        # TODO IDK WHAT to do with schema
        return list([Relation(tuples=tuples, name=name)])

    @staticmethod
    def project(relations):
        """
        Return (a) column(s) from the table.
        """
        return relations
        # Each fact in the Datalog Program defines a tuple in a relation.
        # The fact name identifies a relation to which the tuple belongs.

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
            tuples = self.RelationalDatabase[query]

            if not tuples:  # The set is empty
                result += "No\n"
            else:  # The set isn't empty
                result += "Yes(" + str(len(tuples)) + ")\n"
                for t in tuples:
                    result += "  " + str(t) + "\n"
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

