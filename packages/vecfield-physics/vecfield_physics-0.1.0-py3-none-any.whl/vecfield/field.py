import numpy as np
from .grid import SpatialGrid
from .vector import Vec


class ScalarField:
    def __init__(self, func, bounds, resolution=100):
        self.func = func
        self.grid = SpatialGrid(bounds, resolution)
        self.values = self._sample()

    def _sample(self):
        X, Y = self.grid.X, self.grid.Y
        return self.func(X, Y)

    def __call__(self, x, y):
        return self.func(x, y)

    # ---- calculus ----
    def grad(self):
        from .operators import grad
        return grad(self)

    def laplacian(self):
        return self.grad().div()

    # ---- visualization ----
    def plot(self, **kwargs):
        from .viz import plot_scalar
        plot_scalar(self, **kwargs)


class VectorField:
    def __init__(self, Fx, Fy, grid: SpatialGrid):
        self.grid = grid
        self.Fx = np.asarray(Fx, dtype=float)
        self.Fy = np.asarray(Fy, dtype=float)

        shape = (grid.resolution, grid.resolution)
        if self.Fx.shape != shape or self.Fy.shape != shape:
            raise ValueError("VectorField component arrays have wrong shape")

    # ---- arithmetic ----
    def _check(self, other):
        if not isinstance(other, VectorField):
            raise TypeError("Requires VectorField")
        if self.grid is not other.grid:
            raise ValueError("VectorFields must share grid")

    def __add__(self, other):
        self._check(other)
        return VectorField(self.Fx + other.Fx, self.Fy + other.Fy, self.grid)

    def __sub__(self, other):
        self._check(other)
        return VectorField(self.Fx - other.Fx, self.Fy - other.Fy, self.grid)

    def __neg__(self):
        return VectorField(-self.Fx, -self.Fy, self.grid)

    def __mul__(self, scalar):
        return VectorField(self.Fx * scalar, self.Fy * scalar, self.grid)

    __rmul__ = __mul__

    def __truediv__(self, scalar):
        if scalar == 0:
            raise ZeroDivisionError
        return VectorField(self.Fx / scalar, self.Fy / scalar, self.grid)

    # ---- calculus ----
    def div(self):
        from .operators import div
        return div(self)

    def curl(self):
        from .operators import curl
        return curl(self)

    def magnitude(self):
        g = self.grid

        def dummy(x, y):
            return 0.0

        mag = ScalarField(dummy, (g.xmin, g.xmax, g.ymin, g.ymax), g.resolution)
        mag.values = np.sqrt(self.Fx**2 + self.Fy**2)
        mag.grid = g
        return mag

    # ---- visualization ----
    def quiver(self, **kwargs):
        from .viz import plot_vector
        plot_vector(self, **kwargs)

    def at_index(self, i, j):
        return Vec(self.Fx[i, j], self.Fy[i, j])
