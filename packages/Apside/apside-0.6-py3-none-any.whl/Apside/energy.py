import numpy as np
from numba import njit

# Physical Constants in float64
G = 4.3009e-6
EPS = 1e-8


@njit
def phiBulge(x, y, z):
    Mb = 8.9e9  # Msun
    ab = 0.6  # kpc

    r = np.sqrt(x * x + y * y + z * z)
    if r < EPS: r = EPS

    return -G * Mb / (r + ab)


@njit
def phiDisk(x, y, z):
    Md = 6e10  # Msun
    ad = 3.0  # kpc
    bd = 0.28  # kpc

    R2 = x * x + y * y
    B = np.sqrt(z * z + bd * bd)
    D = np.sqrt(R2 + (ad + B) ** 2)

    return -G * Md / D


@njit
def phiHalo(x, y, z):
    Mh = 1.3e12  # Msun
    rs = 19.6  # kpc

    r = np.sqrt(x * x + y * y + z * z)
    if r < EPS: r = EPS

    return -G * Mh * np.log(1.0 + r / rs) / r


@njit
def totalEnergy(x, y, z, vx, vy, vz):
    # Specific Kinetic Energy: 0.5 * v^2
    v2 = vx * vx + vy * vy + vz * vz
    kinetic = 0.5 * v2

    # Specific Potential Energy
    potential = (
            phiBulge(x, y, z) +
            phiDisk(x, y, z) +
            phiHalo(x, y, z)
    )

    return kinetic + potential  # units: (km/s)^2