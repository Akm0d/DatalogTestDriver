#!/usr/bin/env python3
from ast import literal_eval
from collections import OrderedDict
from itertools import zip_longest
from orderedset._orderedset import OrderedSet
from tokens import VALUE, STRING, TYPE, ID, TokenError

import lexical_analyzer
import datalog_parser

# An ordered dictionary for storing all the query values
RelationalDatabase = None


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
        value = self.value[VALUE] if self.value else "NULL"
        attribute = self.attribute[VALUE] if self.attribute else "NULL"
        return "%s=%s" % (attribute, value)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return str(self) == str(other)

    def __ne__(self, other):
        return str(self) != str(other)


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
            assert isinstance(facts, list)
            self.tuples = set()
            for fact in facts:
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
        elif tuples and name:  # and schema:
            self.name = name
            self.tuples = tuples
            self.schema = schema
        else:
            self.tuples = set()
            self.schema = set()
            self.name = ("", "", "")

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
    # A query mapped to a set of relations
    # This will be shared amongst all instances of this class
    relations = None
    datalog = None

    def __init__(self, datalog_program):
        global RelationalDatabase
        if not RelationalDatabase:
            RelationalDatabase = OrderedDict()
        self.relations = list()
        assert isinstance(datalog_program, datalog_parser.DatalogProgram)
        self.datalog = datalog_program
        for datalog_scheme in self.datalog.schemes.schemes:
            self.relations.append(Relation(scheme=datalog_scheme, facts=self.datalog.facts.facts))
            pass

    def evaluate_query(self, query):
        assert isinstance(query, datalog_parser.Predicate)
        # select, project, then rename
        selected = self.relations
        project_columns = list()
        new_names = list()
        i = 0
        # Perform the select operation
        for p in query.parameterList:
            assert isinstance(p, datalog_parser.Parameter)
            if p.expression:
                print("I can't evaluate expressions yet")
            else:  # It is a string or id
                if p.string_id[TYPE] == STRING:
                    if selected and selected[0].name:
                        selected = self.select(relations=selected, index=i, name=query.id, value=p.string_id)
                elif p.string_id[TYPE] == ID:
                    project_columns.append(i)
                    new_names.append(p.string_id)
            i += 1

        # Make sure relations were found before iterating over them
        projected = self.project(selected, query.id, project_columns)
        renamed = self.rename(projected, query.id, new_names)
        return renamed

    @staticmethod
    def select(relations, name, index, value):
        """
        Always do select first, it doesn't mutilate the tuples
        Return all rows that match a certain condition from the table
        """
        assert isinstance(relations, list)
        result = list()
        for relation in relations:
            tuples = set()
            assert isinstance(relation, Relation)
            if relation.name[VALUE] == name[VALUE]:
                for t in relation.tuples:
                    assert isinstance(t, Tuple)
                    p = t.pairs[index]
                    assert isinstance(p, Pair)
                    if p.value[VALUE] == value[VALUE]:
                        tuples.add(t)
            if tuples:
                result.append(Relation(tuples=tuples, name=name))
        return result

    @staticmethod
    def project(relations, name, columns):
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
            if relation.name[VALUE] == name[VALUE]:
                for t in relation.tuples:
                    assert isinstance(t, Tuple)
                    new_t = Tuple()
                    i = 0
                    for p in t.pairs:
                        if i in columns:
                            new_t.add(p)
                        i += 1
                    tuples.add(new_t)
            if tuples:
                result.append(Relation(tuples=tuples, name=name))
        return result

    @staticmethod
    def rename(relations, name, new_names):
        """
        Always rename all columns at the same time, that way if A,B is being renamed to B,A you don't end up with B,B
        Return a table with the specified columns renamed
        :param relations: 
        :param name: The table/scheme id
        :param new_names: a list of IDs that will be the new names for the all columns
        :return: A relation with columns renamed to the new_names
        """
        assert isinstance(relations, list)
        result = list()
        for relation in relations:
            tuples = set()
            assert isinstance(relation, Relation)
            if relation.name[VALUE] == name[VALUE]:
                for t in relation.tuples:
                    assert isinstance(t, Tuple)
                    new_t = Tuple()
                    # Iterate over the pairs and new names
                    for p, n in zip_longest(t.pairs, new_names, fillvalue=None):
                        if not p:
                            p = Pair(None, None)
                        new_t.add(Pair(n, p.value))

                    # If pairs in the tuple have the same ID but not the same value then the tuple is invalid
                    valid = True
                    for p in new_t.pairs:
                        assert isinstance(p, Pair)
                        # Iterate over the same list twice and make sure all pairs with the same ID have same value
                        for o in new_t.pairs:
                            assert isinstance(o, Pair)
                            if p.attribute == o.attribute and not (p.value == o.value):
                                valid = False
                    if valid:
                        tuples.add(new_t)
            if tuples:
                result.append(Relation(tuples=tuples, name=name))
        return result

    @staticmethod
    def get_database():
        global RelationalDatabase
        if not RelationalDatabase:
            RelationalDatabase = OrderedDict()
        return RelationalDatabase

    def __str__(self):
        """
        For each query, print the query and a space. 
        Then, if the query's resulting relation is empty, output “No”; and if the resulting relation is not empty, 
        output “Yes(n)” where n is the number of tuples in the resulting relation. 
        If there are free variables in the query, print the tuples of the resulting relation,
        one per line and indented by two spaces, according to the following directions.
        """
        result = ""
        for query in RelationalDatabase.keys():
            result += str(query) + "? "
            tuples = RelationalDatabase[query]

            if not tuples:  # The set is empty
                result += "No\n"
            else:  # The set isn't empty
                result += "Yes(" + str(len(tuples)) + ")"
                assert isinstance(tuples, set)
                if next(iter(tuples)).pairs:
                    result += "\n"
                for t in sorted(tuples):
                    result += "  " + str(t) + "\n"
                # Remove whitespace after line
                result = result.rstrip(' \t\n\r') + "\n"
        return result

    @staticmethod
    def set_database(database):
        global RelationalDatabase
        RelationalDatabase = database


