import numpy as np
import sys

def rf(x, y, z):
    # Constants
    ERRTOL = 0.0025
    THIRD = 1.0 / 3.0
    C1 = 1.0 / 24.0
    C2 = 0.1
    C3 = 3.0 / 44.0
    C4 = 1.0 / 14.0

    TINY = 5.0 * sys.float_info.min
    BIG = 0.2 * sys.float_info.max

    # Convert inputs to numpy arrays for vectorized operations
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    z = np.asarray(z, dtype=np.float64)

    # Validate the inputs
    if np.any(np.min([x, y, z], axis=0) < 0.0) or \
       np.any(np.min([x + y, x + z, y + z], axis=0) < TINY) or \
       np.any(np.max([x, y, z], axis=0) > BIG):
        raise ValueError("invalid arguments in rf")

    # Initial values
    xt = x
    yt = y
    zt = z

    while True:
        sqrtx = np.sqrt(xt)
        sqrty = np.sqrt(yt)
        sqrtz = np.sqrt(zt)
        
        alamb = sqrtx * (sqrty + sqrtz) + sqrty * sqrtz
        xt = 0.25 * (xt + alamb)
        yt = 0.25 * (yt + alamb)
        zt = 0.25 * (zt + alamb)
        ave = THIRD * (xt + yt + zt)
        delx = (ave - xt) / ave
        dely = (ave - yt) / ave
        delz = (ave - zt) / ave
        
        # Break condition for vectorized inputs
        if np.all(np.max([np.abs(delx), np.abs(dely), np.abs(delz)], axis=0) <= ERRTOL):
            break

    e2 = delx * dely - delz * delz
    e3 = delx * dely * delz
    return (1.0 + (C1 * e2 - C2 + C3 * e3) * e2 + C4 * e3) / np.sqrt(ave)
        

def rd(x, y, z):
    # Constants
    ERRTOL = 0.0015
    C1 = 3.0 / 14.0
    C2 = 1.0 / 6.0
    C3 = 9.0 / 22.0
    C4 = 3.0 / 26.0
    C5 = 0.25 * C3
    C6 = 1.5 * C4
    TINY = 2.0 * np.power(sys.float_info.max, -2.0 / 3.0)
    BIG = 0.1 * ERRTOL * np.power(sys.float_info.min, -2.0 / 3.0)
    # Check for invalid arguments
    if np.min([x, y]) < 0.0 or np.min([x + y, z]) < TINY or np.max([x, y, z]) > BIG:
        raise ValueError("invalid arguments in rd")

    # Initial values
    xt = x
    yt = y
    zt = z
    sum_ = 0.0
    fac = 1.0

    # Iterative process
    while True:
        sqrtx = np.sqrt(xt)
        sqrty = np.sqrt(yt)
        sqrtz = np.sqrt(zt)
        alamb = sqrtx * (sqrty + sqrtz) + sqrty * sqrtz
        sum_ += fac / (sqrtz * (zt + alamb))
        fac *= 0.25
        xt = 0.25 * (xt + alamb)
        yt = 0.25 * (yt + alamb)
        zt = 0.25 * (zt + alamb)
        ave = 0.2 * (xt + yt + 3.0 * zt)
        delx = (ave - xt) / ave
        dely = (ave - yt) / ave
        delz = (ave - zt) / ave
        if np.max([np.abs(delx), np.abs(dely), np.abs(delz)]) <= ERRTOL:
            break

    # Calculate elliptic integral
    ea = delx * dely
    eb = delz * delz
    ec = ea - eb
    ed = ea - 6.0 * eb
    ee = ed + 2 * ec

    return 3.0 * sum_ + fac * (1.0 + ed * (-C1 + C5 * ed - C6 * delz * ee) + delz * (C2 * ee + delz * (-C3 * ec + delz * C4 * ea))) / (ave * np.sqrt(ave))

