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


# Constants
EPS = 1e-8

# G in: kpc * (km/s)^2 / Msun
G = 4.3009e-6

# You integrate in: x[kpc], v[kpc/Myr], dt[Myr]
# So acceleration must be: kpc / Myr^2
# Your model naturally outputs: (km/s)^2 / kpc
# Convert by multiplying by (km/s -> kpc/Myr)^2
KM_S_TO_KPC_MYR = 0.0010227121650537077
ACC_SCALE = KM_S_TO_KPC_MYR * KM_S_TO_KPC_MYR


@njit
def bulgeAccel(x, y, z):
    Mb = 8.9e9
    ab = 0.6

    rad = np.sqrt(x * x + y * y + z * z)
    if rad < EPS:
        rad = EPS

    h = (-G * Mb) / ((rad + ab) * (rad + ab) * rad)  # (km/s)^2 / kpc^2
    return r(h * x, h * y, h * z)                     # (km/s)^2 / kpc


@njit
def diskAccel(x, y, z):
    ad = 3.0
    bd = 0.28
    Md = 6e10

    R = np.sqrt(x * x + y * y)
    B = np.sqrt(z * z + bd * bd)
    D = np.sqrt(R * R + (ad + B) * (ad + B))

    centralPart = -(G * Md) / (D * D * D)             # (km/s)^2 / kpc^3

    ax = centralPart * x                               # (km/s)^2 / kpc
    ay = centralPart * y
    az = centralPart * ((ad + B) * z / B)

    return r(ax, ay, az)


@njit
def haloAccel(x, y, z):
    Mh = 1.3e12
    rs = 19.6

    rad = np.sqrt(x * x + y * y + z * z)
    if rad < EPS:
        rad = EPS

    radCube = rad * rad * rad

    # NFW profile: result is (km/s)^2 / kpc
    centralPart = ((-G * Mh) / radCube) * (np.log(1.0 + rad / rs) - rad / (rad + rs))
    return r(centralPart * x, centralPart * y, centralPart * z)


@njit
def acceleration(x, y, z):
    bulge = bulgeAccel(x, y, z)
    disk = diskAccel(x, y, z)
    halo = haloAccel(x, y, z)

    ax = bulge.x + disk.x + halo.x   # (km/s)^2 / kpc
    ay = bulge.y + disk.y + halo.y
    az = bulge.z + disk.z + halo.z

    # Convert to kpc / Myr^2 for your leapfrog integrator
    ax *= ACC_SCALE
    ay *= ACC_SCALE
    az *= ACC_SCALE

    return r(ax, ay, az)
