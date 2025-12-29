from .config import CalcSettings


class CalculatorService:
    def add(self, a: float, b: float) -> float:
        return round(a + b, CalcSettings.PRECISION)

    def subtract(self, a: float, b: float) -> float:
        return round(a - b, CalcSettings.PRECISION)

    def multiply(self, a: float, b: float) -> float:
        return round(a * b, CalcSettings.PRECISION)

    def divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError(CalcSettings.ERR_DIV_ZERO)
        return round(a / b, CalcSettings.PRECISION)
