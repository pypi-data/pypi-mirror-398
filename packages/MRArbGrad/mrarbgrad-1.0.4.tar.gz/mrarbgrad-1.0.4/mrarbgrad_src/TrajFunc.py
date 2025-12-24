from numpy import *
from numpy.typing import *

# Spiral
prange_Spiral = lambda kRhoPhi: [0e0, 0.5/kRhoPhi]

def Spiral(phi:float64, kRhoPhi:float64=0.5/(4*pi), phi0:float64=0e0):
    rho = kRhoPhi*phi
    return array([rho*cos(phi+phi0), rho*sin(phi+phi0), zeros_like(phi)])

# VDS
prange_VDS = lambda kRhoPhi0, kRhoPhi1: [0e0, (log(kRhoPhi1)-log(kRhoPhi0))/(2e0*(kRhoPhi1-kRhoPhi0))]

def VDS(phi:float64, kRhoPhi0:float64=0.5/(8*pi), kRhoPhi1:float64=0.5/(2*pi), phi0:float64=0e0):
    rho = kRhoPhi0*(exp(2e0*(kRhoPhi1-kRhoPhi0)*phi)-1e0)/(2e0*(kRhoPhi1-kRhoPhi0))
    return array([rho*cos(phi+phi0), rho*sin(phi+phi0), zeros_like(phi)])

# Rosette
prange_Rosette = [0e0, 1e0]

def Rosette(t:float64, om1:float64=5e0*pi, om2:float64=3e0*pi, phi0:float64=0e0):
    rho = 0.5*sin(om1*t)
    return array([rho*cos(om2*t+phi0), rho*sin(om2*t+phi0), zeros_like(t)])

# Yarnball
prange_Yarnball = lambda kRhoPhi: [0e0, 1e0/(sqrt(8e0)*kRhoPhi)]

def Yarnball(sqrtTht:float64, kRhoPhi:float64=0.5/(2e0*pi), tht0:float64=pi/3e0, phi0:float64=0e0):
    kPhiSqrtTht, kRhoSqrtTht = sqrt(2e0), sqrt(2e0)*kRhoPhi
    tht, rho, phi = sqrtTht**2e0*sign(sqrtTht), kRhoSqrtTht*sqrtTht, kPhiSqrtTht*sqrtTht
    return array([rho*sin(tht+tht0)*cos(phi+phi0), rho*sin(tht+tht0)*sin(phi+phi0), rho*cos(tht+tht0)])

# Cones
prange_Cones = lambda kRhoPhi: [0e0, 0.5/kRhoPhi]

def Cones(phi:float64, kRhoPhi:float64=0.5/(4*pi), tht0:float64=pi/3e0, phi0:float64=0e0):
    rho = kRhoPhi*phi
    return array([rho*sin(tht0)*cos(phi+phi0), rho*sin(tht0)*sin(phi+phi0), rho*cos(tht0)])