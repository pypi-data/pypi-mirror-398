import numpy as np
from numba import njit

# Matrices as global constants (Numba-friendly)
_R_EQ_TO_GAL = np.array([
    [-0.0548755604, -0.8734370902, -0.4838350155],
    [ 0.4941094279, -0.4448296300,  0.7469822445],
    [-0.8676661490, -0.1980763734,  0.4559837762]
], dtype=np.float64)

_R_GAL_TO_EQ = _R_EQ_TO_GAL.T.copy()
_K = 4.74047  # km/s per (kpc * mas/yr)

@njit(cache=True, fastmath=True)
def vHeqToGal(alpha, delta, d_kpc, mu_alpha_star, mu_delta, vr_kms):
    """
    Equatorial observables -> Heliocentric Galactic velocity (km/s).

    Inputs:
      alpha, delta: radians
      d_kpc: kpc
      mu_alpha_star: mas/yr  (this is mu_alpha * cos(delta), usually provided by catalogs)
      mu_delta: mas/yr
      vr_kms: km/s (positive away from Sun)

    Returns:
      vx_gal, vy_gal, vz_gal (km/s)
    """
    ca = np.cos(alpha)
    sa = np.sin(alpha)
    cd = np.cos(delta)
    sd = np.sin(delta)

    # Proper motion -> tangential speeds
    v_alpha = _K * d_kpc * mu_alpha_star
    v_delta = _K * d_kpc * mu_delta

    # Heliocentric equatorial Cartesian velocity (expanded)
    vx_eq = (vr_kms * cd * ca) + (-v_alpha * sa) + (-v_delta * sd * ca)
    vy_eq = (vr_kms * cd * sa) + ( v_alpha * ca) + (-v_delta * sd * sa)
    vz_eq = (vr_kms * sd)      + ( v_delta * cd)

    # Rotate eq -> gal (manual mat-vec; no allocations)
    vx_gal = (_R_EQ_TO_GAL[0, 0] * vx_eq +
              _R_EQ_TO_GAL[0, 1] * vy_eq +
              _R_EQ_TO_GAL[0, 2] * vz_eq)

    vy_gal = (_R_EQ_TO_GAL[1, 0] * vx_eq +
              _R_EQ_TO_GAL[1, 1] * vy_eq +
              _R_EQ_TO_GAL[1, 2] * vz_eq)

    vz_gal = (_R_EQ_TO_GAL[2, 0] * vx_eq +
              _R_EQ_TO_GAL[2, 1] * vy_eq +
              _R_EQ_TO_GAL[2, 2] * vz_eq)

    return vx_gal, vy_gal, vz_gal


@njit(cache=True, fastmath=True)
def vGalToHeq(vx_gal, vy_gal, vz_gal):
    """
    Heliocentric Galactic Cartesian velocity -> heliocentric Equatorial Cartesian velocity (km/s).
    Pure rotation (no solar-motion correction here).
    """
    # Rotate gal -> eq (manual; no allocations)
    vx_eq = (_R_GAL_TO_EQ[0, 0] * vx_gal +
             _R_GAL_TO_EQ[0, 1] * vy_gal +
             _R_GAL_TO_EQ[0, 2] * vz_gal)

    vy_eq = (_R_GAL_TO_EQ[1, 0] * vx_gal +
             _R_GAL_TO_EQ[1, 1] * vy_gal +
             _R_GAL_TO_EQ[1, 2] * vz_gal)

    vz_eq = (_R_GAL_TO_EQ[2, 0] * vx_gal +
             _R_GAL_TO_EQ[2, 1] * vy_gal +
             _R_GAL_TO_EQ[2, 2] * vz_gal)

    return vx_eq, vy_eq, vz_eq
