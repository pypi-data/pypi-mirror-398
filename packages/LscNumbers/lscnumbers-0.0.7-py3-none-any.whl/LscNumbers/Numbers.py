from LscCalculator import *


class Number:
    def __init__(self, number):
        if not isinstance(number, (int, float)):
            if "." in str(number):
                self.number = float(number)
            else:
                self.number = int(number)
        else:
            self.number = number

    def __repr__(self):
        return f"Number({self.number})"

    def __add__(self, other):
        return Number(nc().addition(self.number, other.number) if isinstance(other, Number) else nc().addition(self.number, other))

    def __sub__(self, other):
        return Number(nc().subtraction(self.number, other.number) if isinstance(other, Number) else nc().subtraction(self.number, other))

    def __mul__(self, other):
        return Number(nc().multiplication(self.number, other.number) if isinstance(other, Number) else nc().multiplication(self.number, other))

    def __truediv__(self, other):
        return Number(nc().division(self.number, other.number) if isinstance(other, Number) else nc().division(self.number, other))

    def __int__(self):
        return int(self.number)

    def __float__(self):
        return float(self.number)

    def __getattr__(self, item):
        pass

    def __round__(self, n=None):
        return Number(round(self.number, n))

    def __pow__(self, power, modulo=None):
        return Number(nc().power(self.number, power, modulo))

    def __str__(self):
        return str(self.number)


if __name__ == '__main__':
    n1 = Number('1')
    n1 += 13
    n2 = Number('10')
    n1 -= n2
    n21 = Number(input())
    print(n21 / Number(21))
