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
