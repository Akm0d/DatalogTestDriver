#!/usr/bin/env python3
from difflib import unified_diff
from termcolor import colored


def ColorDiff(a: str or list, b: str or list):
    if isinstance(a, str):
        a = a.splitlines(1)
    if isinstance(b, str):
        b = b.splitlines(1)

    diff = unified_diff(b, a)
    output = ""
    for line in diff:
        line = line.rstrip('\n')
        if (line[-2:] == '@@' and line[:2] == '@@') or line in ['--- ', '+++ ']:
            pass
        elif line[0] == '-':
            # This is the expected/correct value
            output += colored(line[1:], 'green')
            # If this is lab 1 then I will build a list of offending tokens
        elif line[0] == '+':
            # This is what the user actually produced
            output += colored(line[1:], 'red')
        else:
            output += colored(line.lstrip(' '), 'white')
    return output
