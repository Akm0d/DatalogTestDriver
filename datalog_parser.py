#!/usr/bin/env python3
import lexical_analyzer
import logging

from tokens import TokenError, TokenType

logger = logging.getLogger(__name__)


class Scheme:
    """
    id: The main ID Token
    idList: A list of ID tokens
    """

    def __init__(self, lex_tokens):
        self.idList = list()
        t = lex_tokens.pop(0)
        if not t.type == TokenType.ID:
            raise TokenError(t)
        self.id = t
        t = lex_tokens.pop(0)
        if not t.type == TokenType.LEFT_PAREN:
            raise TokenError(t)
        # There must be at least one ID inside the parenthesis
        t = lex_tokens.pop(0)
        if not t.type == TokenType.ID:
            raise TokenError(t)
        self.idList.append(t)
        while len(lex_tokens) > 1:
            t = lex_tokens.pop(0)
            if not t.type == TokenType.COMMA:
                raise TokenError(t)
            t = lex_tokens.pop(0)
            if not t.type == TokenType.ID:
                raise TokenError(t)
            self.idList.append(t)
        if not lex_tokens:
            raise TokenError(t)
        t = lex_tokens.pop(0)
        if not t.type == TokenType.RIGHT_PAREN:
            raise TokenError(t)

    def __str__(self):
        return "{}({})".format(self.id.value, ",".join(t.value for t in self.idList))


class Schemes:
    """
    schemes: a list of Scheme tokens
    """

    def __init__(self, lex_tokens):
        self.schemes = list()
        # SCHEMES
        t = lex_tokens.pop(0)
        if not t.type == TokenType.SCHEMES:
            raise TokenError(t)
        # COLON
        t = lex_tokens.pop(0)
        if not t.type == TokenType.COLON:
            raise TokenError(t)
        # SCHEMELIST
        t_tokens = list()
        while len(lex_tokens) > 1:
            t = lex_tokens.pop(0)
            t_tokens.append(t)
            # Once we reach a right parenthesis it is a new scheme
            if t.type == TokenType.RIGHT_PAREN:
                self.schemes.append(Scheme(t_tokens))
                t_tokens.clear()

        # If there are tokens left over then make a scheme out of them
        t = lex_tokens.pop(0)

        if t_tokens:
            t_tokens.append(t)
            Scheme(t_tokens)

        if not t.type == TokenType.FACTS:
            raise TokenError(t)

    def __str__(self):
        return "Schemes({}):\n{}\n".format(len(self.schemes), "\n".join("  " + str(s) for s in self.schemes))


class Domain(set):
    def __str__(self):
        return "Domain({}):{}{}".format(
            len(self),
            "\n" if self else "",
            "\n".join("  " + f for f in sorted(self)))


class Fact:
    """
    id:
    stringList: a list of String tokens
    """
    # will this be shared amongst all instances of this class?
    domain = Domain()

    def __init__(self, lex_tokens=None, name=None, attributes=None):
        if name and attributes:
            assert isinstance(name, tuple)
            self.id = name
            assert isinstance(attributes, list)
            self.stringList = attributes
        else:
            self.stringList = list()
            t = lex_tokens.pop(0)
            if not t.type == TokenType.ID:
                raise TokenError(t)
            self.id = t
            t = lex_tokens.pop(0)
            if not t.type == TokenType.LEFT_PAREN:
                raise TokenError(t)
            # There must be at least one ID inside the parenthesis
            t = lex_tokens.pop(0)
            if not t.type == TokenType.STRING:
                raise TokenError(t)
            self.domain.add(t.value)
            self.stringList.append(t)
            while len(lex_tokens) > 2 and (t.type in [TokenType.COMMA, TokenType.STRING]):
                t = lex_tokens.pop(0)
                if t.type == TokenType.RIGHT_PAREN:
                    # The loop is ending pre-maturely, but an error will be thrown
                    break
                if not t.type == TokenType.COMMA:
                    raise TokenError(t)
                t = lex_tokens.pop(0)
                if not t.type == TokenType.STRING:
                    raise TokenError(t)
                self.domain.add(t.value)
                self.stringList.append(t)
            if not lex_tokens:
                raise TokenError(t)
            t = lex_tokens.pop(0)
            if not t.type == TokenType.RIGHT_PAREN:
                raise TokenError(t)
            if not lex_tokens:
                raise TokenError(t)
            t = lex_tokens.pop(0)
            if not t.type == TokenType.PERIOD:
                raise TokenError(t)
            if lex_tokens:
                raise TokenError(lex_tokens.pop(0))
            pass

    def __str__(self):
        return "{}({}).".format(self.id.value, ",".join(t.value for t in self.stringList))


