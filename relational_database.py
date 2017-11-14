#!/usr/bin/env python3
import csv
import multiprocessing

from collections import OrderedDict
from pandas import DataFrame as Relation, np
from tokens import TokenType, TokenError, Token

import datalog_parser
import logging
import lexical_analyzer

logger = logging.getLogger(__name__)

SINGLE_MATCH = 1


class RDBMS:
    def __init__(self, datalog_program: datalog_parser.DatalogProgram):
        self.rdbms = OrderedDict()
        self.relations = dict()

        # initialize the rdbms with query values
        for query in datalog_program.queries.queries:
            self.rdbms[query] = Relation()

        # Populate the relations
        for scheme in datalog_program.schemes.schemes:
            facts = [fact for fact in datalog_program.facts.facts if fact.id == scheme.id]
            logger.debug("Scheme: {}".format(scheme))
            logger.debug("Facts: {}".format(" ".join(str(f) for f in facts)))
            if facts:
                self.relations[scheme.id] = (Relation(
                    data=[fact.stringList for fact in facts])
                ).drop_duplicates()
        for query in datalog_program.queries.queries:
            self.rdbms[query] = self.evaluate_query(query)

    def evaluate_query(self, query: datalog_parser.Query) -> Relation or int:
        logger.debug("Evaluating query: {}?".format(query))
        if self.relations.get(query.id, None) is None:
            # Create the Query if it doesn't exist
            self.relations[query.id] = Relation()

        relation = self.relations[query.id]
        logger.debug("Relation:\n{}".format(self.print_relation(relation)))
        if relation.empty:
            logger.debug("Relation empty")
            return relation

        selected = self.select(relation, query)
        if selected.empty:
            logger.debug("No matches found")
            return selected
        relation = self.project(selected, query)
        # If projecting is going to remove the only match
        if relation.empty and not selected.empty:
            logger.debug("Found single match")
            return SINGLE_MATCH  # return len(selected)

        relation = self.rename(relation, query)
        relation = self.inner_join(relation)
        relation = self.project(relation)
        return relation.dropna()

    def select(self, relation: Relation, query: datalog_parser.Query) -> Relation:
        # If a parameter is a string, then select the rows that match that string in the right columns
        for i, x in enumerate(query.parameterList):
            if (not x.expression) and (x.string_id.type is TokenType.STRING):
                mask = relation[[i]] == ([x.string_id])
                mask = mask.reindex(relation.index, relation.columns, method='nearest')
                relation = relation[mask].dropna()
        logger.debug("Selected:\n{}".format(self.print_relation(relation)))
        return relation

    def project(self, relation: Relation, query: datalog_parser.Query = None) -> Relation:
        """
        Project the columns that have the IDs in the query.
        If no query, then remove duplicate columns
        :param relation:
        :param query:
        """
        if query is None:
            _, indices = np.unique(relation.columns, return_index=True)
            relation = relation.iloc[:, np.sort(indices)]
            logger.debug("Projected:\n{}".format(self.print_relation(relation)))
        else:
            columns = [query.parameterList.index(x) for x in query.parameterList
                       if (not x.expression) and (x.string_id.type is TokenType.ID)]
            relation = relation.reindex(columns=columns)[columns]
            logger.debug("Projected:\n{}".format(self.print_relation(relation)))
        return relation

    def rename(self, relation: Relation, query: datalog_parser.Query) -> Relation:
        column_names = [
            x.string_id for x in query.parameterList if (not x.expression) and (x.string_id.type is TokenType.ID)
        ]
        relation.columns = column_names
        logger.debug("Renamed:\n{}".format(relation))
        return relation

    @staticmethod
    def _inner_join(relation: Relation) -> Relation:
        name = list(relation)[0]
        result = {name: []}
        for index, row in relation.iterrows():
            single = row.drop_duplicates()
            if len(single) == 1:
                result[name].append(list(single)[0])
            else:
                result[name].append(None)
        return Relation(result)

    def inner_join(self, relation: Relation) -> Relation:
        """
        Remove rows where multiple columns have the same name but not the same value
        :param relation:
        :return:
        """
        column_names = list(relation)
        if len(column_names) == len(set(column_names)):
            logger.debug("No inner join needs to be done")
            return relation
        relation = relation. \
            groupby(lambda x: x, axis=1). \
            apply(self._inner_join). \
            dropna(how='all', axis=1). \
            dropna(how='any'). \
            reset_index(drop=True)
        if not relation.empty:
            relation.columns = column_names[:len(relation.columns)]
        logger.debug("Inner Joined:\n{}".format(relation))
        return relation

    @staticmethod
    def print_relation(relation: Relation) -> (int, str):
        # TODO this is where most time is spent in the program, optimize it for the speed boosts
        if not relation.empty:
            relation = relation.sort_values(list(relation))
            relation = relation.apply(
                lambda column: column.apply(
                    lambda c: str(column.name.value if isinstance(column.name, Token)
                                  else str(column.name)) + "=" + c.value if isinstance(c, Token) else str(c))
                )
            relation = relation.dropna()
        # FIXME This has corner cases where the sep and escapechar can make incorrect values print out
        return "  " + relation.to_csv(
            index=False, header=False, sep='#', line_terminator='\n  ', quoting=csv.QUOTE_NONE, escapechar="\\"
        ).rstrip().replace("'#", "', ").replace('\\ ', ' ')

    def _str_worker(self, proc: int, query: datalog_parser.Query, results: dict):
        """
        Since print_relation is the most computationally heavy function, handle each query's print_relation in it's
        own process and save the results to a multi-threading dictionary.
        :param query:
        :param results:
        """
        result = str(query) + "? "
        if self.rdbms[query] is SINGLE_MATCH:
            result += "Yes(1)\n"
        elif self.rdbms[query] is None or self.rdbms[query].empty:
            result += "No\n"
        else:
            result += "Yes({})\n{}\n".format(len(self.rdbms[query]), self.print_relation(self.rdbms[query]))
        results[proc] = result

    def __str__(self) -> str:
        """
        This is the same as printing a relational database except we will also print the passes
        :return:
        """
        manager = multiprocessing.Manager()
        results = manager.dict()
        result = ""
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

    logger.debug("Parsing '%s'" % args.file)

    # Create class objects
    tokens = lexical_analyzer.scan(args.file)
    datalog = None
    try:
        datalog = datalog_parser.DatalogProgram(tokens)
    except TokenError as t:
        print("Failure!\n  {}".format(t))
        exit(1)

    print(RDBMS(datalog))
