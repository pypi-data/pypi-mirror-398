import numpy as np
from numba import njit

from .coordinates import heqToGal
from .velocity import *
from .leapfrog import leapfrogStep  # wherever your leapfrogStep lives

# ---- Unit helpers (recommended) ----
# If you integrate with positions in kpc and time in Myr, you want velocities in kpc/Myr.
KM_S_TO_KPC_MYR = 0.0010227121650537077  # 1 km/s = 0.0010227 kpc/Myr

@njit(cache=True)
def addSolarMotion(vxGalHelKms, vyGalHelKms, vzGalHelKms,
                   uSunKms=11.1, vSunKms=12.24, wSunKms=7.25, vLsrKms=232.0):
    """
    Convert heliocentric Galactic velocity -> Galactocentric Galactic velocity by adding Sun's motion.

    Convention:
      +U toward Galactic Center
      +V in direction of rotation
      +W toward North Galactic Pole

    vSunTotal = (U, VLSR + Vpec, W)
    """
    vxGc = vxGalHelKms + uSunKms
    vyGc = vyGalHelKms + (vLsrKms + vSunKms)
    vzGc = vzGalHelKms + wSunKms
    return vxGc, vyGc, vzGc


@njit(cache=True)
def backwardIntegrateSingleStar(
    alpha, delta, dKpc,
    muAlphaStarMasYr, muDeltaMasYr, vrKms,
    dtMyr, tLookbackMyr,
    R0=8.2, z0=0.0208,
    useSolarMotion=True,
    uSunKms=11.1, vSunKms=12.24, wSunKms=7.25, vLsrKms=232.0,
    storeStride=1
):
    """
    Backward integrate ONE star from observables using your existing coordinate + velocity modules.

    Inputs
    ------
    alpha, delta : radians
    dKpc : kpc
    muAlphaStarMasYr : mas/yr (mu_alpha * cos(delta); Gaia pmra already is this)
    muDeltaMasYr : mas/yr
    vrKms : km/s (positive away from Sun)

    dtMyr : Myr (positive; this function will integrate with -dtMyr)
    tLookbackMyr : Myr (positive)

    Returns
    -------
    xs, ys, zs : kpc
    vxs, vys, vzs : kpc/Myr   (NOTE: converted from km/s)
    """

    if storeStride < 1:
        storeStride = 1

    # 1) Observables -> Galactocentric position (kpc)
    x0, y0, z0Out = heqToGal(alpha, delta, dKpc, R0, z0)

    # 2) Observables -> heliocentric Galactic velocity (km/s)
    vxHelGalKms, vyHelGalKms, vzHelGalKms = vHeqToGal(
        alpha, delta, dKpc, muAlphaStarMasYr, muDeltaMasYr, vrKms
    )

    # 3) (Recommended) convert heliocentric -> Galactocentric velocity by adding solar motion
    if useSolarMotion:
        vxGcKms, vyGcKms, vzGcKms = addSolarMotion(
            vxHelGalKms, vyHelGalKms, vzHelGalKms,
            uSunKms, vSunKms, wSunKms, vLsrKms
        )
    else:
        vxGcKms, vyGcKms, vzGcKms = vxHelGalKms, vyHelGalKms, vzHelGalKms

    # 4) Convert km/s -> kpc/Myr for consistency with (kpc, Myr) integration
    vx0 = vxGcKms * KM_S_TO_KPC_MYR
    vy0 = vyGcKms * KM_S_TO_KPC_MYR
    vz0 = vzGcKms * KM_S_TO_KPC_MYR

    # 5) Backward integrate with negative dt
    dt = -np.abs(dtMyr)
    nSteps = int(tLookbackMyr / np.abs(dtMyr)) + 1
    nStore = (nSteps - 1) // storeStride + 1

    xs = np.empty(nStore, dtype=np.float64)
    ys = np.empty(nStore, dtype=np.float64)
    zs = np.empty(nStore, dtype=np.float64)
    vxs = np.empty(nStore, dtype=np.float64)
    vys = np.empty(nStore, dtype=np.float64)
    vzs = np.empty(nStore, dtype=np.float64)

    x, y, z = x0, y0, z0Out
    vx, vy, vz = vx0, vy0, vz0

    xs[0], ys[0], zs[0] = x, y, z
    vxs[0], vys[0], vzs[0] = vx, vy, vz

    storeIdx = 1
    for i in range(1, nSteps):
        x, y, z, vx, vy, vz = leapfrogStep(x, y, z, vx, vy, vz, dt)

        if (i % storeStride) == 0:
            xs[storeIdx], ys[storeIdx], zs[storeIdx] = x, y, z
            vxs[storeIdx], vys[storeIdx], vzs[storeIdx] = vx, vy, vz
            storeIdx += 1

    return xs, ys, zs, vxs, vys, vzs
