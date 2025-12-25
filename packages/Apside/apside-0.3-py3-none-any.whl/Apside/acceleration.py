from decimal import Decimal, getcontext

# High precision for orbital dynamics
getcontext().prec = 50
EPS = Decimal("1e-8")


class r:
    __slots__ = ("x", "y", "z")

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other):
        return r(
            self.x + other.x,
            self.y + other.y,
            self.z + other.z
        )

    def __repr__(self):
        return f"r(x={self.x}, y={self.y}, z={self.z})"


def sqrt(d: Decimal) -> Decimal:
    return d.sqrt()


def ln(d: Decimal) -> Decimal:
    return d.ln()


def bulgeAccel(x, y, z):
    """
    ax = (-G Mb / (r + ab)^2) * (x / r)
    ay = (-G Mb / (r + ab)^2) * (y / r)
    az = (-G Mb / (r + ab)^2) * (z / r)
    """

    G = Decimal("4.3009e-6")
    Mb = Decimal("8.9e9")
    ab = Decimal("0.6")

    x = Decimal(x)
    y = Decimal(y)
    z = Decimal(z)

    rad = sqrt(x * x + y * y + z * z)
    if rad < EPS:
        rad = EPS

    h = (-G * Mb) / ((rad + ab) * (rad + ab) * rad)

    ax = h * x
    ay = h * y
    az = h * z

    return r(ax, ay, az)


def diskAccel(x, y, z):
    """
    Miyamoto–Nagai disk
    """

    ad = Decimal("3.0")
    bd = Decimal("0.28")
    G = Decimal("4.3009e-6")
    Md = Decimal("6e10")

    x = Decimal(x)
    y = Decimal(y)
    z = Decimal(z)

    R = sqrt(x * x + y * y)
    B = sqrt(z * z + bd * bd)
    D = sqrt(R * R + (ad + B) * (ad + B))

    centralPart = -(G * Md) / (D * D * D)

    ax = centralPart * x
    ay = centralPart * y
    az = centralPart * ((ad + B) * z / B)

    return r(ax, ay, az)


def haloAccel(x, y, z):
    """
    NFW halo (McMillan 2017)
    a = -G Mh / r^3 * [ ln(1 + r/rs) - r/(r + rs) ] * r_vec
    """

    G = Decimal("4.3009e-6")
    Mh = Decimal("1.3e12")
    rs = Decimal("19.6")

    x = Decimal(x)
    y = Decimal(y)
    z = Decimal(z)

    rad = sqrt(x * x + y * y + z * z)
    if rad < EPS:
        rad = EPS

    radCube = rad * rad * rad

    centralPart = (
                          (-G * Mh) / radCube
                  ) * (ln(Decimal(1) + rad / rs) - rad / (rad + rs))

    ax = centralPart * x
    ay = centralPart * y
    az = centralPart * z

    return r(ax, ay, az)


def acceleration(x, y, z):
    bulge = bulgeAccel(x, y, z)
    disk = diskAccel(x, y, z)
    halo = haloAccel(x, y, z)

    ax = bulge.x + disk.x + halo.x
    ay = bulge.y + disk.y + halo.y
    az = bulge.z + disk.z + halo.z

    return r(ax, ay, az)