def rc(x, y):
    # Carlson's symmetric elliptic integral RC
    ERRTOL = 0.0012
    THIRD = 1.0 / 3.0
    C1 = 0.3
    C2 = 1.0 / 7.0
    C3 = 0.375
    C4 = 9.0 / 22.0
    TINY = 5.0 * np.finfo(float).tiny
    BIG = 0.2 * np.finfo(float).max
    COMP1 = 2.236 / np.sqrt(TINY)
    COMP2 = (TINY * BIG)**2 / 25.0

    if np.any(x < 0.0) or np.any(y == 0.0) or \
       np.any((x + np.abs(y)) < TINY) or np.any((x + np.abs(y)) > BIG) or \
       np.any((y < -COMP1) & (x > 0.0) & (x < COMP2)):
        raise ValueError("Invalid arguments in rc")

    xt = np.where(y > 0.0, x, x - y)
    yt = np.where(y > 0.0, y, -y)
    w = np.where(y > 0.0, 1.0, np.sqrt(x) / np.sqrt(xt))

    while True:
        alamb = 2.0 * np.sqrt(xt) * np.sqrt(yt) + yt
        xt = 0.25 * (xt + alamb)
        yt = 0.25 * (yt + alamb)
        ave = THIRD * (xt + yt + yt)
        s = (yt - ave) / ave
        if np.all(np.abs(s) <= ERRTOL):
            break

    return w * (1.0 + s*s*(C1 + s*(C2 + s*(C3 + s*C4)))) / np.sqrt(ave)

def rj(x, y, z, p):
    # Constants
    ERRTOL = 0.0015
    C1 = 3.0 / 14.0
    C2 = 1.0 / 3.0
    C3 = 3.0 / 22.0
    C4 = 3.0 / 26.0
    C5 = 0.75 * C3
    C6 = 1.5 * C4
    C7 = 0.5 * C2
    C8 = C3 + C3
    TINY = np.power(5.0 * np.finfo(float).tiny, 1.0 / 3.0)
    BIG = 0.3 * np.power(0.2 * np.finfo(float).max, 1.0 / 3.0)

    # Convert inputs to numpy arrays for vectorized operations
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    z = np.asarray(z, dtype=np.float64)
    p = np.asarray(p, dtype=np.float64)

    # Check for invalid arguments
    if np.any(np.min([x, y, z], axis=0) < 0.0) or \
       np.any(np.min([x + y, x + z, y + z, np.abs(p)], axis=0) < TINY) or \
       np.any(np.max([x, y, z, np.abs(p)], axis=0) > BIG):
        raise ValueError("invalid arguments in rj")

    # Initial values
    sum_ = np.zeros_like(x)
    fac = 1.0

    if np.all(p > 0):
        xt = x
        yt = y
        zt = z
        pt = p
    else:
        xt = np.min([x, y, z], axis=0)
        zt = np.max([x, y, z], axis=0)
        yt = x + y + z - xt - zt
        a = 1.0 / (yt - p)
        b = a * (zt - yt) * (yt - xt)
        pt = yt + b
        rho = xt * zt / yt
        tau = p * pt / yt
        rcx = rc(rho, tau)

    while True:
        sqrtx = np.sqrt(xt)
        sqrty = np.sqrt(yt)
        sqrtz = np.sqrt(zt)
        alamb = sqrtx * (sqrty + sqrtz) + sqrty * sqrtz
        alpha = np.square(pt * (sqrtx + sqrty + sqrtz) + sqrtx * sqrty * sqrtz)
        beta = pt * np.square(pt + alamb)
        sum_ += fac * rc(alpha, beta)
        fac *= 0.25
        xt = 0.25 * (xt + alamb)
        yt = 0.25 * (yt + alamb)
        zt = 0.25 * (zt + alamb)
        pt = 0.25 * (pt + alamb)
        ave = 0.2 * (xt + yt + zt + pt + pt)
        delx = (ave - xt) / ave
        dely = (ave - yt) / ave
        delz = (ave - zt) / ave
        delp = (ave - pt) / ave
        if np.all(np.max([np.abs(delx), np.abs(dely), np.abs(delz), np.abs(delp)], axis=0) <= ERRTOL):
            break

    # Calculate elliptic integral
    ea = delx * (dely + delz) + dely * delz
    eb = delx * dely * delz
    ec = delp * delp
    ed = ea - 3.0 * ec
    ee = eb + 2.0 * delp * (ea - ec)

    ans = 3.0 * sum_ + fac * (1.0 + ed * (-C1 + C5 * ed - C6 * ee) + eb * (C7 + delp * (-C8 + delp * C4)) +
                              delp * ea * (C2 - delp * C3) - C2 * delp * ec) / (ave * np.sqrt(ave))

    if np.any(p <= 0):
        ans = a * (b * ans + 3.0 * (rcx - rf(xt, yt, zt)))
        
    return ans

