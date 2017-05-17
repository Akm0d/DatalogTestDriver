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
        if not lex_tokens:
            raise TokenError(t)
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
    schemes = None

    def __init__(self, lex_tokens):
        self.schemes = list()
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
            # If there are any left over tokens then create a new scheme with them to get the right error
            Scheme(new_scheme)

    def __str__(self):
        """
        :return: A string representation of this class
        """
        result = "Schemes(%s):\n" % str(len(self.schemes))
        for scheme in self.schemes:
            result += "  " + str(scheme) + "\n"
        result += "\n"
        # Remove trailing new line
        result = result[:-1]
        return result


class Fact:
    id = None
    stringList = None
    # This will be shared across every instance of the Fact class
    domain = set()

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
        self.domain.add(t[VALUE])
        self.stringList.append(t)
        while len(lex_tokens) > 2:
            t = lex_tokens.pop(0)
            if not t[TYPE] == COMMA:
                raise TokenError(t)
            t = lex_tokens.pop(0)
            if not t[TYPE] == STRING:
                raise TokenError(t)
            self.domain.add(t[VALUE])
            self.stringList.append(t)
        if not lex_tokens:
            raise TokenError(t)
        t = lex_tokens.pop(0)
        if not t[TYPE] == RIGHT_PAREN:
            raise TokenError(t)
        if not lex_tokens:
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
    facts = None

    def __init__(self, lex_tokens):
        self.facts = list()
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
            Fact(new_fact)

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

    def print_domain(self):
        """
        :return A string representation of the domain of all Fact objects
        """
        if self.facts:
            domain = self.facts[0].domain
            result = "Domain(%s):\n" % str(len(domain))
            for item in sorted(domain):
                result += "  " + item + "\n"
            # Remove trailing new line
            result = result[:-1]
            return result
        else:
            return None


class Parameter:
    expression = None

    def __init__(self, lex_tokens):
        self.expression = list([])
        t = lex_tokens.pop(0)
        if t[TYPE] in [STRING, ID]:
            self.expression = list([t])
            # If it is a string or ID then there should be nothing else
            if lex_tokens:
                if not lex_tokens:
                    raise TokenError(t)
                t = lex_tokens.pop(0)
                raise TokenError(t)
        elif t[TYPE] == LEFT_PAREN:
            self.expression.append(t)
            # Look at tokens until there are no more or we balance parenthesis
            while len(lex_tokens) > 1:
                # TODO Next token is a parameter
                # TODO Next is an operator
                # TODO Next is a parameter
                t = lex_tokens.pop(0)
                self.expression.append(t)

            # end with right parenthesis
            if not lex_tokens:
                raise TokenError(t)
            t = lex_tokens.pop(0)
            self.expression.append(t)
            if not t[TYPE] == RIGHT_PAREN:
                raise TokenError(t)

    def __str__(self):
        result = ""
        for t in self.expression:
            result += t[VALUE]
        return result


def get_parameter(lex_tokens):
    t = lex_tokens.pop(0)
    expression = list([])
    if t[TYPE] in [STRING, ID]:
        return list([t]), lex_tokens
    # It must be an expression
    elif t[TYPE] == LEFT_PAREN:
        expression.append(t)
        palindrome = 1
        # Look at tokens until there are no more or we balance parenthesis
        while lex_tokens and palindrome > 0:
            t = lex_tokens.pop(0)
            if t[TYPE] == RIGHT_PAREN:
                palindrome -= 1
            expression.append(t)
        return expression, lex_tokens
    else:
        raise TokenError(t)


class Predicate:
    id = None
    parameterList = None

    def __init__(self, lex_tokens):
        t = lex_tokens.pop(0)
        if not t[TYPE] == ID:
            raise TokenError(t)
        self.id = t

        if not lex_tokens:
            raise TokenError(t)
        t = lex_tokens.pop(0)
        if not t[TYPE] == LEFT_PAREN:
            raise TokenError(t)
        # Check if there is a parameter
        (parameter, lex_tokens) = get_parameter(lex_tokens)
        self.parameterList = list([Parameter(parameter)])

        while len(lex_tokens) > 2:
            t = lex_tokens.pop(0)
            if not t[TYPE] == COMMA:
                raise TokenError(t)
            (parameter_tokens, lex_tokens) = get_parameter(lex_tokens)
            self.parameterList.append(Parameter(parameter_tokens))

    def __str__(self):
        """
        :return: A string representation of this class
        """
        result = "%s(" % self.id[VALUE]
        for parameter in self.parameterList:
            result += str(parameter) + ","

        # Remove extra comma
        result = result[:-1]

        return result + ")"