def main(d_file, part=2, debug=False):
    global RelationalDatabase
    if not RelationalDatabase:
        RelationalDatabase = OrderedDict()
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

    rdbms = RDBMS(datalog)

    for datalog_query in datalog.queries.queries:
        for r in rdbms.evaluate_query(datalog_query):
            # Each query contains a set of relations
            if datalog_query not in RelationalDatabase:
                RelationalDatabase[datalog_query] = set()
            if r.tuples:
                for t in r.tuples:
                    RelationalDatabase[datalog_query].add(t)

    if part == 1:
        # This is the same thing that comes from evaluate queries, but we are going to stop at each point and print
        one_query = datalog.queries.queries[0]
        assert isinstance(one_query, datalog_parser.Predicate)
        # Each query contains a set of relations
        RelationalDatabase[one_query] = set()
        relation = RelationalDatabase[one_query]
        assert isinstance(relation, set)
        # select, project, then rename
        one_selected = rdbms.relations
        one_project_columns = list()
        one_new_names = list()
        one_i = 0
        # Perform the select operation
        for p in one_query.parameterList:
            assert isinstance(p, datalog_parser.Parameter)
            if p.expression:
                result += "I can't evaluate expressions yet\n"
            else:  # It is a string or id
                if p.string_id[TYPE] == STRING:
                    if one_selected and one_selected[0].name:
                        one_selected = rdbms.select(relations=one_selected, index=one_i, name=one_query.id,
                                                    value=p.string_id)
                elif p.string_id[TYPE] == ID:
                    one_project_columns.append(one_i)
                    one_new_names.append(p.string_id)
            one_i += 1

        # Print original database
        result += (str(one_query) + "? ")
        if rdbms.relations:
            result += ("Yes(" + str(len(rdbms.relations[0].tuples)) + ")\n")
            for r in sorted(rdbms.relations[0].tuples):
                result += ("  " + str(r)) + "\n"
        else:
            result += "No"

        # Print after select
        result += "AFTER SELECT\n"
        result += (str(one_query) + "? ")
        if one_selected:
            result += ("Yes(" + str(len(one_selected[0].tuples)) + ")\n")
            for r in sorted(one_selected[0].tuples):
                result += ("  " + str(r)) + "\n"
        else:
            result += "No"

        # Print after project
        result += "AFTER PROJECT\n"
        result += (str(one_query) + "? ")
        one_projected = rdbms.project(one_selected, one_query.id, one_project_columns)
        if one_projected:
            result += ("Yes(" + str(len(one_projected[0].tuples)) + ")\n")
            for r in sorted(one_projected[0].tuples):
                result += ("  " + str(r)) + "\n"
        else:
            result += "No"

        # Print after rename
        result += "AFTER RENAME\n"
        result += (str(one_query) + "? ")
        one_renamed = rdbms.rename(one_projected, one_query.id, one_new_names)
        one_renamed = rdbms.project(one_renamed, one_query.id, one_project_columns)
        if one_renamed:
            result += ("Yes(" + str(len(one_renamed[0].tuples)) + ")\n")
            for r in sorted(one_renamed[0].tuples):
                result += ("  " + str(r)) + "\n"
        else:
            result += "No"
        result.rstrip("\n")

    else:
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
