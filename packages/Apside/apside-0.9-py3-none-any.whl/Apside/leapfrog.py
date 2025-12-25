from .acceleration import *


# Assuming the 'r' jitclass and 'acceleration' function are
# available in the same scope or imported from your JIT acceleration module.

@njit
def halfVelocity(x, y, z, vx, vy, vz, dt):
    """
    Half-step velocity: v_{n+1/2} = v_n + 0.5 * dt * a(x_n)
    """
    a = acceleration(x, y, z)

    vxHalf = vx + 0.5 * dt * a.x
    vyHalf = vy + 0.5 * dt * a.y
    vzHalf = vz + 0.5 * dt * a.z

    return r(vxHalf, vyHalf, vzHalf)


@njit
def nextPos(vHalf, x, y, z, dt):
    """
    Drift: x_{n+1} = x_n + dt * v_{n+1/2}
    """
    xNew = x + dt * vHalf.x
    yNew = y + dt * vHalf.y
    zNew = z + dt * vHalf.z

    return r(xNew, yNew, zNew)


@njit
def nextVel(vHalf, xNew, yNew, zNew, dt):
    """
    Full-step velocity: v_{n+1} = v_{n+1/2} + 0.5 * dt * a(x_{n+1})
    """
    aNew = acceleration(xNew, yNew, zNew)

    vxNew = vHalf.x + 0.5 * dt * aNew.x
    vyNew = vHalf.y + 0.5 * dt * aNew.y
    vzNew = vHalf.z + 0.5 * dt * aNew.z

    return r(vxNew, vyNew, vzNew)


@njit
def leapfrogStep(x, y, z, vx, vy, vz, dt):
    """
    Optimized pure-functional step.
    """
    # 1) Half-step velocity (Kick)
    vHalf = halfVelocity(x, y, z, vx, vy, vz, dt)

    # 2) Full-step position (Drift)
    posNew = nextPos(vHalf, x, y, z, dt)

    # 3) Full-step velocity (Kick)
    vNew = nextVel(vHalf, posNew.x, posNew.y, posNew.z, dt)

    # 4) Updated state
    return (posNew.x, posNew.y, posNew.z, vNew.x, vNew.y, vNew.z)