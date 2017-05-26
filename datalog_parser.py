#!/usr/bin/env python3
from ast import literal_eval

from tokens import COMMA, PERIOD, Q_MARK, LEFT_PAREN, RIGHT_PAREN, COLON, COLON_DASH, MULTIPLY, Token
from tokens import ADD, SCHEMES, FACTS, RULES, QUERIES, ID, STRING, COMMENT, WHITESPACE, EOF
from tokens import TokenError, TYPE, VALUE
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
        # SCHEMES
        t = lex_tokens.pop(0)
        if not t[TYPE] == SCHEMES:
            raise TokenError(t)
        # COLON
        t = lex_tokens.pop(0)
        if not t[TYPE] == COLON:
            raise TokenError(t)
        # SCHEMELIST
        t_tokens = list()
        while len(lex_tokens) > 1:
            t = lex_tokens.pop(0)
            t_tokens.append(t)
            # Once we reach a right parenthesis it is a new scheme
            if t[TYPE] == RIGHT_PAREN:
                self.schemes.append(Scheme(t_tokens))
                t_tokens.clear()

        # If ther are tokens left over then make a scheme out of them
        t = lex_tokens.pop(0)

        if t_tokens:
            t_tokens.append(t)
            Scheme(t_tokens)

        if not t[TYPE] == FACTS:
            raise TokenError(t)

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


# This will eventually become a set
domain = None


class Fact:
    id = None
    stringList = None

    # This will be shared across every instance of the Fact class

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
        domain.add(t[VALUE])
        self.stringList.append(t)
        while len(lex_tokens) > 2 and (t[TYPE] in [COMMA, STRING]):
            t = lex_tokens.pop(0)
            if t[TYPE] == RIGHT_PAREN:
                # The loop is ending pre-maturely, but an error will be thrown
                break
            if not t[TYPE] == COMMA:
                raise TokenError(t)
            t = lex_tokens.pop(0)
            if not t[TYPE] == STRING:
                raise TokenError(t)
            domain.add(t[VALUE])
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
        if lex_tokens:
            raise TokenError(lex_tokens.pop(0))
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
        global domain
        domain = set()
        self.facts = list()
        # Validate the syntax of the Scheme
        t = lex_tokens.pop(0)
        if not t[TYPE] == COLON:
            raise TokenError(t)

        t_tokens = list()
        while len(lex_tokens) > 1:
            t = lex_tokens.pop(0)
            t_tokens.append(t)
            # Once we reach a period it is a new fact
            if t[TYPE] == PERIOD:
                self.facts.append(Fact(t_tokens))
                t_tokens.clear()

        t = lex_tokens.pop(0)

        if t_tokens:
            t_tokens.append(t)
            Fact(t_tokens)

        if not t[TYPE] == RULES:
            raise TokenError(t)

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
            result = "Domain(%s):\n" % str(len(domain))
            for item in sorted(domain):
                result += "  " + item + "\n"
            # Remove trailing new line
            result = result.strip()
            return result
        else:
            return None


