import numpy as np
from numba import njit
from .coordinates import heqToGal
from .velocity import vHeqToGal
from .leapfrog import leapfrogStep

# 1 km/s = 0.001022712165 kpc/Myr
KM_S_TO_KPC_MYR = 0.0010227121650537077

@njit(cache=True)
def helioGalToGalactoGal(vxHelGalKms, vyHelGalKms, vzHelGalKms,
                         uSunKms, vSunKms, wSunKms, vLsrKms):
    """
    Convert heliocentric Galactic Cartesian velocity -> Galactocentric Cartesian velocity.

    Assumed axes (matches your heqToGal convention):
      +X: GC -> Sun
      +Y: direction of Galactic rotation
      +Z: North Galactic Pole

    Standard solar peculiar motion definition:
      +U toward GC  (i.e. -X)
      +V along rotation (+Y)
      +W toward NGP (+Z)

    Therefore Sun's Galactocentric velocity components are:
      vxSun = -U
      vySun = V_LSR + V
      vzSun = W
    """
    vxSun = -uSunKms
    vySun = vLsrKms + vSunKms
    vzSun = wSunKms

    return (vxHelGalKms + vxSun,
            vyHelGalKms + vySun,
            vzHelGalKms + vzSun)


@njit(cache=True)
def backwardIntegrateSingleStar(
    alpha, delta, dKpc,
    muAlphaStarMasYr, muDeltaMasYr, vrKms,
    dtMyr, tLookbackMyr,
    R0=8.2, zSunKpc=0.0208,
    useSolarMotion=True,
    uSunKms=11.1, vSunKms=12.24, wSunKms=7.25, vLsrKms=232.0,
    storeStride=1
):
    if storeStride < 1:
        storeStride = 1

    # Position: observables -> Galactocentric Cartesian (kpc)
    x0, y0, z0 = heqToGal(alpha, delta, dKpc, R0, zSunKpc)

    # Velocity: observables -> heliocentric Galactic Cartesian (km/s)
    vxHel, vyHel, vzHel = vHeqToGal(alpha, delta, dKpc,
                                   muAlphaStarMasYr, muDeltaMasYr, vrKms)

    # Optional: heliocentric -> Galactocentric by adding Sun motion
    if useSolarMotion:
        vxGc, vyGc, vzGc = helioGalToGalactoGal(vxHel, vyHel, vzHel,
                                                uSunKms, vSunKms, wSunKms, vLsrKms)
    else:
        vxGc, vyGc, vzGc = vxHel, vyHel, vzHel

    # Convert km/s -> kpc/Myr for leapfrog
    vx = vxGc * KM_S_TO_KPC_MYR
    vy = vyGc * KM_S_TO_KPC_MYR
    vz = vzGc * KM_S_TO_KPC_MYR

    # Backward integration: negative dt
    dt = -np.abs(dtMyr)
    nSteps = int(tLookbackMyr / np.abs(dtMyr)) + 1
    nStore = (nSteps - 1) // storeStride + 1

    xs = np.empty(nStore, dtype=np.float64)
    ys = np.empty(nStore, dtype=np.float64)
    zs = np.empty(nStore, dtype=np.float64)
    vxs = np.empty(nStore, dtype=np.float64)
    vys = np.empty(nStore, dtype=np.float64)
    vzs = np.empty(nStore, dtype=np.float64)

    xs[0], ys[0], zs[0] = x0, y0, z0
    vxs[0], vys[0], vzs[0] = vx, vy, vz

    x, y, z = x0, y0, z0
    storeIdx = 1

    for i in range(1, nSteps):
        x, y, z, vx, vy, vz = leapfrogStep(x, y, z, vx, vy, vz, dt)

        if (i % storeStride) == 0:
            xs[storeIdx], ys[storeIdx], zs[storeIdx] = x, y, z
            vxs[storeIdx], vys[storeIdx], vzs[storeIdx] = vx, vy, vz
            storeIdx += 1

    return xs, ys, zs, vxs, vys, vzs
