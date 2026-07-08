import math

import pytest

from app.services.scoring import apri, de_ritis, fib4, zone


# 10 hand-picked cases, cross-checked against the manual FIB-4 formula
# fib4 = (age * ast) / (plt * sqrt(alt))
CASES = [
    # age, ast, alt, plt
    (25, 20, 20, 250),
    (45, 40, 35, 180),
    (60, 80, 30, 90),
    (70, 120, 50, 60),
    (30, 15, 25, 300),
    (55, 60, 45, 150),
    (65, 100, 40, 120),
    (40, 35, 35, 200),
    (50, 90, 20, 80),
    (80, 150, 60, 50),
]


@pytest.mark.parametrize("age,ast,alt,plt", CASES)
def test_fib4_matches_manual_calculation(age, ast, alt, plt):
    expected = (age * ast) / (plt * math.sqrt(alt))
    assert fib4(age, ast, alt, plt) == pytest.approx(expected)


def test_fib4_zone_thresholds():
    assert zone(1.0) == "low"
    assert zone(1.3) == "grey"
    assert zone(2.0) == "grey"
    assert zone(2.67) == "grey"
    assert zone(3.0) == "high"


def test_fib4_guards_against_missing_inputs():
    assert fib4(None, 20, 20, 200) is None
    assert fib4(40, None, 20, 200) is None
    assert fib4(40, 20, None, 200) is None
    assert fib4(40, 20, 20, None) is None


def test_fib4_guards_against_division_by_zero():
    assert fib4(40, 20, 0, 200) is None
    assert fib4(40, 20, 20, 0) is None


def test_zone_none_when_fib4_missing():
    assert zone(None) is None


def test_apri_matches_manual_calculation():
    # apri = (ast / ast_uln) / plt * 100
    expected = (80 / 40) / 100 * 100
    assert apri(80, 40, 100) == pytest.approx(expected)


def test_apri_guards_against_division_by_zero():
    assert apri(80, 0, 100) is None
    assert apri(80, 40, 0) is None
    assert apri(None, 40, 100) is None


def test_de_ritis_matches_manual_calculation():
    assert de_ritis(80, 40) == pytest.approx(2.0)


def test_de_ritis_guards_against_division_by_zero():
    assert de_ritis(80, 0) is None
    assert de_ritis(None, 40) is None
