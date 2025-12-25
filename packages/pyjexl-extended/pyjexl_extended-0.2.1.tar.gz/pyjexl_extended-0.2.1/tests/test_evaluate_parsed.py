import pytest
from pyjexl.jexl import JEXL

def test_evaluate_with_parsed_expression():
    jexl = JEXL()
    expr = '2 + 3'
    parsed = jexl.parse(expr)
    # Should work with parsed expression
    assert jexl.evaluate(parsed) == 5
    # Should work with string as before
    assert jexl.evaluate(expr) == 5
