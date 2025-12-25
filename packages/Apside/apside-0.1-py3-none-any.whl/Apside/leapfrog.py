from decimal import Decimal, getcontext

# Package import (relative) – works when installed / imported as astrokit.leapfrog
from .acceleration import acceleration, r

getcontext().prec = 50


def halfVelocity(x, y, z, vx, vy, vz, dt):
    """
    Half-step velocity:
      v_{n+1/2} = v_n + 0.5 * dt * a(x_n)
    """
    x = Decimal(x);
    y = Decimal(y);
    z = Decimal(z)
    vx = Decimal(vx);
    vy = Decimal(vy);
    vz = Decimal(vz)
    dt = Decimal(dt)

    a = acceleration(x, y, z)

    vxHalf = vx + Decimal("0.5") * dt * a.x
    vyHalf = vy + Decimal("0.5") * dt * a.y
    vzHalf = vz + Decimal("0.5") * dt * a.z

    return r(vxHalf, vyHalf, vzHalf)


def nextPos(halfVel, x, y, z, dt):
    """
    Drift:
      x_{n+1} = x_n + dt * v_{n+1/2}
    """
    x = Decimal(x);
    y = Decimal(y);
    z = Decimal(z)
    dt = Decimal(dt)

    return r(
        x + dt * halfVel.x,
        y + dt * halfVel.y,
        z + dt * halfVel.z
    )


def nextVel(halfVel, xNew, yNew, zNew, dt):
    """
    Full-step velocity:
      v_{n+1} = v_{n+1/2} + 0.5 * dt * a(x_{n+1})
    """
    xNew = Decimal(xNew);
    yNew = Decimal(yNew);
    zNew = Decimal(zNew)
    dt = Decimal(dt)

    aNew = acceleration(xNew, yNew, zNew)

    return r(
        halfVel.x + Decimal("0.5") * dt * aNew.x,
        halfVel.y + Decimal("0.5") * dt * aNew.y,
        halfVel.z + Decimal("0.5") * dt * aNew.z
    )


def leapfrogStep(x, y, z, vx, vy, vz, dt):
    """
    Pure-functional step (more Pythonic than pass-by-ref):
    returns (x, y, z, vx, vy, vz) at next timestep.
    """
    # 1) Half-step velocity (leap)
    vHalf = halfVelocity(x, y, z, vx, vy, vz, dt)

    # 2) Full-step position (drift)
    xNew = nextPos(vHalf, x, y, z, dt)

    # 3) Full-step velocity (leap again)
    vNew = nextVel(vHalf, xNew.x, xNew.y, xNew.z, dt)

    # 4) Updated state
    return (xNew.x, xNew.y, xNew.z, vNew.x, vNew.y, vNew.z)
