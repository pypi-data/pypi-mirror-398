import numpy as np

class SpatialGrid:
    def __init__(self, bounds, resolution):
        self.xmin, self.xmax, self.ymin, self.ymax = bounds
        self.resolution = int(resolution)

        if self.resolution < 2:
            raise ValueError("Resolution must be >= 2")

        self.x = np.linspace(self.xmin, self.xmax, self.resolution)
        self.y = np.linspace(self.ymin, self.ymax, self.resolution)

        self.dx = self.x[1] - self.x[0]
        self.dy = self.y[1] - self.y[0]

        self.X, self.Y = np.meshgrid(self.x, self.y, indexing="ij")
