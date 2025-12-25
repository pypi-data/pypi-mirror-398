import numpy as np
from numba import njit

@njit
def heqToGal(alpha, delta, d, R0=8.2, z0=0.0208):
    """
    JIT-optimized conversion from heliocentric equatorial (RA, Dec, d)
    to Galactocentric Cartesian (X, Y, Z).
    """

    cosd = np.cos(delta)
    sind = np.sin(delta)
    cosa = np.cos(alpha)
    sina = np.sin(alpha)

    # Pre-calculating d * cosd to save two multiplications
    d_cosd = d * cosd

    X = (
        R0
        - 0.0548755604 * d_cosd * cosa
        - 0.8734370902 * d_cosd * sina
        - 0.4838350155 * d * sind
    )

    Y = (
        0.4941094279 * d_cosd * cosa
        - 0.4448296300 * d_cosd * sina
        + 0.7469822445 * d * sind
    )

    Z = (
        z0
        - 0.8676661490 * d_cosd * cosa
        - 0.1980763734 * d_cosd * sina
        + 0.4559837762 * d * sind
    )

    return X, Y, Z

@njit
def galToHeq(X, Y, Z, R0=8.2, z0=0.0208):
    """
    JIT-optimized conversion from Galactocentric Cartesian (X, Y, Z)
    back to Heliocentric equatorial Cartesian (x_eq, y_eq, z_eq).
    """

    # Undo translation (Shift from Galactic Center to Sun's position)
    xg = X - R0
    yg = Y
    zg = Z - z0

    # Apply the Transpose of the IAU J2000 rotation matrix.
    # Numba will optimize these multiplications into fused multiply-add (FMA) instructions.

    x_eq = (
            -0.0548755604 * xg
            + 0.4941094279 * yg
            - 0.8676661490 * zg
    )

    y_eq = (
            -0.8734370902 * xg
            - 0.4448296300 * yg
            - 0.1980763734 * zg
    )

    z_eq = (
            -0.4838350155 * xg
            + 0.7469822445 * yg
            + 0.4559837762 * zg
    )

    return x_eq, y_eq, z_eq

def cartToEq(x, y, z):
    """
    JIT-optimized conversion from heliocentric equatorial Cartesian (x, y, z)
    to spherical coordinates (RA, Dec, distance).

    Returns
    -------
    alpha : float (RA in radians)
    delta : float (Dec in radians)
    d     : float (Distance in kpc)
    """
    d2 = x * x + y * y + z * z
    d = np.sqrt(d2)

    # atan2 handles the quadrants for Right Ascension automatically
    alpha = np.atan2(y, x)

    # Check for division by zero if point is at origin
    if d > 1e-15:
        delta = np.asin(z / d)
    else:
        delta = 0.0

    return alpha, delta, d