#Complete integral of the first kind:
#\int_0^{\pi*0.5} d\theta (1 - k*k*sin(\theta))^{-0.5}
def ellipK(k2):
    if np.isscalar(k2):
        return rf(0, 1 - k2, 1)
    else:
        k2 = np.asarray(k2, dtype=np.float64)
        return rf(np.zeros(np.shape(k2)), 1 - k2, np.ones(np.shape(k2)))
        
def ellipE(k2):
    if np.isscalar(k2):
        return rf(0, 1 - k2, 1) - k2/3.0*rd(0, 1 - k2, 1)
    else:
        k2 = np.asarray(k2, dtype=np.float64)
        return rf(np.zeros(np.shape(k2)), 1 - k2, np.ones(np.shape(k2))) - k2/3.0*rd(np.zeros(np.shape(k2)), 1 - k2, np.ones(np.shape(k2)))

#Num. Recipes page 315
#def ellipPI(h2,k2):
#    if np.isscalar(k2):
#        return rf(0, 1 - k2, 1) - h2/3.0*rj(0, 1 - k2, 1, 1 + h2)
#    else:
#        k2 = np.asarray(k2, dtype=np.float64)
#        return rf(np.zeros(np.shape(k2)), 1 - k2, np.ones(np.shape(k2))) - h2/3.0*rj(np.zeros(np.shape(k2)), 1 - k2, np.ones(np.shape(k2)), 1 + h2)
#
#John Burkhard
def ellipPI(h2,k2):
    if np.isscalar(k2):
        return rf(0, 1 - k2, 1) + h2/3.0*rj(0, 1 - k2, 1, 1 - h2)
    else:
        k2 = np.asarray(k2, dtype=np.float64)
        return rf(np.zeros(np.shape(k2)), 1 - k2, np.ones(np.shape(k2))) + h2/3.0*rj(np.zeros(np.shape(k2)), 1 - k2, np.ones(np.shape(k2)), 1 - h2)


if __name__ == '__main__':
    
    import scipy.special as sp
    import matplotlib.pyplot as plt
    import os
    
    print(ellipK(0))
    print(ellipPI(0,0))
    print(np.pi/2)

    k = np.linspace(0.1, 0.99, 101)
    
    #test K(k)
#    plt.plot(k, sp.ellipk(k*k), '-b')
#    plt.plot(k , ellipK(k), '+r')

    #test E(k)
#    plt.plot(k, sp.ellipe(k*k), '-b')
#    plt.plot(k, ellipE(k), '+r')

    #test PI(k)
    # Create input arrays
    h = np.ones(np.shape(k)) * (-10)

#    # Write input to file
#    with open("PI_in.txt", "w") as f:
#        for hi, ki in zip(h, k*k):
#            f.write(f"{hi} {ki}\n")
#
#    # Run the C++ program
#    os.system("./PI")
#
#    # Read output from file
#    results = []
#    with open("PI_out.txt", "r") as f:
#        for line in f:
#            results.append(float(line.strip()))
#    plt.plot(k, np.array(results), '-b')
#
#
#    plt.plot(k, ellipPI(h,k), '+r')
#    plt.plot(k, np.array(results) /  ellipPI(h, k), '-k', lw=0.5)
#    plt.ylim(0,6)
#    plt.show()

