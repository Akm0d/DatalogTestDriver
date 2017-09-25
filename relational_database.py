#!/usr/bin/env python3
from collections import OrderedDict
from itertools import zip_longest, combinations
from orderedset._orderedset import OrderedSet
from tokens import TokenType, TokenError, Token

import logging
import lexical_analyzer
import datalog_parser

logger = logging.getLogger(__name__)


class Pair(tuple):
    """
    The format of a pair is v= 's', where v is the variable and 's' is the string value. 
    """

    def __new__(cls, v: Token = None, s: Token = None):
        cls.hash_value = hash(v.value if v else '' + s.value if v else '')
        return tuple.__new__(cls, (v, s))

    @property
    def attribute(self):
        return self[0]

    @property
    def value(self):
        return self[1]

    def __str__(self):
        return "{}={}".format(
            self.attribute.value if self.attribute else None, self.value.value if self.value else None
        )

    def __hash__(self):
        return self.hash_value

    def __eq__(self, other):
        return str(self) == str(other)

    def __ne__(self, other):
        return str(self) != str(other)


class Tuple(OrderedSet):
    """
    A Tuple is a set of attribute/value pairs.
    """

    def __init__(self):
        super().__init__()
        self.hash_value = hash(str(self))

    def union(self, other):
        for pair in other:
            self.add(Pair(pair.attribute, pair.value))
        self.hash_value = hash(str(self))

    def get(self, attribute: Token):
        """
        :param attribute:
        :return: The pair that has the given attribute
        """
        for pair in self:
            if pair.attribute.value == attribute.value:
                return pair
        return None

    def __bool__(self):
        if not len(self):
            return False
        for x, y in combinations(self, 2):
            if x.attribute.value == y.attribute.value:
                return False
        return True

    def __str__(self):
        return ", ".join(str(pair) for pair in self)

    def __hash__(self):
        return self.hash_value

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

    def __init__(self,
                 scheme: datalog_parser.Scheme = None, facts: datalog_parser.Facts = None, tuples: set = None,
                 name: Token = None, schema: set = None):
        if scheme and facts:
            self.name = scheme.id
            # A schema is a set of attributes.
            self.schema = set(scheme.idList)
            # A tuple is a set of attribute/value pairs.
            self.tuples = set()
            for fact in facts.facts:
                if fact.id.value == scheme.id.value:
                    # Create a new tuple
                    new_tuple = Tuple()

                    # Iterate over both lists in parallel
                    # If one list is longer than the other, then fill the shorter list with None types
                    for attribute, value in zip_longest(scheme.idList, fact.stringList, fillvalue=None):
                        # add pairs to the tuple
                        new_tuple.add(Pair(attribute, value))
                        # Add the full tuple to our set
                    self.tuples.add(new_tuple)
        elif tuples and name:  # and schema:
            self.name = name
            self.tuples = tuples
            self.schema = schema
        else:
            self.tuples = set()
            self.schema = set()
            self.name = Token(0)

    def __str__(self):
        """
        Sort the tuples alphabetically based on string values in the tuples' variables 
        (sort with the first sort key as the first variable (in order of appearance in the query),
        the second sort key as the second variable, and so on). 
        """
        result = ""
        if self.tuples:
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

    def __init__(self, datalog_program: datalog_parser.DatalogProgram, rdbms: OrderedDict = None):
        if rdbms is None:
            self.rdbms = OrderedDict()
        else:
            self.rdbms = rdbms
        self.relations = list()
        assert isinstance(datalog_program, datalog_parser.DatalogProgram)
        self.datalog = datalog_program
        for datalog_scheme in self.datalog.schemes.schemes:
            self.relations.append(Relation(scheme=datalog_scheme, facts=self.datalog.facts))
            pass

    def evaluate_query(self, query: datalog_parser.Query):
        # select, project, then rename
        logger.debug("Evaluating query: {}?".format(query))
        selected = self.relations
        logger.debug("Relations:\n{}".format(selected[0]))
        project_columns = list()
        new_names = list()
        i = 0
        # Perform the select operation
        for p in query.parameterList:
            assert isinstance(p, datalog_parser.Parameter)
            if p.expression:
                logger.warning("Expressions cannot be handled yet")
            else:  # It is a string or id
                if p.string_id.type == TokenType.STRING:
                    logger.debug("Selecting {} in column {}".format(p.string_id.value, i))
                    if selected and selected[0].name:
                        selected = self.select(relations=selected, index=i, name=query.id, value=p.string_id)
                        if selected and selected[0].name:
                            logger.debug("Selected:\n{}".format(selected[0]))
                elif p.string_id.type == TokenType.ID:
                    project_columns.append(i)
                    new_names.append(p.string_id)
            i += 1

        # Make sure relations were found before iterating over them
        if not (selected and selected[0].name):
            logger.debug("No relations after selecting")
        projected = self.project(selected, query.id, project_columns)
        if projected and projected[0].name:
            logger.debug("Projected: {}\n{}".format(
                ",".join([str(i) for i in project_columns]), projected[0])
            )
        else:
            logger.debug("No relations after projecting")
        renamed = self.rename(projected, query.id, new_names)
        if renamed and renamed[0].name:
            logger.debug("Renamed:\n{}".format(renamed[0]))
        else:
            logger.debug("No relations after renaming")
        return renamed

    @staticmethod
    def select(relations: list, name: Token, index: int, value: Token):
        """
        Always do select first, it doesn't mutilate the tuples
        Return all rows that match a certain condition from the table
        """
        result = list()
        for relation in relations:
            tuples = set()
            assert isinstance(relation, Relation)
            if relation.name.value == name.value:
                for t in relation.tuples:
                    assert isinstance(t, Tuple)
                    p = t[index]
                    assert isinstance(p, Pair)
                    if p.value.value == value.value:
                        tuples.add(t)
            if tuples:
                result.append(Relation(tuples=tuples, name=name))
        return result

    @staticmethod
    def project(relations: list, name: Token, columns: list):
        """
        :param relations: 
        :param name: The table/scheme id
        :param columns: a list of indices of IDs in a query
        :return: A relation with only the specified columns from the table.
        """
        assert isinstance(relations, list)
        result = list()
        for relation in relations:
            tuples = set()
            assert isinstance(relation, Relation)
            if relation.name.value == name.value:
                for t in relation.tuples:
                    assert isinstance(t, Tuple)
                    new_t = Tuple()
                    i = 0
                    for p in t:
                        if i in columns:
                            new_t.add(p)
                        i += 1
                    tuples.add(new_t)
            if tuples:
                result.append(Relation(tuples=tuples, name=name))
        return result

    @staticmethod
    def rename(relations: list, name: Token, new_names: list):
        """
        Always rename all columns at the same time, that way if A,B is being renamed to B,A you don't end up with B,B
        Return a table with the specified columns renamed
        :param relations: 
        :param name: The table/scheme id
        :param new_names: a list of IDs that will be the new names for the all columns
        :return: A relation with columns renamed to the new_names
        """
        result = list()
        for relation in relations:
            tuples = set()
            assert isinstance(relation, Relation)
            if relation.name.value == name.value:
                for t in relation.tuples:
                    assert isinstance(t, Tuple)
                    new_t = Tuple()
                    # Iterate over the pairs and new names
                    for p, n in zip_longest(t, new_names, fillvalue=None):
                        if not p:
                            p = Pair(None, None)
                        new_t.add(Pair(n, p.value))

                    # If pairs in the tuple have the same ID but not the same value then the tuple is invalid
                    valid = True
                    for p in new_t:
                        assert isinstance(p, Pair)
                        # Iterate over the same list twice and make sure all pairs with the same ID have same value
                        for o in new_t:
                            assert isinstance(o, Pair)
                            if p.attribute == o.attribute and not (p.value == o.value):
                                valid = False
                    if valid:
                        tuples.add(new_t)
            if tuples:
                result.append(Relation(tuples=tuples, name=name))
        return result

    def __str__(self):
        """
        For each query, print the query and a space. 
        Then, if the query's resulting relation is empty, output “No”; and if the resulting relation is not empty, 
        output “Yes(n)” where n is the number of tuples in the resulting relation. 
        If there are free variables in the query, print the tuples of the resulting relation,
        one per line and indented by two spaces, according to the following directions.
        """
        result = ""
        for query in self.rdbms.keys():
            result += str(query) + "? "
            tuples = self.rdbms[query]

            if not tuples:  # The set is empty
                result += "No\n"
            else:  # The set isn't empty
                result += "Yes(" + str(len(tuples)) + ")"
                assert isinstance(tuples, set)
                if next(iter(tuples)):
                    result += "\n"
                for t in sorted(tuples):
                    result += "  " + str(t) + "\n"
                # Remove whitespace after line
                result = result.rstrip(' \t\n\r') + "\n"
        return result

    def evaluate_queries(self, queries: datalog_parser.Queries):
        for datalog_query in queries.queries:
            database = self.rdbms
            assert isinstance(database, OrderedDict)
            if datalog_query not in database:
                database[datalog_query] = set()

            for r in self.evaluate_query(datalog_query):
                if r.tuples:
                    for t in r.tuples:
                        database[datalog_query].add(t)
            self.rdbms = database

        for datalog_query in queries.queries:
            # Each rule returns a new relation
            self.evaluate_query(datalog_query)

        # print number of passes through rules for schemes to be populated
        return str(self)


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

    if args.debug:
        datalog = datalog_parser.DatalogProgram(tokens)
    else:
        try:
            datalog = datalog_parser.DatalogProgram(tokens)
        except TokenError as t:
            print('Failure!\n  {}'.format(t))

    relations = OrderedDict()
    rdbms = RDBMS(datalog, rdbms=relations)

    for datalog_query in datalog.queries.queries:
        relations[datalog_query] = set()
        for r in rdbms.evaluate_query(datalog_query):
            if r.tuples:
                for t in r.tuples:
                    relations[datalog_query].add(t)

    print(str(rdbms))