class Facts:
    """
    facts
    """

    def __init__(self, lex_tokens):
        self.facts = list()
        # Validate the syntax of the Scheme
        t = lex_tokens.pop(0)
        if not t.type == TokenType.COLON:
            raise TokenError(t)

        t_tokens = list()
        while len(lex_tokens) > 1:
            t = lex_tokens.pop(0)
            t_tokens.append(t)
            # Once we reach a period it is a new fact
            if t.type == TokenType.PERIOD:
                self.facts.append(Fact(t_tokens))
                t_tokens.clear()

        t = lex_tokens.pop(0)

        if t_tokens:
            t_tokens.append(t)
            Fact(t_tokens)

        if not t.type == TokenType.RULES:
            raise TokenError(t)

    def __str__(self):
        return "Facts({}):{}{}".format(
            len(self.facts),
            "\n" if self.facts else "",
            "\n".join("  " + str(fact) for fact in self.facts)
        )


class Expression:
    param_1 = None
    operator = None
    param_2 = None

    def __init__(self, lex_tokens):
        # Get Param 1
        t = lex_tokens.pop(0)
        if not t.type in [TokenType.STRING, TokenType.ID, TokenType.LEFT_PAREN]:
            raise TokenError(t)
        if t.type in [TokenType.STRING, TokenType.ID]:
            self.param_1 = Parameter(list([t]))
        # If it is a left parenthesis, then grab tokens until we are palindrome and pass to parameter
        elif t.type == TokenType.LEFT_PAREN:
            t_tokens = list([])
            palindrome = 1
            t_tokens.append(t)
            # Grab tokens until palindrome is zero
            while palindrome > 0 and lex_tokens:
                t = lex_tokens.pop(0)
                t_tokens.append(t)
                if t.type == TokenType.RIGHT_PAREN:
                    palindrome -= 1
                elif t.type == TokenType.LEFT_PAREN:
                    palindrome += 1
            self.param_1 = Parameter(t_tokens)

        # Get Operator
        if not lex_tokens:
            raise TokenError(t)
        t = lex_tokens.pop(0)
        if not t.type in [TokenType.MULTIPLY, TokenType.ADD]:
            raise TokenError(t)
        self.operator = t

        # Get Param 2
        if not lex_tokens:
            raise TokenError(t)
        t = lex_tokens.pop(0)
        if not t.type in [TokenType.STRING, TokenType.ID, TokenType.LEFT_PAREN]:
            raise TokenError(t)
        if t.type in [TokenType.STRING, TokenType.ID]:
            self.param_2 = Parameter(list([t]))
        # If it is a left parenthesis, then grab tokens until we are palindrome and pass to parameter
        elif t.type == TokenType.LEFT_PAREN:
            t_tokens = list([])
            palindrome = 1
            t_tokens.append(t)
            # Grab tokens until palindrome is zero
            while palindrome > 0 and lex_tokens:
                t = lex_tokens.pop(0)
                t_tokens.append(t)
                if t.type == TokenType.RIGHT_PAREN:
                    palindrome -= 1
                elif t.type == TokenType.LEFT_PAREN:
                    palindrome += 1
            self.param_2 = Parameter(t_tokens)

    def __str__(self):
        return "({}{}{})".format(str(self.param_1), self.operator.value, str(self.param_2))


class Parameter:
    string_id = None
    expression = None

    def __init__(self, lex_tokens):
        t = lex_tokens.pop(0)
        # If there was only one token, it is a string or an id
        if not lex_tokens:
            if not t.type in [TokenType.ID, TokenType.STRING]:
                raise TokenError(t)
            self.string_id = t
        else:
            self.expression = Expression(lex_tokens)

    def __str__(self):
        return self.string_id.value if self.string_id else str(self.expression)


