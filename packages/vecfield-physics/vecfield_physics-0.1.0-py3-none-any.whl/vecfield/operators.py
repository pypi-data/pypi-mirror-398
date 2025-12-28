import numpy as np
from .field import ScalarField, VectorField


def grad(V: ScalarField) -> VectorField:
    g = V.grid
    vals = V.values

    dVdx = np.zeros_like(vals)
    dVdy = np.zeros_like(vals)

    dVdx[1:-1, :] = (vals[2:, :] - vals[:-2, :]) / (2 * g.dx)
    dVdx[0, :] = (vals[1, :] - vals[0, :]) / g.dx
    dVdx[-1, :] = (vals[-1, :] - vals[-2, :]) / g.dx

    dVdy[:, 1:-1] = (vals[:, 2:] - vals[:, :-2]) / (2 * g.dy)
    dVdy[:, 0] = (vals[:, 1] - vals[:, 0]) / g.dy
    dVdy[:, -1] = (vals[:, -1] - vals[:, -2]) / g.dy

    return VectorField(dVdx, dVdy, g)


def div(F: VectorField) -> ScalarField:
    g = F.grid

    dFxdx = np.zeros_like(F.Fx)
    dFydy = np.zeros_like(F.Fy)

    dFxdx[1:-1, :] = (F.Fx[2:, :] - F.Fx[:-2, :]) / (2 * g.dx)
    dFxdx[0, :] = (F.Fx[1, :] - F.Fx[0, :]) / g.dx
    dFxdx[-1, :] = (F.Fx[-1, :] - F.Fx[-2, :]) / g.dx

    dFydy[:, 1:-1] = (F.Fy[:, 2:] - F.Fy[:, :-2]) / (2 * g.dy)
    dFydy[:, 0] = (F.Fy[:, 1] - F.Fy[:, 0]) / g.dy
    dFydy[:, -1] = (F.Fy[:, -1] - F.Fy[:, -2]) / g.dy

    def dummy(x, y):
        return 0.0

    out = ScalarField(dummy, (g.xmin, g.xmax, g.ymin, g.ymax), g.resolution)
    out.values = dFxdx + dFydy
    out.grid = g
    return out


def curl(F: VectorField) -> ScalarField:
    g = F.grid

    dFydx = np.zeros_like(F.Fy)
    dFxdy = np.zeros_like(F.Fx)

    dFydx[1:-1, :] = (F.Fy[2:, :] - F.Fy[:-2, :]) / (2 * g.dx)
    dFydx[0, :] = (F.Fy[1, :] - F.Fy[0, :]) / g.dx
    dFydx[-1, :] = (F.Fy[-1, :] - F.Fy[-2, :]) / g.dx

    dFxdy[:, 1:-1] = (F.Fx[:, 2:] - F.Fx[:, :-2]) / (2 * g.dy)
    dFxdy[:, 0] = (F.Fx[:, 1] - F.Fx[:, 0]) / g.dy
    dFxdy[:, -1] = (F.Fx[:, -1] - F.Fx[:, -2]) / g.dy

    def dummy(x, y):
        return 0.0

    out = ScalarField(dummy, (g.xmin, g.xmax, g.ymin, g.ymax), g.resolution)
    out.values = dFydx - dFxdy
    out.grid = g
    return out
