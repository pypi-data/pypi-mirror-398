from decimal import Decimal, getcontext

# Match precision used in acceleration
getcontext().prec = 50

EPS = Decimal("1e-8")


def sqrt(d: Decimal) -> Decimal:
    return d.sqrt()


def ln(d: Decimal) -> Decimal:
    return d.ln()


# Specific potential: bulge (Hernquist)
def phiBulge(x, y, z):
    G  = Decimal("4.3009e-6")  # kpc (km/s)^2 / Msun
    Mb = Decimal("8.9e9")      # Msun
    ab = Decimal("0.6")        # kpc

    x = Decimal(x)
    y = Decimal(y)
    z = Decimal(z)

    r = sqrt(x*x + y*y + z*z)

    return -G * Mb / (r + ab)


# Specific potential: disk (Miyamoto–Nagai)
def phiDisk(x, y, z):
    G  = Decimal("4.3009e-6")
    Md = Decimal("6e10")   # Msun
    ad = Decimal("3.0")    # kpc
    bd = Decimal("0.28")   # kpc

    x = Decimal(x)
    y = Decimal(y)
    z = Decimal(z)

    R = sqrt(x*x + y*y)
    B = sqrt(z*z + bd*bd)
    D = sqrt(R*R + (ad + B)*(ad + B))

    return -G * Md / D


# Specific potential: halo (NFW)
def phiHalo(x, y, z):
    G  = Decimal("4.3009e-6")
    Mh = Decimal("1.3e12")  # Msun (McMillan 2017)
    rs = Decimal("19.6")    # kpc

    x = Decimal(x)
    y = Decimal(y)
    z = Decimal(z)

    r = sqrt(x*x + y*y + z*z)
    if r < EPS:
        r = EPS

    return -G * Mh * ln(Decimal(1) + r/rs) / r


def totalEnergy(x, y, z, vx, vy, vz):
    x  = Decimal(x)
    y  = Decimal(y)
    z  = Decimal(z)
    vx = Decimal(vx)
    vy = Decimal(vy)
    vz = Decimal(vz)

    v2 = vx*vx + vy*vy + vz*vz
    kinetic = Decimal("0.5") * v2

    potential = (
        phiBulge(x, y, z)
        + phiDisk(x, y, z)
        + phiHalo(x, y, z)
    )

    return kinetic + potential  # (km/s)^2, specific energy