class Predicate:
    id = None
    parameterList = None

    def __init__(self, lex_tokens):
        self.parameterList = list([])
        t = lex_tokens.pop(0)
        if not t.type == TokenType.ID:
            raise TokenError(t)
        self.id = t

        if not lex_tokens:
            raise TokenError(t)
        t = lex_tokens.pop(0)
        if not t.type == TokenType.LEFT_PAREN:
            raise TokenError(t)

        # Check if there is a parameter
        t = lex_tokens.pop(0)
        if not t.type in [TokenType.STRING, TokenType.ID, TokenType.LEFT_PAREN]:
            raise TokenError(t)

        if t.type in [TokenType.STRING, TokenType.ID]:
            self.parameterList.append(Parameter(list([t])))
        # If it is a left parenthesis, then grab tokens until we are palindrome and pass to parameter
        elif t.type == TokenType.LEFT_PAREN:
            t_tokens = list([])
            palindrome = 1
            t_tokens.append(t)
            # Grab tokens until palindrome is zero
            while palindrome > 0 and lex_tokens:
                t = lex_tokens.pop(0)
                if t.type == TokenType.RIGHT_PAREN:
                    palindrome -= 1
                elif t.type == TokenType.LEFT_PAREN:
                    palindrome += 1
                if palindrome != 0: t_tokens.append(t)
            self.parameterList.append(Parameter(t_tokens))
            t_tokens.clear()

        while len(lex_tokens) > 1:
            # Check for comma
            t = lex_tokens.pop(0)
            if not t.type == TokenType.COMMA:
                raise TokenError(t)

            # Check for another parameter
            t = lex_tokens.pop(0)
            if not t.type in [TokenType.STRING, TokenType.ID, TokenType.LEFT_PAREN]:
                raise TokenError(t)

            if t.type in [TokenType.STRING, TokenType.ID]:
                self.parameterList.append(Parameter(list([t])))
            # If it is a left parenthesis, then grab tokens until we are palindrome and pass to parameter
            elif t.type == TokenType.LEFT_PAREN:
                t_tokens = list([])
                palindrome = 1
                t_tokens.append(t)
                # Grab tokens until palindrome is zero
                while palindrome > 0 and lex_tokens > 1:
                    t = lex_tokens.pop(0)
                    t_tokens.append(t)
                    if t.type == TokenType.RIGHT_PAREN:
                        palindrome -= 1
                    elif t.type == TokenType.LEFT_PAREN:
                        palindrome += 1
                self.parameterList.append(Parameter(t_tokens))
                t_tokens.clear()

        if not lex_tokens:
            raise TokenError(t)
        t = lex_tokens.pop(0)
        if not t.type == TokenType.RIGHT_PAREN:
            raise TokenError(t)

        if lex_tokens:
            raise TokenError(lex_tokens.pop(0))

        # Only compute this once to save time
        self.hash = hash(str(self))

    def __str__(self):
        return "{}({})".format(self.id.value, ",".join(str(p) for p in self.parameterList))

    def __hash__(self):
        """
        This is necessary if we want to use queries as a key in lab 3
        :return: The hashed form of the string representation of this class
        """
        return self.hash


class Rule:
    head = None
    predicates = None

    def __init__(self, lex_tokens):
        t_tokens = list()
        palindrome = 0
        while len(lex_tokens) > 1:
            t = lex_tokens.pop(0)
            t_tokens.append(t)
            if t.type == TokenType.LEFT_PAREN:
                palindrome += 1

            # Once we balance the right-parenthesis it is a new predicate
            if t.type == TokenType.RIGHT_PAREN:
                palindrome -= 1
                if palindrome < 0:
                    raise TokenError(t)
                elif palindrome == 0:
                    if not self.head:
                        # The format for a head predicate is exactly the same as that of a scheme
                        self.head = Scheme(t_tokens)
                        if not lex_tokens:
                            raise TokenError(t)
                        t = lex_tokens.pop(0)
                        if not t.type == TokenType.COLON_DASH:
                            raise TokenError(t)
                    else:
                        new_item = Predicate(t_tokens)
                        if not self.predicates:
                            self.predicates = list([])
                        self.predicates.append(new_item)
                        if not lex_tokens:
                            self.parent_error = True
                        else:
                            t = lex_tokens.pop(0)
                            if not t.type == TokenType.COMMA and len(lex_tokens) > 1:
                                raise TokenError(t)
                    t_tokens.clear()
                else:
                    # We haven't balanced parenthesis yet
                    pass

        if not t.type == TokenType.PERIOD:
            raise TokenError(t)

        if t_tokens or palindrome:
            raise TokenError(t_tokens.pop())
        pass

    def __str__(self):
        return "{}:- {}".format(str(self.head), ",".join(str(p) for p in self.predicates))


class Rules:
    rules = None

    def __init__(self, lex_tokens):
        self.rules = list()
        # Validate the syntax of the Scheme
        t = lex_tokens.pop(0)
        if not t.type == TokenType.COLON:
            raise TokenError(t)

        t_tokens = list()
        while len(lex_tokens) > 1:
            t = lex_tokens.pop(0)
            t_tokens.append(t)
            # Once we reach a period it is a new rule
            if t.type == TokenType.PERIOD:
                self.rules.append(Rule(t_tokens))
                t_tokens.clear()

        t = lex_tokens.pop(0)

        if t_tokens:
            t_tokens.append(t)
            Rule(t_tokens)

        if not t.type == TokenType.QUERIES:
            raise TokenError(t)

    def __str__(self):
        return "Rules({}):\n{}".format(len(self.rules), "\n".join("  " + str(r) for r in self.rules))


