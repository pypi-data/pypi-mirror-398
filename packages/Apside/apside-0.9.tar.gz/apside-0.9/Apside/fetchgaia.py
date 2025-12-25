import numpy as np
from astroquery.gaia import Gaia

def getGaiaDr3InputsBySourceIdRequireRV(sourceId: int):
    """
    Fetch Gaia DR3 observables for one star.
    REQUIRE radial velocity; raise if missing.

    Returns values in the exact units expected by:
      backwardIntegrateSingleStar(...)
    """

    adql = f"""
    SELECT
        source_id,
        ra, dec,
        parallax, parallax_error,
        pmra, pmra_error,
        pmdec, pmdec_error,
        radial_velocity, radial_velocity_error
    FROM gaiadr3.gaia_source
    WHERE source_id = {int(sourceId)}
      AND radial_velocity IS NOT NULL
    """

    job = Gaia.launch_job_async(adql)
    tbl = job.get_results()

    if len(tbl) == 0:
        raise ValueError(
            f"Gaia DR3 source_id={sourceId} has no radial velocity; skipping."
        )

    row = tbl[0]

    # --- Astrometry ---
    raDeg = float(row["ra"])
    decDeg = float(row["dec"])
    parallaxMas = float(row["parallax"])

    if parallaxMas <= 0.0 or not np.isfinite(parallaxMas):
        raise ValueError(f"Invalid parallax for source_id={sourceId}")

    # Convert to integrator units
    alpha = np.deg2rad(raDeg)
    delta = np.deg2rad(decDeg)
    dKpc = 1.0 / parallaxMas

    # Gaia already provides mu_alpha_star
    muAlphaStarMasYr = float(row["pmra"])
    muDeltaMasYr = float(row["pmdec"])

    # --- Radial velocity (guaranteed present here) ---
    vrKms = float(row["radial_velocity"])

    # --- Uncertainties (for Monte Carlo) ---
    errors = {
        "parallaxMasErr": float(row["parallax_error"]),
        "muAlphaStarMasYrErr": float(row["pmra_error"]),
        "muDeltaMasYrErr": float(row["pmdec_error"]),
        "vrKmsErr": float(row["radial_velocity_error"]),
    }

    return alpha, delta, dKpc, muAlphaStarMasYr, muDeltaMasYr, vrKms, errors
