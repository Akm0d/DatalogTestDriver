#!/usr/bin/env python3
from tokens import *
import lexical_analyzer


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
        # Remove trailing new line
        result = result[:-1]
        return result


class Domain:
    items = set()

    def __init__(self, lex_tokens):
        self.items = set([i[VALUE] for i in lex_tokens if i[TYPE] == STRING])
        pass

    def __str__(self):
        """
        :return: A string representation of this class
        """
        result = "Domain(%s):\n" % str(len(self.items))
        for fact in sorted(self.items):
            result += "  " + str(fact) + "\n"
        # Remove trailing new line
        if self.items:
            result = result[:-1]
        return result

    def __iter__(self):
        """
        When iterating over the domain just give back the ordered set
        :return: 
        """
        return sorted(self.items)


class Fact:
    id = None
    stringList = None

    def __init__(self, lex_tokens):
        self.stringList = list()
        t = lex_tokens.pop(0)
        if not t[TYPE] == ID:
            raise TokenError(t)
        self.id = t
        t = lex_tokens.pop(0)
        if not t[TYPE] == LEFT_PAREN:
            raise TokenError(t)
        # There must be at least one ID inside the parenthesis
        t = lex_tokens.pop(0)
        if not t[TYPE] == STRING:
            raise TokenError(t)
        self.stringList.append(t)
        while len(lex_tokens) > 2:
            t = lex_tokens.pop(0)
            if not t[TYPE] == COMMA:
                raise TokenError(t)
            t = lex_tokens.pop(0)
            if not t[TYPE] == STRING:
                raise TokenError(t)
            self.stringList.append(t)
        t = lex_tokens.pop(0)
        if not t[TYPE] == RIGHT_PAREN:
            raise TokenError(t)
        t = lex_tokens.pop(0)
        if not t[TYPE] == PERIOD:
            raise TokenError(t)
        pass

    def __str__(self):
        """
        :return: A string representation of this class
        """
        result = "%s(" % self.id[VALUE]
        for t in self.stringList:
            result += t[VALUE] + ","

        # Remove extra comma
        result = result[:-1]

        return result + ")."


class Facts:
    domain = None
    facts = list()

    def __init__(self, lex_tokens):
        # Generate the domain from these tokens
        self.domain = Domain(lex_tokens)
        # Validate the syntax of the Scheme
        t = lex_tokens.pop(0)
        if not t[TYPE] == COLON:
            raise TokenError(t)

        new_fact = list()
        while lex_tokens:
            t = lex_tokens.pop(0)
            new_fact.append(t)
            # Once we reach a period it is a new fact
            if t[TYPE] == PERIOD:
                self.facts.append(Fact(new_fact))
                new_fact.clear()
        if new_fact:
            raise TokenError(new_fact.pop())

    def __str__(self):
        """
        :return: A string representation of this class
        """
        result = "Facts(%s):\n" % str(len(self.facts))
        for fact in self.facts:
            result += "  " + str(fact) + "\n"
        # Remove trailing new line
        result = result[:-1]
        return result


class Rule:
    def __init__(self, lex_tokens):
        print([i[TYPE] for i in lex_tokens])
        pass

    def __str__(self):
        """
        :return: A string representation of this class
        """
        return ""


class Rules:
    rules = list()

    def __init__(self, lex_tokens):
        # Validate the syntax of the Scheme
        t = lex_tokens.pop(0)
        if not t[TYPE] == COLON:
            raise TokenError(t)

        new_rule = list()
        while lex_tokens:
            t = lex_tokens.pop(0)
            new_rule.append(t)
            # Once we reach a period it is a new rule
            if t[TYPE] == PERIOD:
                self.rules.append(Rule(new_rule))
                new_rule.clear()
        if new_rule:
            raise TokenError(new_rule.pop())

    def __str__(self):
        """
        :return: A string representation of this class
        """
        result = "Rules(%s):\n" % str(len(self.rules))
        for rule in self.rules:
            result += "  " + str(rule) + "\n"
        # Remove trailing new line
        result = result[:-1]
        return result


class Query:
    def __init__(self, lex_tokens):
        # print([i[TYPE] for i in lex_tokens])
        pass

    def __str__(self):
        """
        :return: A string representation of this class
        """
        return ""


class Queries:
    queries = list()

    def __init__(self, lex_tokens):
        # Validate the syntax of the Scheme
        t = lex_tokens.pop(0)
        if not t[TYPE] == COLON:
            raise TokenError(t)

        new_query = list()
        while lex_tokens:
            t = lex_tokens.pop(0)
            new_query.append(t)
            # Once we reach a question mark it is a new query
            if t[TYPE] == Q_MARK:
                self.queries.append(Query(new_query))
                new_query.clear()
        if new_query:
            raise TokenError(new_query.pop())

    def __str__(self):
        """
        :return: A string representation of this class
        """
        result = "Queries(%s):\n" % str(len(self.queries))
        for query in self.queries:
            result += "  " + str(query) + "\n"
        # Remove trailing new line
        result = result[:-1]
        return result


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
            elif t[0] == EOF and iteration == QUERIES:
                # Everything else belongs to queries
                self.queries = Queries(t_tokens)
            elif not iteration:
                # If Schemes haven't been seen yet
                raise TokenError(t)
            else:
                t_tokens.append(t)

        # If every field didn't get populated
        if not iteration == QUERIES:
            raise TokenError(t_tokens.pop())

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
    from argparse import ArgumentParser
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
        print("Success!\n" + str(datalog))
    else:
        # Ignore traces on token errors
        try:
            datalog = DatalogProgram(tokens)
            print("Success!\n" + str(datalog))
        except TokenError:
            pass