class Queries:
    queries = None

    def __init__(self, lex_tokens):
        self.queries = list()
        # Validate the syntax of the Scheme
        t = lex_tokens.pop(0)
        if not t.type == TokenType.COLON:
            raise TokenError(t)

        t_tokens = list()
        while len(lex_tokens) > 1:
            t = lex_tokens.pop(0)
            # Once we reach a question mark it is a new query
            if t.type == TokenType.Q_MARK:
                last = t_tokens.pop()
                if not last.type == TokenType.RIGHT_PAREN:
                    raise TokenError(t)
                t_tokens.append(last)
                self.queries.append(Predicate(t_tokens))
                t_tokens.clear()
            else:
                t_tokens.append(t)

        if not t.type == TokenType.Q_MARK:
            t = lex_tokens.pop(0)
            raise TokenError(t)

        t = lex_tokens.pop(0)

        # If there are leftover tokens then turn them into a predicate to throw the right token error
        if t_tokens:
            t_tokens.append(t)
            Predicate(t_tokens)

        if not t.type == TokenType.EOF:
            raise TokenError(t)

    def __str__(self):
        return "Queries({}):\n{}".format(len(self.queries), "\n".join("  " + str(q) + "?" for q in self.queries))


class DatalogProgram:
    schemes = None
    facts = None
    rules = None
    queries = None

    def __init__(self, lex_tokens):
        # Remove all comments from tokens
        t_tokens = list()
        iteration = None
        for t in lex_tokens:
            t_tokens.append(t)
            if t.type == TokenType.SCHEMES and not iteration:
                iteration = TokenType.SCHEMES
            # If iteration hasn't been defined and the first token wasn't a scheme we need to stop
            elif not iteration:
                raise TokenError(t)
            elif t.type == TokenType.FACTS and iteration == TokenType.SCHEMES:
                # Everything from the beginning of file to FACTS belongs to schemes
                self.schemes = Schemes(t_tokens)
                # There must be at least one scheme
                if not self.schemes.schemes:
                    raise TokenError(t)
                t_tokens.clear()
                iteration = TokenType.FACTS
            elif t.type == TokenType.RULES and iteration == TokenType.FACTS:
                # Everything form FACTS to RULES belongs to facts
                self.facts = Facts(t_tokens)
                t_tokens.clear()
                iteration = TokenType.RULES
            elif t.type == TokenType.QUERIES and iteration == TokenType.RULES:
                # Everything from RULES to QUERIES belongs to rules
                self.rules = Rules(t_tokens)
                # Make sure it ended correctly
                t_tokens.clear()
                iteration = TokenType.QUERIES
            elif t.type == TokenType.EOF and iteration == TokenType.QUERIES:
                # Everything else belongs to queries
                self.queries = Queries(t_tokens)
                # There must be at least one query
                if not self.queries.queries:
                    raise TokenError(t)
            elif not iteration:
                # If Schemes haven't been seen yet
                raise TokenError(t)

        # If There are left over tokens, then hand them off to the class of the current iteration so it can give the
        # proper error
        if t_tokens:
            if iteration == TokenType.SCHEMES:
                Schemes(t_tokens)
            elif iteration == TokenType.FACTS:
                Facts(t_tokens)
            elif iteration == TokenType.RULES:
                Rules(t_tokens)
            elif iteration == TokenType.QUERIES:
                Queries(t_tokens)
            else:
                raise TokenError(t_tokens.pop(0))

    def __str__(self):
        return '{}{}\n{}\n{}\n{}\n'.format(
            self.schemes,
            self.facts,
            self.rules,
            self.queries,
            self.facts.facts[0].domain if self.facts.facts else Domain()
        )


def main(d_file, part: int = 2, debug: bool = False):
    result = "Success!\n"

    if not (1 <= part <= 2):
        raise ValueError("Part must be either 1 or 2")

    logger.debug("Parsing '%s'" % d_file)

    tokens = lexical_analyzer.scan(d_file)

    if debug:
        # Print out traces on token errors
        datalog = DatalogProgram(tokens)
        if part == 2:
            result += str(datalog)
    else:
        # Ignore traces on token errors
        try:
            datalog = DatalogProgram(tokens)
            if part == 2:
                result += str(datalog)
        except TokenError as t:
            return 'Failure!\n  %s' % str(t)
    return result


if __name__ == "__main__":
    """
    Run the datalog parser by itself and produce the proper output
    """
    from argparse import ArgumentParser

    arg = ArgumentParser(description="Run the datalog parser, this will produce output for lab 2")
    arg.add_argument('-d', '--debug', help="The logging debug level to use", default=logging.NOTSET, metavar='LEVEL')
    arg.add_argument('-p', '--part', help='A 1 or a 2.  Defaults to 2', default=2)
    arg.add_argument('file', help='datalog file to parse')
    args = arg.parse_args()

    logging.basicConfig(level=logging.ERROR)
    logger.setLevel(int(args.debug))

    print(str(main(args.file, part=int(args.part), debug=True)))