class Expression:
    param_1 = None
    operator = None
    param_2 = None

    def __init__(self, lex_tokens):
        # Get Param 1
        t = lex_tokens.pop(0)
        if not t[TYPE] in [STRING, ID, LEFT_PAREN]:
            raise TokenError(t)
        if t[TYPE] in [STRING, ID]:
            self.param_1 = Parameter(list([t]))
        # If it is a left parenthesis, then grab tokens until we are palindrome and pass to parameter
        elif t[TYPE] == LEFT_PAREN:
            t_tokens = list([])
            palindrome = 1
            t_tokens.append(t)
            # Grab tokens until palindrome is zero
            while palindrome > 0 and lex_tokens:
                t = lex_tokens.pop(0)
                t_tokens.append(t)
                if t[TYPE] == RIGHT_PAREN:
                    palindrome -= 1
                elif t[TYPE] == LEFT_PAREN:
                    palindrome += 1
            self.param_1 = Parameter(t_tokens)

        # Get Operator
        if not lex_tokens:
            raise TokenError(t)
        t = lex_tokens.pop(0)
        if not t[TYPE] in [MULTIPLY, ADD]:
            raise TokenError(t)
        self.operator = t

        # Get Param 2
        if not lex_tokens:
            raise TokenError(t)
        t = lex_tokens.pop(0)
        if not t[TYPE] in [STRING, ID, LEFT_PAREN]:
            raise TokenError(t)
        if t[TYPE] in [STRING, ID]:
            self.param_2 = Parameter(list([t]))
        # If it is a left parenthesis, then grab tokens until we are palindrome and pass to parameter
        elif t[TYPE] == LEFT_PAREN:
            t_tokens = list([])
            palindrome = 1
            t_tokens.append(t)
            # Grab tokens until palindrome is zero
            while palindrome > 0 and lex_tokens:
                t = lex_tokens.pop(0)
                t_tokens.append(t)
                if t[TYPE] == RIGHT_PAREN:
                    palindrome -= 1
                elif t[TYPE] == LEFT_PAREN:
                    palindrome += 1
            self.param_2 = Parameter(t_tokens)

    def __str__(self):
        return "(%s%s%s)" % (str(self.param_1), str(self.operator[VALUE]), str(self.param_2))


class Parameter:
    string_id = None
    expression = None

    def __init__(self, lex_tokens):
        t = lex_tokens.pop(0)
        # If there was only one token, it is a string or an id
        if not lex_tokens:
            if not t[TYPE] in [ID, STRING]:
                raise TokenError(t)
            self.string_id = t
        else:
            self.expression = Expression(lex_tokens)

    def __str__(self):
        if self.string_id:
            assert isinstance(self.string_id, tuple)
            return self.string_id[VALUE]
        else:
            return str(self.expression)


class Predicate:
    id = None
    parameterList = None

    def __init__(self, lex_tokens):
        self.parameterList = list([])
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
        t = lex_tokens.pop(0)
        if not t[TYPE] in [STRING, ID, LEFT_PAREN]:
            raise TokenError(t)

        if t[TYPE] in [STRING, ID]:
            self.parameterList.append(Parameter(list([t])))
        # If it is a left parenthesis, then grab tokens until we are palindrome and pass to parameter
        elif t[TYPE] == LEFT_PAREN:
            t_tokens = list([])
            palindrome = 1
            t_tokens.append(t)
            # Grab tokens until palindrome is zero
            while palindrome > 0 and lex_tokens:
                t = lex_tokens.pop(0)
                if t[TYPE] == RIGHT_PAREN:
                    palindrome -= 1
                elif t[TYPE] == LEFT_PAREN:
                    palindrome += 1
                if palindrome != 0: t_tokens.append(t)
            self.parameterList.append(Parameter(t_tokens))
            t_tokens.clear()

        while len(lex_tokens) > 1:
            # Check for comma
            t = lex_tokens.pop(0)
            if not t[TYPE] == COMMA:
                raise TokenError(t)

            # Check for another parameter
            t = lex_tokens.pop(0)
            if not t[TYPE] in [STRING, ID, LEFT_PAREN]:
                raise TokenError(t)

            if t[TYPE] in [STRING, ID]:
                self.parameterList.append(Parameter(list([t])))
            # If it is a left parenthesis, then grab tokens until we are palindrome and pass to parameter
            elif t[TYPE] == LEFT_PAREN:
                t_tokens = list([])
                palindrome = 1
                t_tokens.append(t)
                # Grab tokens until palindrome is zero
                while palindrome > 0 and lex_tokens > 1:
                    t = lex_tokens.pop(0)
                    t_tokens.append(t)
                    if t[TYPE] == RIGHT_PAREN:
                        palindrome -= 1
                    elif t[TYPE] == LEFT_PAREN:
                        palindrome += 1
                self.parameterList.append(Parameter(t_tokens))
                t_tokens.clear()

        if not lex_tokens:
            raise TokenError(t)
        t = lex_tokens.pop(0)
        if not t[TYPE] == RIGHT_PAREN:
            raise TokenError(t)

        if lex_tokens:
            raise TokenError(lex_tokens.pop(0))

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

    def __hash__(self):
        """
        This is necessary if we want to use queries as a key in lab 3
        :return: The hashed form of the string representation of this class
        """
        return hash(str(self))


