import unittest

from ometa.runtime import ParseError

from akumabot.calculate import (
    grammar, calculate_expression, CalculatorParseError
)


class GrammarTestCase(unittest.TestCase):
    _integers = (
        '123',
        '-123',
    )
    _floats = (
        '0.1',
        '1.0',
        '123.567',
        '-123.567',
    )
    _scinotes = (
        '1.234e3',
        '-1.234e3',
        '1.234e+3',
        '1.234e-3',
        '1e-3',
    )
    def _run_rule(self, rule, expression):
        rulerunner = getattr(grammar(expression), rule)
        return rulerunner()

    def assertRuleReturns(self, rule, expression, expected):
        result = self._run_rule(rule, expression)
        self.assertEqual(result, expected)

    def assertRuleMatches(self, rule, expression):
        result = self._run_rule(rule, expression)
        self.assertEqual(result, expression)

    def assertRuleFails(self, rule, expression):
        with self.assertRaises(ParseError):
            self._run_rule(rule, expression)

    def test_integer(self):
        for intstring in self._integers:
            self.assertRuleMatches('integer', intstring)

    def test_float(self):
        for floatstring in self._floats:
            self.assertRuleMatches('float', floatstring)

    def test_scinote(self):
        for scinotestring in self._scinotes:
            self.assertRuleMatches('scinote', scinotestring)

    def test_number_integers(self):
        for intstring in self._integers:
            self.assertRuleReturns('number', intstring, float(intstring))

        self.assertRuleFails('number', 'abcdef')

    def test_number_floats(self):
        for floatstring in self._floats:
            self.assertRuleReturns('number', floatstring, float(floatstring))

        self.assertRuleFails('number', '.2')
        self.assertRuleFails('number', '.')
        self.assertRuleFails('number', '1.')

    def test_number_scinotes(self):
        for scinotestring in self._scinotes:
            self.assertRuleReturns(
                'number', scinotestring, float(scinotestring))

    def test_number_negative(self):
        self.assertRuleReturns('number', '-1', -1.0)
        self.assertRuleReturns('number', '-1.0', -1.0)
        self.assertRuleReturns('number', '-1.0e0', -1.0)

    def test_parens_basic(self):
        self.assertRuleReturns('parens', '(23)', 23.0)
        self.assertRuleReturns('parens', '(1 + 2)', 3.0)


class CalculateExpressionTestCase(unittest.TestCase):
    def assertExpressionEquals(self, expression, expected):
        result = calculate_expression(expression)
        self.assertEqual(result, expected)

    def test_failure_raises_correct_exception(self):
        with self.assertRaises(CalculatorParseError):
            calculate_expression('bogus crap')

    def test_basic_addition(self):
        self.assertExpressionEquals('1 + 2', 3)

    def test_basic_subtraction(self):
        self.assertExpressionEquals('3 - 2', 1)
        self.assertExpressionEquals('1 - 2', -1)

    def test_basic_multiplication(self):
        self.assertExpressionEquals('2 * 3', 6)

    def test_basic_division(self):
        self.assertExpressionEquals('2 / 1', 2)
        self.assertExpressionEquals('5 / 2', 2.5)

    def test_mul_before_add(self):
        self.assertExpressionEquals('5 * 2 + 1', 11)
        self.assertExpressionEquals('1 + 5 * 2', 11)
