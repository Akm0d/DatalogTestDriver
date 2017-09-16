#!/usr/bin/env python3
import lexical_analyzer
import logging

from tokens import TokenError, TokenType, Token

logger = logging.getLogger(__name__)

recent_token = None


class Parser:
    # All classes will read from this list of shared tokens until they are gone
    unused_tokens = list()

    # Share the most recently parsed token amongst all instances of this class

    def __init__(self, grammar: list = None, tokens: list = None, root: bool = False, lazy: bool = False):
        """
        :param grammar: A list of tokens in the order they should be expected.
        If the token is a list, then allow zero or more of the tokens in the list.
        If the token is a set, then the match one of the objects in the set
        If the token is a class, then return an instance of that class and continue parsing the remaining tokens
        :param tokens: Only the base class should add tokens to the list of unused_tokens with this parameter.
        unused_tokens are shared amongst all instances of the Parser class and its children
        :param root: If This instance is the base, then any leftover tokens will be treated as an error

        """
        self.grammar = grammar if grammar is not None else self.grammar
        if tokens is not None:
            self.unused_tokens.extend(tokens)
        self.objects = self._parse_unused_tokens(lazy=lazy)

        if root and self.unused_tokens:
            raise TokenError(self.get_token())

    def _parse_unused_tokens(self, grammar: list = None, lazy: bool = False):
        """
        :param grammar: The grammar to use, if none, then it will default to the class grammar
        :param lazy: Don't raise any errors or remove from the list if the match fails
        :return: The list of objects that matched the grammar
        The list will contain instances of Token and Parser
        """
        global recent_token
        if grammar is None:
            grammar = self.grammar
        objects = list()
        for g in grammar:
            if isinstance(g, TokenType):
                t = self.get_token()
                objects.append(t)
                if not t.type == g:
                    if lazy:
                        self.put_back_tokens(objects)
                        return []
                    else:
                        raise TokenError(t)
                recent_token = t
            elif isinstance(g, list):
                # keep matching in the list until something doesn't match
                # print("GO:" + " ".join([str(x.__class__) for x in g]))
                inner_list = self._parse_unused_tokens(lazy=True, grammar=g)
                while inner_list:
                    # print([str(x) for x in inner_list])
                    objects.append(inner_list)
                    inner_list = self._parse_unused_tokens(lazy=True, grammar=g)
                    # print([str(x) for x in inner_list])
            elif isinstance(g, set):
                for s in g:
                    inner_list = self._parse_unused_tokens(lazy=True, grammar=[s])
                    while inner_list:
                        objects.append(inner_list)
                        inner_list = self._parse_unused_tokens(lazy=True, grammar=[s])
            elif isinstance(g, type):
                # print("TYPE: " + g.__name__)
                parser = g(lazy=lazy)
                assert isinstance(parser, Parser)
                if parser:
                    objects.append(parser)
                else:
                    if lazy:
                        self.put_back_tokens(objects)
                        return []
                    else:
                        raise TokenError(recent_token)
            else:
                raise ValueError("Unrecognized type in grammar: %s" % g.__class__)

        return objects
    
    def put_back_tokens(self, objects):
        logger.debug("Putting back tokens %s" % " ".join([str(x) for x in objects]))
        for o in reversed(objects):
            if isinstance(o, Token):
                self.unused_tokens.insert(0, o)
            elif isinstance(o, Parser):
                for T in reversed(o.objects):
                    self.unused_tokens.insert(0, T)

    def get_token(self):
        """
        :return: The top token from the list
        """
        global recent_token
        if self.unused_tokens:
            return self.unused_tokens.pop(0)
        else:
            # If there are no more tokens then raise an error on the last token seen
            raise TokenError(recent_token)


class Scheme(Parser):
    """
    id: The main ID Token
    idList: A list of ID tokens
    """
    grammar = [
        TokenType.ID,
        TokenType.LEFT_PAREN,
        TokenType.ID,
        [
            TokenType.COMMA,
            TokenType.ID
        ],
        TokenType.RIGHT_PAREN
    ]

    def __init__(self, lazy: bool = False):
        super().__init__(lazy=lazy)
        
        try:
            self.id = self.objects[0]
            self.idList = [self.objects[2]]
        except IndexError:
            self.id = None
            self.idList = None

        for o in self.objects[3:]:
            if isinstance(o, list):
                self.idList.extend([t for t in o if t.type == TokenType.ID])

    def __str__(self):
        return "{}({})".format(self.id.value, ",".join(t.value for t in self.idList))
    
    def __bool__(self):
        return False if (self.id is None or self.idList is None) else True


class Schemes(Parser):
    """
    schemes: a list of Scheme tokens
    """
    grammar = [
        Scheme,
        [
            Scheme
        ]
    ]

    def __init__(self, lazy=False):
        super().__init__(lazy=lazy)

        self.schemes = [self.objects[0]] + self.objects[1]

        self.objects.clear()

    def __str__(self):
        return "Schemes({}):\n{}\n".format(len(self.schemes), "\n".join("  " + str(s) for s in self.schemes))


class Domain(set):
    def __str__(self):
        return "Domain({}):{}{}".format(
            len(self),
            "\n" if self else "",
            "\n".join("  " + f.value for f in sorted(self)))


