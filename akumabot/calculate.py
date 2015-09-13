"""
Original from parsley tutorial:
http://parsley.readthedocs.org/en/latest/tutorial.html#building-a-calculator
"""
import operator

from parsley import makeGrammar
from ometa.runtime import ParseError as _ParsleyParseError


class CalculatorParseError(Exception):
    pass


def calculate_expression(expression):
    try:
        return grammar(expression).expr()
    except _ParsleyParseError:
        raise CalculatorParseError


_grammar_text = """
integer = <'-'? digit+>:val -> val
float = <integer '.' digit+>:val -> val
scinote = <(float | integer) ('e' | 'E') ('+' | '-')? digit+>:val -> val
number =  <scinote | float | integer>:n -> float(n)
parens = '(' ws expr:e ws ')' -> e
value = number | parens
ws = ' '*
add = '+' ws expr2:n -> ('+', n)
sub = '-' ws expr2:n -> ('-', n)
mul = '*' ws expr2:n -> ('*', n)
div = '/' ws expr2:n -> ('/', n)

addsub = ws (add | sub)
muldiv = ws (mul | div)


expr = expr2:left addsub*:right -> calculate(left, right)
expr2 = value:left muldiv*:right -> calculate(left, right)
"""


operations = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
}


def _calculate(start, pairs):
    result = start
    for op, value in pairs:
        result = operations[op](result, value)
    return result


grammar = makeGrammar(_grammar_text, {'calculate': _calculate})