class Rule:
    head = None
    predicates = None

    def __init__(self, lex_tokens):
        # print([i[TYPE] for i in lex_tokens])
        # Validate the syntax of the Rule
        new_predicate = list()
        palindrome = 0
        while lex_tokens:
            t = lex_tokens.pop(0)
            new_predicate.append(t)
            if t[TYPE] == LEFT_PAREN:
                palindrome += 1

            # Once we balance the right-parenthesis it is a new predicate
            if t[TYPE] == RIGHT_PAREN:
                palindrome -= 1
                if palindrome < 0:
                    raise TokenError(t)
                elif palindrome == 0:
                    if not self.head:
                        # The format for a head predicate is exactly the same as that of a scheme
                        self.head = Scheme(new_predicate)
                        if not lex_tokens:
                            raise TokenError(t)
                        t = lex_tokens.pop(0)
                        if not t[TYPE] == COLON_DASH:
                            raise TokenError(t)
                    else:
                        new_item = Predicate(new_predicate)
                        if not self.predicates:
                            self.predicates = list([])
                        self.predicates.append(new_item)
                        if not lex_tokens:
                            raise TokenError(t)
                        t = lex_tokens.pop(0)
                        # If the next token is a period and there are still more tokens, then we have a problem
                        if t[TYPE] == PERIOD and lex_tokens:
                            raise TokenError(t)
                        # The next token should be a comma, or a period if we are at the end of the rule
                        elif not t[TYPE] == COMMA and not (t[TYPE] == PERIOD and not lex_tokens):
                            raise TokenError(t)
                        if t[TYPE] == PERIOD and lex_tokens:
                            raise TokenError(lex_tokens.pop(0))
                    new_predicate.clear()
                else:
                    # We haven't balanced parenthesis yet
                    pass

        if new_predicate or palindrome:
            raise TokenError(new_predicate.pop())
        pass

    def __str__(self):
        """
        :return: A string representation of this class
        """
        result = str(self.head) + " :- "
        for predicate in self.predicates:
            result += str(predicate) + ","

        # Remove extra comma
        result = result[:-1]

        return result + "."


class Rules:
    rules = None

    def __init__(self, lex_tokens):
        self.rules = list()
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
            Rule(new_rule)

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


class Queries:
    queries = None

    def __init__(self, lex_tokens):
        self.queries = list()
        # Validate the syntax of the Scheme
        t = lex_tokens.pop(0)
        if not t[TYPE] == COLON:
            raise TokenError(t)

        new_query = list()
        while lex_tokens:
            t = lex_tokens.pop(0)
            # Once we reach a question mark it is a new query
            if t[TYPE] == Q_MARK:
                self.queries.append(Predicate(new_query))
                new_query.clear()
            else:
                new_query.append(t)
        if new_query:
            Predicate(new_query)

    def __str__(self):
        """
        :return: A string representation of this class
        """
        result = "Queries(%s):\n" % str(len(self.queries))
        for query in self.queries:
            result += "  " + str(query) + "?\n"
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
        lex_tokens = [t for t in lex_tokens if not t[TYPE] in ignore_types]
        t_tokens = list()
        iteration = None
        for t in lex_tokens:
            if t[TYPE] == SCHEMES and not iteration:
                iteration = SCHEMES
            elif t[TYPE] == FACTS and iteration == SCHEMES:
                # Everything from the beginning of file to FACTS belongs to schemes
                self.schemes = Schemes(t_tokens)
                # There must be at least one scheme
                if not self.schemes.schemes:
                    raise TokenError(t)
                t_tokens.clear()
                iteration = FACTS
            elif t[TYPE] == RULES and iteration == FACTS:
                # Everything form FACTS to RULES belongs to facts
                self.facts = Facts(t_tokens)
                t_tokens.clear()
                iteration = RULES
            elif t[TYPE] == QUERIES and iteration == RULES:
                # Everything from RULES to QUERIES belongs to rules
                self.rules = Rules(t_tokens)
                t_tokens.clear()
                iteration = QUERIES
            elif t[TYPE] == EOF and iteration == QUERIES:
                # Everything else belongs to queries
                self.queries = Queries(t_tokens)
            elif not iteration:
                # If Schemes haven't been seen yet
                raise TokenError(t)
            else:
                t_tokens.append(t)

        # If There are left over tokens, then hand them off to the class of the current iteration so it can give the
        # proper error
        if t_tokens:
            if iteration == SCHEMES:
                Schemes(t_tokens)
            elif iteration == FACTS:
                Facts(t_tokens)
            elif iteration == RULES:
                Rules(t_tokens)
            elif iteration == QUERIES:
                Queries(t_tokens)
            else:
                raise TokenError(t_tokens.pop(0))

    def __str__(self):
        """
        :return: A string representation of this class
        """
        return '%s%s\n%s\n%s\n%s' % (
            str(self.schemes),
            str(self.facts),
            str(self.rules),
            str(self.queries),
            str(self.facts.print_domain() if self.facts.facts else "Domain(0):")
        )


if __name__ == "__main__":
    """
    Run the datalog parser by itself and produce the proper output
    """
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

    tokens = lexical_analyzer.scan(d_file)

    if debug:
        # Print out traces on token errors
        datalog = DatalogProgram(tokens)
        print("Success!")
        if part == 2:
            print(str(datalog))
    else:
        # Ignore traces on token errors
        try:
            datalog = DatalogProgram(tokens)
            print("Success!")
            if part == 2:
                print(str(datalog))
        except TokenError:
            pass
