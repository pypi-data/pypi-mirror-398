import matplotlib.pyplot as plt

def plot_scalar(field, levels=30, cmap="viridis"):
    """
    Contour plot of a ScalarField.
    """
    g = field.grid
    X, Y = g.X, g.Y

    plt.figure()
    cs = plt.contourf(X, Y, field.values, levels=levels, cmap=cmap)
    plt.colorbar(cs)
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("Scalar Field")
    plt.axis("equal")
    plt.tight_layout()
    plt.show()


def plot_vector(field, scale=None):
    """
    Quiver plot of a VectorField.
    """
    g = field.grid
    X, Y = g.X, g.Y

    plt.figure()
    plt.quiver(X, Y, field.Fx, field.Fy, scale=scale)
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("Vector Field")
    plt.axis("equal")
    plt.tight_layout()
    plt.show()

def plot_streamlines(lines, linewidth=1.0):
    """
    Plot streamlines returned by VectorField.streamlines().
    """
    plt.figure()
    for pts in lines:
        if len(pts) < 2:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        plt.plot(xs, ys, linewidth=linewidth)
    plt.axis("equal")
    plt.tight_layout()
    plt.show()

from vecfield import ScalarField
from vecfield.viz import plot_streamlines
import numpy as np

V = ScalarField(lambda x, y: x**2 + y**2, (-2,2,-2,2), resolution=80)
E = -V.grad()

seeds = E.seed_circle(radius=1.0, n=24)
lines = E.streamlines(seeds, step=0.05, n_steps=300)

#plot_streamlines(lines)


