import numpy as np
from numba import njit

# Physical Constants
G = 4.3009e-6
EPS = 1e-8

# Velocity conversion (consistent with your earlier constant)
KM_S_TO_KPC_MYR = 0.0010227121650537077
KPC_MYR_TO_KM_S = 1.0 / KM_S_TO_KPC_MYR


@njit
def phiBulge(x, y, z):
    Mb = 8.9e9
    ab = 0.6

    r = np.sqrt(x * x + y * y + z * z)
    if r < EPS:
        r = EPS

    return -G * Mb / (r + ab)  # (km/s)^2


@njit
def phiDisk(x, y, z):
    Md = 6e10
    ad = 3.0
    bd = 0.28

    R2 = x * x + y * y
    B = np.sqrt(z * z + bd * bd)
    D = np.sqrt(R2 + (ad + B) * (ad + B))

    return -G * Md / D  # (km/s)^2


@njit
def phiHalo(x, y, z):
    Mh = 1.3e12
    rs = 19.6

    r = np.sqrt(x * x + y * y + z * z)
    if r < EPS:
        r = EPS

    return -G * Mh * np.log(1.0 + r / rs) / r  # (km/s)^2


@njit
def totalEnergy(x, y, z, vx, vy, vz):
    # vx,vy,vz are kpc/Myr in your integrator -> convert to km/s for energy consistency
    vxKms = vx * KPC_MYR_TO_KM_S
    vyKms = vy * KPC_MYR_TO_KM_S
    vzKms = vz * KPC_MYR_TO_KM_S

    v2 = vxKms * vxKms + vyKms * vyKms + vzKms * vzKms
    kinetic = 0.5 * v2  # (km/s)^2

    potential = phiBulge(x, y, z) + phiDisk(x, y, z) + phiHalo(x, y, z)  # (km/s)^2

    return kinetic + potential  # (km/s)^2
