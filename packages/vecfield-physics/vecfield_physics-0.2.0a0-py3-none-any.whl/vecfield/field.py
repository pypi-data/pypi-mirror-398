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
        g = self.grid

        # ---- bounds check ----
        if x < g.xmin or x > g.xmax or y < g.ymin or y > g.ymax:
            raise ValueError("Point outside grid")

        # ---- map to fractional grid coordinates ----
        gx = (x - g.xmin) / g.dx
        gy = (y - g.ymin) / g.dy

        i = int(gx)
        j = int(gy)

        # ---- edge safety ----
        if i >= g.resolution - 1:
            i = g.resolution - 2
        if j >= g.resolution - 1:
            j = g.resolution - 2

        tx = gx - i
        ty = gy - j

        v00 = self.values[i, j]
        v10 = self.values[i + 1, j]
        v01 = self.values[i, j + 1]
        v11 = self.values[i + 1, j + 1]

        # ---- bilinear interpolation ----
        return (
            (1 - tx) * (1 - ty) * v00 +
            tx * (1 - ty) * v10 +
            (1 - tx) * ty * v01 +
            tx * ty * v11
        )


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
        
    def __call__(self, x, y):
        g = self.grid

        # ---- bounds check ----
        if x < g.xmin or x > g.xmax or y < g.ymin or y > g.ymax:
            raise ValueError("Point outside grid")

        gx = (x - g.xmin) / g.dx
        gy = (y - g.ymin) / g.dy

        i = int(gx)
        j = int(gy)

        if i >= g.resolution - 1:
            i = g.resolution - 2
        if j >= g.resolution - 1:
            j = g.resolution - 2

        tx = gx - i
        ty = gy - j

        # ---- interpolate Fx ----
        fx = (
            (1 - tx) * (1 - ty) * self.Fx[i, j] +
            tx * (1 - ty) * self.Fx[i + 1, j] +
            (1 - tx) * ty * self.Fx[i, j + 1] +
            tx * ty * self.Fx[i + 1, j + 1]
        )

        # ---- interpolate Fy ----
        fy = (
            (1 - tx) * (1 - ty) * self.Fy[i, j] +
            tx * (1 - ty) * self.Fy[i + 1, j] +
            (1 - tx) * ty * self.Fy[i, j + 1] +
            tx * ty * self.Fy[i + 1, j + 1]
        )

        return Vec(fx, fy)
    
    def streamlines(
        self,
        seeds,
        step=0.05,
        n_steps=500,
        direction="both",
        min_speed=1e-9,
    ):
        """
        Compute streamlines (field lines) for this vector field using RK4.

        Parameters
        ----------
        seeds : list[tuple[float, float]]
            Starting points [(x0, y0), ...]
        step : float
            Step size in arc-length-ish parameter. Larger = faster/rougher.
        n_steps : int
            Max steps in each direction.
        direction : {"forward", "backward", "both"}
            Integrate along +F, -F, or both and stitch.
        min_speed : float
            Stop if |F| < min_speed (near equilibrium).

        Returns
        -------
        list[list[tuple[float, float]]]
            A list of polylines, each a list of (x, y) points.
        """
        if direction not in {"forward", "backward", "both"}:
            raise ValueError("direction must be 'forward', 'backward', or 'both'")

        def rk4_step(x, y, h, sgn):
            # sgn = +1 for forward, -1 for backward
            # k1
            v1 = self(x, y)
            if v1.mag() < min_speed:
                return None
            k1x, k1y = sgn * v1.x, sgn * v1.y

            # k2
            v2 = self(x + 0.5 * h * k1x, y + 0.5 * h * k1y)
            if v2.mag() < min_speed:
                return None
            k2x, k2y = sgn * v2.x, sgn * v2.y

            # k3
            v3 = self(x + 0.5 * h * k2x, y + 0.5 * h * k2y)
            if v3.mag() < min_speed:
                return None
            k3x, k3y = sgn * v3.x, sgn * v3.y

            # k4
            v4 = self(x + h * k3x, y + h * k3y)
            if v4.mag() < min_speed:
                return None
            k4x, k4y = sgn * v4.x, sgn * v4.y

            xn = x + (h / 6.0) * (k1x + 2 * k2x + 2 * k3x + k4x)
            yn = y + (h / 6.0) * (k1y + 2 * k2y + 2 * k3y + k4y)
            return xn, yn

        def integrate_one(seed, sgn):
            x, y = float(seed[0]), float(seed[1])
            pts = [(x, y)]

            for _ in range(int(n_steps)):
                try:
                    nxt = rk4_step(x, y, float(step), sgn)
                    if nxt is None:
                        break
                    x, y = nxt
                    pts.append((x, y))
                except ValueError:
                    # out of bounds from self(x,y)
                    break

            return pts

        lines = []
        for seed in seeds:
            if direction == "forward":
                lines.append(integrate_one(seed, +1))
            elif direction == "backward":
                lines.append(integrate_one(seed, -1))
            else:
                back = integrate_one(seed, -1)
                fwd = integrate_one(seed, +1)

                # stitch: reverse(back) without repeating seed + fwd
                stitched = list(reversed(back[:-1])) + fwd
                lines.append(stitched)

        return lines



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

    def plot_streamlines(self, seeds, **kwargs):
        from .viz import plot_streamlines
        lines = self.streamlines(seeds, **{k: v for k, v in kwargs.items() if k != "linewidth"})
        plot_streamlines(lines, linewidth=kwargs.get("linewidth", 1.0))
        return lines
    
    def seed_circle(self, radius, n=16, center=(0.0, 0.0)):
        """
        Generate n seed points evenly spaced on a circle.

        Parameters
        ----------
        radius : float
            Circle radius.
        n : int
            Number of seeds.
        center : tuple[float, float]
            Center of the circle.

        Returns
        -------
        list[tuple[float, float]]
        """
        import math

        cx, cy = center
        seeds = []

        for k in range(n):
            theta = 2 * math.pi * k / n
            x = cx + radius * math.cos(theta)
            y = cy + radius * math.sin(theta)
            seeds.append((x, y))

        return seeds

    def seed_grid(self, nx=6, ny=6, margin=0.05):
        """
        Generate seed points on a uniform grid inside the domain.

        Parameters
        ----------
        nx, ny : int
            Number of seeds in x and y directions.
        margin : float
            Fractional margin to avoid boundaries.

        Returns
        -------
        list[tuple[float, float]]
        """
        g = self.grid

        xmin = g.xmin + margin * (g.xmax - g.xmin)
        xmax = g.xmax - margin * (g.xmax - g.xmin)
        ymin = g.ymin + margin * (g.ymax - g.ymin)
        ymax = g.ymax - margin * (g.ymax - g.ymin)

        xs = [xmin + i * (xmax - xmin) / (nx - 1) for i in range(nx)]
        ys = [ymin + j * (ymax - ymin) / (ny - 1) for j in range(ny)]

        return [(x, y) for x in xs for y in ys]

    def at_index(self, i, j):
        return Vec(self.Fx[i, j], self.Fy[i, j])
    
    
