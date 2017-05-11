#!/usr/bin/env python3
from argparse import ArgumentParser
import lexical_analyzer
from tokens import *


class Scheme:
    id = None
    idList = None

    def __init__(self, lex_tokens):
        self.idList = list()
        t = lex_tokens.pop(0)
        if not t[TYPE] == ID:
            raise TokenError(t)
        self.id = t
        t = lex_tokens.pop(0)
        if not t[TYPE] == LEFT_PAREN:
            raise TokenError(t)
        # There must be at least one ID inside the parenthesis
        t = lex_tokens.pop(0)
        if not t[TYPE] == ID:
            raise TokenError(t)
        self.idList.append(t)
        while len(lex_tokens) > 1:
            t = lex_tokens.pop(0)
            if not t[TYPE] == COMMA:
                raise TokenError(t)
            t = lex_tokens.pop(0)
            if not t[TYPE] == ID:
                raise TokenError(t)
            self.idList.append(t)
        t = lex_tokens.pop(0)
        if not t[TYPE] == RIGHT_PAREN:
            raise TokenError(t)
        pass

    def __str__(self):
        """
        :return: A string representation of this class
        """
        result = "%s(" % self.id[VALUE]
        for t in self.idList:
            result += t[VALUE] + ","

        # Remove extra comma
        result = result[:-1]

        return result + ")"


class Schemes:
    schemes = list()

    def __init__(self, lex_tokens):
        # Validate the syntax of the Scheme
        t = lex_tokens.pop(0)
        if not t[TYPE] == COLON:
            raise TokenError(t)

        new_scheme = list()
        while lex_tokens:
            t = lex_tokens.pop(0)
            new_scheme.append(t)
            # Once we reach a right parenthesis it is a new scheme
            if t[TYPE] == RIGHT_PAREN:
                self.schemes.append(Scheme(new_scheme))
                new_scheme.clear()
        if new_scheme:
            raise TokenError(new_scheme.pop())

    def __str__(self):
        """
        :return: A string representation of this class
        """
        result = "Schemes(%s):\n" % str(len(self.schemes))
        for scheme in self.schemes:
            result += "  " + str(scheme) + "\n"
        return result


class Facts:
    domain = None

    def __init__(self, lex_tokens):
        pass

    def __str__(self):
        """
        :return: A string representation of this class
        """
        return "foo"


class Rules:
    def __init__(self, lex_tokens):
        pass

    def __str__(self):
        """
        :return: A string representation of this class
        """
        return "foo"


class Queries:
    def __init__(self, lex_tokens):
        pass

    def __str__(self):
        """
        :return: A string representation of this class
        """
        return "foo"


class DatalogProgram:
    schemes = None
    facts = None
    rules = None
    queries = None

    def __init__(self, lex_tokens):
        # Remove all comments from tokens
        ignore_types = [WHITESPACE, MULTILINE, COMMENT]
        lex_tokens = [t for t in lex_tokens if not t[0] in ignore_types]
        t_tokens = list()
        iteration = None
        for t in lex_tokens:
            if t[0] == SCHEMES:
                iteration = SCHEMES
            elif t[0] == FACTS and iteration == SCHEMES:
                # Everything from the beginning of file to FACTS belongs to schemes
                self.schemes = Schemes(t_tokens)
                # There must be at least one scheme
                if not self.schemes.schemes:
                    raise TokenError(t)
                t_tokens.clear()
                iteration = FACTS
            elif t[0] == RULES and iteration == FACTS:
                # Everything form FACTS to RULES belongs to facts
                self.facts = Facts(t_tokens)
                t_tokens.clear()
                iteration = RULES
            elif t[0] == QUERIES and iteration == RULES:
                # Everything from RULES to QUERIES belongs to rules
                self.rules = Rules(t_tokens)
                t_tokens.clear()
                iteration = QUERIES
            elif not iteration:
                # If Schemes haven't been seen yet
                raise TokenError(t)
            else:
                t_tokens.append(t)

        # If every field didn't get populated
        if not iteration == QUERIES:
            raise TokenError(t_tokens.pop())

        # Everything else belongs to queries
        self.queries = Queries(t_tokens)

    def __str__(self):
        """
        :return: A string representation of this class
        """
        return '%s\n%s\n%s\n%s\n%s' % (
            str(self.schemes),
            str(self.facts),
            str(self.rules),
            str(self.queries),
            str(self.facts.domain if self.facts else None)
        )


if __name__ == "__main__":
    """
    Run the datalog parser by itself and produce the proper output
    """
    args = ArgumentParser(description="Run the datalog parser, this will produce output for lab 2")
    args.add_argument('-d', '--debug', action='store_true', default=False)
    args.add_argument('file', help='datalog file to parse')
    arg = args.parse_args()

    debug = arg.debug
    d_file = arg.file

    if debug: print("Parsing '%s'" % d_file)

    tokens = lexical_analyzer.scan(d_file)

    if debug:
        # Print out traces on token errors
        datalog = DatalogProgram(tokens)
        print(str(datalog))
    else:
        # Ignore traces on token errors
        try:
            datalog = DatalogProgram(tokens)
            print(str(datalog))
        except TokenError:
            pass
