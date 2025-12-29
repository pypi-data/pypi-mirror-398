import pytest
from calculator_pkg.service import CalculatorService, CalcSettings


def test_add_success():

    service = CalculatorService()
    a, b = 10, 5.5

    result = service.add(a, b)

    assert result == 15.5


def test_divide_success():
    service = CalculatorService()
    assert service.divide(10, 2) == 5.0


def test_divide_by_zero():
    service = CalculatorService()

    with pytest.raises(ValueError) as excinfo:
        service.divide(10, 0)

    assert str(excinfo.value) == CalcSettings.ERR_DIV_ZERO


def test_subtract_success():
    service = CalculatorService()
    assert service.subtract(10.5, 5) == 5.5


def test_multiply_success():
    service = CalculatorService()
    assert service.multiply(2.5, 3) == 7.5


def test_precision_handling():
    service = CalculatorService()
    assert service.divide(2, 3) == 0.67
