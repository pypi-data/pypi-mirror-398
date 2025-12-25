import numpy as np
from numba import njit

_R_EQ_TO_GAL = np.array([
    [-0.0548755604, -0.8734370902, -0.4838350155],
    [ 0.4941094279, -0.4448296300,  0.7469822445],
    [-0.8676661490, -0.1980763734,  0.4559837762]
], dtype=np.float64)

_R_GAL_TO_EQ = _R_EQ_TO_GAL.T.copy()

# Proper motion conversion constant:
# v_tan[km/s] = 4.74047 * d[kpc] * mu[mas/yr]
_K_PM = 4.74047

# Unit conversion for your leapfrog:
# 1 km/s = 0.001022712165 kpc/Myr
KM_S_TO_KPC_MYR = 0.0010227121650537077
KPC_MYR_TO_KM_S = 1.0 / KM_S_TO_KPC_MYR


@njit(cache=True, fastmath=True)
def vHeqToGal(alpha, delta, dKpc, muAlphaStarMasYr, muDeltaMasYr, vrKms):
    """
    Equatorial observables -> heliocentric Galactic Cartesian velocity (km/s).
    """
    ca = np.cos(alpha)
    sa = np.sin(alpha)
    cd = np.cos(delta)
    sd = np.sin(delta)

    vAlpha = _K_PM * dKpc * muAlphaStarMasYr
    vDelta = _K_PM * dKpc * muDeltaMasYr

    vxEq = (vrKms * cd * ca) + (-vAlpha * sa) + (-vDelta * sd * ca)
    vyEq = (vrKms * cd * sa) + ( vAlpha * ca) + (-vDelta * sd * sa)
    vzEq = (vrKms * sd)      + ( vDelta * cd)

    vxGal = (_R_EQ_TO_GAL[0, 0] * vxEq +
             _R_EQ_TO_GAL[0, 1] * vyEq +
             _R_EQ_TO_GAL[0, 2] * vzEq)

    vyGal = (_R_EQ_TO_GAL[1, 0] * vxEq +
             _R_EQ_TO_GAL[1, 1] * vyEq +
             _R_EQ_TO_GAL[1, 2] * vzEq)

    vzGal = (_R_EQ_TO_GAL[2, 0] * vxEq +
             _R_EQ_TO_GAL[2, 1] * vyEq +
             _R_EQ_TO_GAL[2, 2] * vzEq)

    return vxGal, vyGal, vzGal


@njit(cache=True, fastmath=True)
def vGalToHeq(vxGal, vyGal, vzGal):
    """
    Galactic Cartesian velocity (km/s) -> Equatorial Cartesian velocity (km/s).
    Pure rotation.
    """
    vxEq = (_R_GAL_TO_EQ[0, 0] * vxGal +
            _R_GAL_TO_EQ[0, 1] * vyGal +
            _R_GAL_TO_EQ[0, 2] * vzGal)

    vyEq = (_R_GAL_TO_EQ[1, 0] * vxGal +
            _R_GAL_TO_EQ[1, 1] * vyGal +
            _R_GAL_TO_EQ[1, 2] * vzGal)

    vzEq = (_R_GAL_TO_EQ[2, 0] * vxGal +
            _R_GAL_TO_EQ[2, 1] * vyGal +
            _R_GAL_TO_EQ[2, 2] * vzGal)

    return vxEq, vyEq, vzEq


# -------------------------
# Leapfrog-friendly wrappers
# -------------------------

@njit(cache=True, fastmath=True)
def vHeqToGalKpcMyr(alpha, delta, dKpc, muAlphaStarMasYr, muDeltaMasYr, vrKms):
    """
    Same as vHeqToGal, but returns velocities in kpc/Myr for leapfrog.
    """
    vxKms, vyKms, vzKms = vHeqToGal(alpha, delta, dKpc, muAlphaStarMasYr, muDeltaMasYr, vrKms)
    return (vxKms * KM_S_TO_KPC_MYR,
            vyKms * KM_S_TO_KPC_MYR,
            vzKms * KM_S_TO_KPC_MYR)


@njit(cache=True, fastmath=True)
def vGalToHeqKpcMyr(vxKpcMyr, vyKpcMyr, vzKpcMyr):
    """
    Galactic Cartesian velocity (kpc/Myr) -> Equatorial Cartesian velocity (kpc/Myr).
    """
    vxKms = vxKpcMyr * KPC_MYR_TO_KM_S
    vyKms = vyKpcMyr * KPC_MYR_TO_KM_S
    vzKms = vzKpcMyr * KPC_MYR_TO_KM_S

    vxEqKms, vyEqKms, vzEqKms = vGalToHeq(vxKms, vyKms, vzKms)
    return (vxEqKms * KM_S_TO_KPC_MYR,
            vyEqKms * KM_S_TO_KPC_MYR,
            vzEqKms * KM_S_TO_KPC_MYR)
