import numpy as np
from numba import njit, float64
from numba.experimental import jitclass

# JIT-compiled class to replace your slots class
spec = [
    ('x', float64),
    ('y', float64),
    ('z', float64),
]


@jitclass(spec)
class r:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


# Constants in float64
EPS = 1e-8
G = 4.3009e-6


@njit
def bulgeAccel(x, y, z):
    Mb = 8.9e9
    ab = 0.6

    rad = np.sqrt(x ** 2 + y ** 2 + z ** 2)
    if rad < EPS:
        rad = EPS

    # Math simplified: (rad + ab)^2 * rad in denominator
    h = (-G * Mb) / ((rad + ab) ** 2 * rad)

    return r(h * x, h * y, h * z)


@njit
def diskAccel(x, y, z):
    ad = 3.0
    bd = 0.28
    Md = 6e10

    R = np.sqrt(x ** 2 + y ** 2)
    B = np.sqrt(z ** 2 + bd ** 2)
    # D = sqrt(R^2 + (ad + B)^2)
    D = np.sqrt(R ** 2 + (ad + B) ** 2)

    centralPart = -(G * Md) / (D ** 3)

    ax = centralPart * x
    ay = centralPart * y
    az = centralPart * ((ad + B) * z / B)

    return r(ax, ay, az)


@njit
def haloAccel(x, y, z):
    Mh = 1.3e12
    rs = 19.6

    rad = np.sqrt(x ** 2 + y ** 2 + z ** 2)
    if rad < EPS:
        rad = EPS

    radCube = rad ** 3

    # NFW Profile acceleration
    centralPart = ((-G * Mh) / radCube) * (np.log(1.0 + rad / rs) - rad / (rad + rs))

    return r(centralPart * x, centralPart * y, centralPart * z)


@njit
def acceleration(x, y, z):
    bulge = bulgeAccel(x, y, z)
    disk = diskAccel(x, y, z)
    halo = haloAccel(x, y, z)

    return r(
        bulge.x + disk.x + halo.x,
        bulge.y + disk.y + halo.y,
        bulge.z + disk.z + halo.z
    )