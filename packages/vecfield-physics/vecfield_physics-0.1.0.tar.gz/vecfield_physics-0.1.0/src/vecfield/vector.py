import math


class Vec:
    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)

    def __add__(self, other):
        return Vec(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vec(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float):
        return Vec(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__

    def dot(self, other):
        return self.x * other.x + self.y * other.y

    def cross(self, other):
        return self.x * other.y - self.y * other.x

    def mag(self):
        return math.sqrt(self.x**2 + self.y**2)

    def unit(self):
        m = self.mag()
        if m == 0:
            raise ValueError("Zero vector has no direction")
        return Vec(self.x / m, self.y / m)

    def __repr__(self):
        return f"Vec(x={self.x}, y={self.y})"