class Rule:
    head = None
    predicates = None

    def __init__(self, lex_tokens):
        t_tokens = list()
        palindrome = 0
        while len(lex_tokens) > 1:
            t = lex_tokens.pop(0)
            t_tokens.append(t)
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
                        self.head = Scheme(t_tokens)
                        if not lex_tokens:
                            raise TokenError(t)
                        t = lex_tokens.pop(0)
                        if not t[TYPE] == COLON_DASH:
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
                            if not t[TYPE] == COMMA and len(lex_tokens) > 1:
                                raise TokenError(t)
                    t_tokens.clear()
                else:
                    # We haven't balanced parenthesis yet
                    pass

        if not t[TYPE] == PERIOD:
            raise TokenError(t)

        if t_tokens or palindrome:
            raise TokenError(t_tokens.pop())
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

        t_tokens = list()
        while len(lex_tokens) > 1:
            t = lex_tokens.pop(0)
            t_tokens.append(t)
            # Once we reach a period it is a new rule
            if t[TYPE] == PERIOD:
                self.rules.append(Rule(t_tokens))
                t_tokens.clear()

        t = lex_tokens.pop(0)

        if t_tokens:
            t_tokens.append(t)
            Rule(t_tokens)

        if not t[TYPE] == QUERIES:
            raise TokenError(t)

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

        t_tokens = list()
        while len(lex_tokens) > 1:
            t = lex_tokens.pop(0)
            # Once we reach a question mark it is a new query
            if t[TYPE] == Q_MARK:
                last = t_tokens.pop()
                if not last[TYPE] == RIGHT_PAREN:
                    raise TokenError(t)
                t_tokens.append(last)
                self.queries.append(Predicate(t_tokens))
                t_tokens.clear()
            else:
                t_tokens.append(t)

        if not t[TYPE] == Q_MARK:
            t = lex_tokens.pop(0)
            raise TokenError(t)

        t = lex_tokens.pop(0)

        # If there are leftover tokens then turn them into a predicate to throw the right token error
        if t_tokens:
            t_tokens.append(t)
            Predicate(t_tokens)

        if not t[TYPE] == EOF:
            raise TokenError(t)

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
        ignore_types = [WHITESPACE, COMMENT]
        lex_tokens = [t for t in lex_tokens if not t[TYPE] in ignore_types]
        t_tokens = list()
        iteration = None
        for t in lex_tokens:
            t_tokens.append(t)
            if t[TYPE] == SCHEMES and not iteration:
                iteration = SCHEMES
            # If iteration hasn't been defined and the first token wasn't a scheme we need to stop
            elif not iteration:
                raise TokenError(t)
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
                # Make sure it ended correctly
                t_tokens.clear()
                iteration = QUERIES
            elif t[TYPE] == EOF and iteration == QUERIES:
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


def main(d_file, part=2, debug=False):
    result = ""
    if not (1 <= part <= 2):
        raise ValueError("Part must be either 1 or 2")

    if debug: print("Parsing '%s'" % d_file)

    tokens = lexical_analyzer.scan(d_file)

    if debug:
        # Print out traces on token errors
        datalog = DatalogProgram(tokens)
        result += "Success!\n"
        if part == 2:
            result += str(datalog) + "\n"
    else:
        # Ignore traces on token errors
        try:
            datalog = DatalogProgram(tokens)
            result += "Success!\n"
            if part == 2:
                result += str(datalog) + "\n"
        except TokenError as t:
            return 'Failure!\n  (%s,"%s",%s)\n' % tuple(literal_eval(str(t)))
    return result


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

    str(main(arg.file, part=int(arg.part), debug=arg.debug))
