# tests/test_vector.py

from vecfield.vector import Vec
from vecfield.field import ScalarField
import math
import numpy as np


def test_basic_construction():
    v = Vec(1, 2)
    assert v.x == 1
    assert v.y == 2
    assert len(v) == 2


def test_addition():
    v = Vec(1, 2)
    w = Vec(3, 4)
    r = v + w
    assert r.is_close(Vec(4, 6))


def test_scalar_mult():
    v = Vec(1, -2)
    assert (2 * v).is_close(Vec(2, -4))
    assert (v * 3).is_close(Vec(3, -6))


def test_dot_cross():
    v = Vec(1, 0)
    w = Vec(0, 2)
    assert v.dot(w) == 0
    assert v.cross(w) == 2


def test_magnitude():
    v = Vec(3, 4)
    assert math.isclose(v.mag(), 5)


def test_unit_vector():
    v = Vec(3, 4)
    u = v.unit()
    assert math.isclose(u.mag(), 1)


def test_projection():
    v = Vec(3, 4)
    d = Vec(1, 0)
    p = v.proj(d)
    assert p.is_close(Vec(3, 0))


def test_perp():
    v = Vec(1, 0)
    p = v.perp()
    assert p.is_close(Vec(0, 1))

def test_scalar_field_eval():
    V = ScalarField(lambda x, y: x**2 + y**2, (-1, 1, -1, 1))
    assert V(1, 2) == 5


def test_scalar_field_sampling():
    V = ScalarField(lambda x, y: x + y, (-1, 1, -1, 1), resolution=10)
    assert V.values.shape == (10, 10)


def test_scalar_field_arithmetic():
    V1 = ScalarField(lambda x, y: x, (-1, 1, -1, 1))
    V2 = ScalarField(lambda x, y: y, (-1, 1, -1, 1))
    V = V1 + V2
    assert V(1, 2) == 3
