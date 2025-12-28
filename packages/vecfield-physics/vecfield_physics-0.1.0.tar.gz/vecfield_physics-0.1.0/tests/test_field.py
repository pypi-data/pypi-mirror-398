from vecfield.field import ScalarField, VectorField
import numpy as np


def test_vectorfield_scalar_mult():
    V = ScalarField(lambda x, y: x*0, (-1, 1, -1, 1), resolution=11)
    g = V.grid

    Fx = np.ones((g.resolution, g.resolution))
    Fy = 2*np.ones((g.resolution, g.resolution))
    F = VectorField(Fx, Fy, g)

    G = 3 * F
    assert np.allclose(G.Fx, 3)
    assert np.allclose(G.Fy, 6)


def test_vectorfield_addition():
    V = ScalarField(lambda x, y: x*0, (-1, 1, -1, 1), resolution=11)
    g = V.grid

    F1 = VectorField(np.ones((g.resolution, g.resolution)),
                     np.zeros((g.resolution, g.resolution)), g)

    F2 = VectorField(np.zeros((g.resolution, g.resolution)),
                     np.ones((g.resolution, g.resolution)), g)

    F = F1 + F2
    assert np.allclose(F.Fx, 1)
    assert np.allclose(F.Fy, 1)


