#!/usr/bin/env python3
from collections import OrderedDict
from pandas import DataFrame as Relation
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
            self.relations[scheme.id] = (Relation(
                data=[fact.stringList for fact in facts])
            )

    @staticmethod
    def _join(group: Relation) -> Relation:
        name = list(group)[0]
        result = {name: []}
        for index, row in group.iterrows():
            single = row.drop_duplicates()
            if len(single) == 1:
                result[name].append(list(single)[0])
            else:
                result[name].append(None)

        return Relation(result)

    def evaluate_query(self, query: datalog_parser.Query) -> Relation or int:
        logger.debug("Evaluating query: {}?".format(query))
        if self.relations.get(query.id, None) is None:
            # Create the Query if it doesn't exist
            self.relations[query.id] = Relation()
        logger.debug("Relation:\n{}".format(self.print_relation(self.relations[query.id])))

        keep_columns = list()

        # SELECT
        # If a parameter is a string, then select the rows that match that string in the right columns
        selected = self.relations[query.id]
        if not selected.empty:
            selected = selected.drop_duplicates()
        logger.debug("Shape: {}".format(selected.shape))
        max_keep = selected.shape[1]

        for i, p in enumerate(query.parameterList):
            if p.expression:
                logger.warning("I don't know how to handle expressions yet")
            elif p.string_id.type is TokenType.STRING:
                # Only keep rows that match
                if not selected.empty:
                    selected = selected.loc[selected.ix[:, i] == p.string_id]
            elif p.string_id.type is TokenType.ID and i < max_keep:
                keep_columns.append(i)

        if not selected.empty:
            selected = selected.drop_duplicates()

        logger.debug("Selected:\n{}".format(self.print_relation(selected)))
        if selected.shape[0] == 1 and not keep_columns:
            logger.debug("Returning Single Match")
            return SINGLE_MATCH

        # PROJECT
        logger.debug("Keeping columns {}".format(", ".join([str(i) for i in keep_columns])))
        projected = selected.iloc[:, keep_columns]
        logger.debug("Projected:\n{}".format(self.print_relation(projected)))

        # RENAME
        if projected.empty:
            renamed = projected
        else:
            renamed = projected.drop_duplicates()
        renamed.columns = [x for x in query.parameterList[:max_keep] if x.string_id and x.string_id.type is TokenType.ID]
        logger.debug("Renamed:\n{}".format(self.print_relation(renamed)))

        # COMBINE
        # Make sure columns with the same name have the same values in each row
        joined = renamed. \
            groupby(lambda x: x.string_id, axis=1). \
            apply(self._join). \
            dropna(how='all', axis=1). \
            dropna(how='any'). \
            reset_index(drop=True)
        logger.debug("Joined:\n{}".format(self.print_relation(joined)))
        return joined

    @staticmethod
    def print_relation(relation: Relation) -> (int, str):
        rows = set()
        if not relation.empty:
            relation = relation.drop_duplicates()
        for _, row in relation.iterrows():
            pairs = list()
            for index, item in row.iteritems():
                if isinstance(index, tuple):
                    index = index[1].string_id
                if isinstance(index, datalog_parser.Parameter):
                    index = index.string_id
                pairs.append("{}={}".format(
                    index.value if isinstance(index, Token) else None, item.value if isinstance(item, Token) else None)
                )
            rows.add(", ".join(pairs))
        return "  " + "\n  ".join(sorted(rows))

    def __str__(self) -> str:
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

            if self.rdbms[query] is SINGLE_MATCH:
                result += "Yes(1)\n"
            elif self.rdbms[query] is None or self.rdbms[query].empty:
                result += "No\n"
            else:
                self.rdbms[query].drop_duplicates(inplace=True)
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
    if args.debug:
        datalog = datalog_parser.DatalogProgram(tokens)
    else:
        try:
            datalog = datalog_parser.DatalogProgram(tokens)
        except TokenError as t:
            print('Failure!\n  {}'.format(t))

    assert isinstance(datalog, datalog_parser.DatalogProgram)
    main_rdbms = RDBMS(datalog)

    for datalog_query in datalog.queries.queries:
        main_rdbms.rdbms[datalog_query] = main_rdbms.evaluate_query(datalog_query)

    print(main_rdbms)
