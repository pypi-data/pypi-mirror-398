from LscCalculator import *


class Number:
    def __init__(self, number):
        self.number = self.toNum(number)

    def toNum(self, n):
        self.number = self.number
        if not isinstance(n, (int, float)):
            if "." in str(n):
                return float(n)
            else:
                return int(n)
        else:
            return n

    def __repr__(self):
        return f"Number({self.number})"

    def __add__(self, other):
        return Number(nc().addition(self.number, self.toNum(other)))

    def __sub__(self, other):
        return Number(nc().subtraction(self.number, self.toNum(other)))

    def __mul__(self, other):
        return Number(nc().multiplication(self.number, self.toNum(other)))

    def __truediv__(self, other):
        return Number(nc().division(self.number, self.toNum(other)))

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

    def __eq__(self, other):
        return self.number == self.toNum(other)

    def __ne__(self, other):
        return self.number != self.toNum(other)

    def __lt__(self, other):
        return self.number < self.toNum(other)

    def __gt__(self, other):
        return self.number > self.toNum(other)

    def __le__(self, other):
        return self.number <= self.toNum(other)

    def __ge__(self, other):
        return self.number >= self.toNum(other)


if __name__ == '__main__':
    n1 = Number('1')
    n1 += 13
    n2 = Number('10')
    n1 -= n2
    n21 = Number(input())
    print(n21 / Number(21))
    print(n1 == n2)