class Fact(Parser):
    """
    id: The main ID token
    stringList: a list of String tokens
    """
    grammar = [
        TokenType.ID,
        TokenType.LEFT_PAREN,
        TokenType.STRING,
        [
            TokenType.COMMA,
            TokenType.STRING
        ],
        TokenType.RIGHT_PAREN,
        TokenType.PERIOD
    ]
    # will this be shared amongst all instances of this class?
    domain = Domain()

    def __init__(self, name: tuple = None, attributes: list = None, lazy: bool = False):
        if name and attributes:
            self.id = name
            self.stringList = attributes
        else:
            super().__init__(lazy=lazy)
            try:
                self.id = self.objects[0]
                self.stringList = [self.objects[2]]
            except IndexError:
                self.id = None
                self.stringList = None

            for o in self.objects[3:]:
                if isinstance(o, list):
                    self.stringList.extend([t for t in o if t.type == TokenType.STRING])

            self.objects.clear()

        # Add facts to the domain
        if self.stringList is not None:
            for t in self.stringList:
                if t.type == TokenType.STRING:
                    self.domain.add(t)

    def __str__(self):
        return "{}({}).".format(self.id.value, ",".join(t.value for t in self.stringList))

    def __bool__(self):
        return False if (self.id is None or self.stringList is None) else True


class Facts(Parser):
    """
    facts
    """
    grammar = [
        Fact,
        [
            Fact
        ]
    ]

    def __init__(self, lazy: bool = True):
        super().__init__(lazy=lazy)
        self.facts = [self.objects[0]] + self.objects[1]

    def __str__(self):
        return "Facts({}):{}{}".format(
            len(self.facts),
            "\n" if self.facts else "",
            "\n".join("  " + str(fact) for fact in self.facts)
        )


class Expression(Parser):
    def __init__(self):
        self.grammar = [TokenType.LEFT_PAREN, Parameter, {TokenType.ADD, TokenType.MULTIPLY}, Parameter,
                        TokenType.RIGHT_PAREN]
        super().__init__()
        self.param_1 = self.objects[1]
        self.operator = self.objects[2]
        self.param_2 = self.objects[3]

    def __str__(self):
        return "({}{}{})".format(str(self.param_1), self.operator.value, str(self.param_2))


class Parameter(Parser):
    def __init__(self):
        self.grammar = [{TokenType.STRING, TokenType.ID, Expression}]
        super().__init__()
        o = self.objects[0]
        self.string_id = None
        self.expression = None
        if isinstance(o, Expression):
            self.expression = o
        else:
            self.string_id = o

    def __str__(self):
        return self.string_id.value if self.string_id else str(self.expression)


class Predicate(Parser):
    grammar = [TokenType.ID, TokenType.LEFT_PAREN, Parameter, [TokenType.COMMA, Parameter], TokenType.RIGHT_PAREN]

    def __init__(self):
        super().__init__()
        self.id = self.objects[0]
        self.parameterList = [self.objects[2]] + self.objects[3]

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


# A headPredicate has the exact same grammar as a scheme
headPredicate = Scheme


class Rule(Parser):
    grammar = [headPredicate, TokenType.COLON_DASH, Predicate, [TokenType.COMMA, Predicate], TokenType.PERIOD]

    def __init__(self):
        super().__init__()
        self.head = self.objects[0]
        self.predicates = [self.objects[2]] + self.objects[3]
        assert isinstance(self.predicates, list)

    def __str__(self):
        return "{}:- {}".format(str(self.head), ",".join(str(p) for p in self.predicates))


class Rules(Parser):
    grammar = [Rule, [TokenType.COMMA, Rule]]

    def __init__(self):
        super().__init__()
        self.rules = [self.objects[0]] + self.objects[1]

    def __str__(self):
        return "Rules({}):\n{}".format(len(self.rules), "\n".join("  " + str(r) for r in self.rules))


class Queries(Parser):
    grammar = [Predicate, TokenType.Q_MARK, [Predicate, TokenType.Q_MARK]]

    def __init__(self):
        super().__init__()
        self.queries = [self.objects[0]] + [o for o in self.objects[2] if isinstance(o, Predicate)]

    def __str__(self):
        return "Queries({}):\n{}".format(len(self.queries), "\n".join("  " + str(q) + "?" for q in self.queries))


class DatalogProgram(Parser):
    grammar = [
        TokenType.SCHEMES, TokenType.COLON, Schemes,
        TokenType.FACTS, TokenType.COLON, Facts,
        # TokenType.RULES, TokenType.COLON, Rules,
        # TokenType.QUERIES, TokenType.COLON, Queries,
        # TokenType.EOF
    ]

    def __init__(self, lex_tokens: list):
        # super().__init__(tokens=lex_tokens, root=True)
        super().__init__(tokens=lex_tokens)
        self.schemes = self.objects[2]
        self.facts = self.objects[5]
        # self.rules = self.objects[8]
        # self.queries = self.objects[11]

    def __str__(self):
        return '{}{}\n{}\n{}\n{}\n'.format(
            self.schemes,
            self.facts,
            "","",
            #self.rules,
            #self.queries,
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
