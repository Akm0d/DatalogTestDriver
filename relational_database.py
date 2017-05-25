#!/usr/bin/env python3
from collections import OrderedDict
from tokens import VALUE
import lexical_analyzer
import datalog_parser


class Pair:
    """
     The format of a pair is v= 's', where v is the variable and 's' is the string value. 
    """
    # An ID
    variable = None
    # A string
    value = None

    def __init__(self, id, string):
        self.variable = id
        self.value = string

    def __str__(self):
        return "%s='%s'" % (self.variable[VALUE], self.value[VALUE])


class Relation:
    """
     A tuple-like list of pairs.  A list of these will be mapped to a query
    """
    pairs = None

    def __init__(self):
        self.pairs = list()

    def append(self, pair):
        self.pairs.append(pair)

    def __str__(self):
        result = ""
        for pair in self.pairs:
            result += str(pair)
        return ", ".join(map(str, self.pairs))

    def __hash__(self):
        """
        Sort the tuples alphabetically based on string values in the tuples' variables 
        (sort with the first sort key as the first variable (in order of appearance in the query),
        the second sort key as the second variable, and so on). 
        """
        return hash(str(self))


class RDBMS:
    """
    A relational Database Management system that can add Relations to a query
    """
    # A query mapped to a set of relations
    # This will be shared amongst all instances of this class
    RelationalDatabase = OrderedDict()

    # A copy of the datalog program that we can manipulate for this query
    # This will be unique each time the class is created
    datalog = None

    def __init__(self, datalog_program, query):
        # Manipulate this datalog_program object so that we find all relations that match the query
        self.datalog = datalog_program
        # Each query contains a set of relations
        self.RelationalDatabase[query] = set([])

    def select(self):
        pass

    def project(self):
        pass

    def rename(self):
        pass

    def __str__(self):
        return ""


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

    rdbms = None
    for query_object in datalog.queries.queries:
        rdbms = RDBMS(datalog, query_object)

