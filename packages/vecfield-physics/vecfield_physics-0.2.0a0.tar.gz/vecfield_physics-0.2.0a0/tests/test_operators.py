import numpy as np
from vecfield import ScalarField
from vecfield.field import VectorField
from vecfield.operators import grad, div, curl


def test_grad_of_linear_field():
    # V = 3x + 5y -> grad V = (3, 5) everywhere
    V = ScalarField(lambda x, y: 3*x + 5*y, (-1, 1, -1, 1), resolution=51)
    G = grad(V)

    # Ignore boundaries (they use one-sided differences)
    Fx = G.Fx[1:-1, 1:-1]
    Fy = G.Fy[1:-1, 1:-1]

    assert np.allclose(Fx, 3.0, atol=1e-10)
    assert np.allclose(Fy, 5.0, atol=1e-10)


def test_grad_of_quadratic_field_center_point():
    # V = x^2 + y^2 -> grad = (2x, 2y)
    V = ScalarField(lambda x, y: x**2 + y**2, (-2, 2, -2, 2), resolution=101)
    G = grad(V)

    # pick center index corresponds to x=0,y=0
    mid = V.grid.resolution // 2
    assert abs(G.Fx[mid, mid] - 0.0) < 1e-8
    assert abs(G.Fy[mid, mid] - 0.0) < 1e-8

def test_div_of_constant_field():
    # F = (2, -3) -> div F = 0 everywhere
    V = ScalarField(lambda x, y: x*0, (-1, 1, -1, 1), resolution=51)
    g = V.grid

    Fx = np.full((g.resolution, g.resolution), 2.0)
    Fy = np.full((g.resolution, g.resolution), -3.0)
    F = VectorField(Fx, Fy, g)

    d = div(F).values[1:-1, 1:-1]
    assert np.allclose(d, 0.0, atol=1e-10)


def test_div_of_linear_field():
    # F = (x, y) -> div F = 1 + 1 = 2
    V = ScalarField(lambda x, y: x*0, (-2, 2, -2, 2), resolution=101)
    g = V.grid

    Fx = g.X
    Fy = g.Y
    F = VectorField(Fx, Fy, g)

    d = div(F).values[1:-1, 1:-1]  # ignore boundaries
    assert np.allclose(d, 2.0, atol=1e-8)

def test_curl_of_zero_field():
    V = ScalarField(lambda x, y: 0*x, (-1, 1, -1, 1), resolution=51)
    g = V.grid

    Fx = np.zeros((g.resolution, g.resolution))
    Fy = np.zeros((g.resolution, g.resolution))
    F = VectorField(Fx, Fy, g)

    c = curl(F).values[1:-1, 1:-1]
    assert np.allclose(c, 0.0)


def test_curl_of_rotational_field():
    # F = (-y, x) -> curl = 2
    V = ScalarField(lambda x, y: 0*x, (-2, 2, -2, 2), resolution=101)
    g = V.grid

    Fx = -g.Y
    Fy = g.X
    F = VectorField(Fx, Fy, g)

    c = curl(F).values[1:-1, 1:-1]
    assert np.allclose(c, 2.0, atol=1e-8)

def test_method_syntax():
    V = ScalarField(lambda x, y: x**2 + y**2, (-2,2,-2,2), resolution=51)

    E = -V.grad()
    rho = E.div()
    omega = E.curl()

    mid = V.grid.resolution // 2
    assert abs(omega.values[mid, mid]) < 1e-8

def test_laplacian_of_quadratic():
    # V = x^2 + y^2 -> ∇²V = 2 + 2 = 4
    from vecfield import ScalarField

    V = ScalarField(lambda x, y: x**2 + y**2, (-2,2,-2,2), resolution=101)
    lapV = V.laplacian()

    mid = V.grid.resolution // 2
    assert abs(lapV.values[mid, mid] - 4.0) < 1e-6

def test_vectorfield_magnitude():
    from vecfield import ScalarField
    import numpy as np

    V = ScalarField(lambda x, y: 0*x, (-1,1,-1,1), resolution=21)
    g = V.grid

    Fx = np.ones((g.resolution, g.resolution)) * 3
    Fy = np.ones((g.resolution, g.resolution)) * 4

    from vecfield.field import VectorField
    F = VectorField(Fx, Fy, g)

    mag = F.magnitude()
    assert np.allclose(mag.values, 5.0)

def test_neg_grad():
    V = ScalarField(lambda x, y: x**2 + y**2, (-2,2,-2,2), resolution=51)
    G = grad(V)
    E = -G  # should now work cleanly

    mid = V.grid.resolution // 2
    assert abs(E.Fx[mid, mid]) < 1e-8
    assert abs(E.Fy[mid, mid]) < 1e-8



