from numpy import *
from numpy.linalg import norm
from matplotlib.pyplot import *
import mrarbgrad as mag

gamma = 42.5756e6
fov = 0.256
nPix = 256
sLim = 100 * gamma * fov/nPix
gLim = 120e-3 * gamma * fov/nPix
dtGrad = 10e-6
dtADC = 2.5e-6

# Rosette
om1 = 5*pi
om2 = 3*pi
pLim = [0,1]
def TrajFunc(t):
    rho = 0.5*sin(om1*t)
    return array\
    ([
        rho*cos(om2*t),
        rho*sin(om2*t),
        zeros_like(t)
    ])

# sample
arrP = linspace(pLim[0], pLim[1], 1000)
arrK = TrajFunc(arrP).T
nAx = 2

# derive slew-rate constrained trajectory
for i in range(1):
    arrG, _ = mag.calGrad4ExSamp(False, fov, nPix, sLim, gLim, dtGrad, arrK)
nRO, _ = arrG.shape

arrS = diff(arrG, axis=0)/dtGrad
print(f"sMax: {max(norm(arrS,axis=-1))/(42.58e6)*(nPix/fov)}")

arrK, _ = mag.cvtGrad2Traj(arrG, dtGrad, dtADC, 0.5)
arrK += TrajFunc(pLim[0])
print(f"Err: {norm(arrK[-1,:]-TrajFunc(pLim[1])):.1e}")

# derive reference trajectory
arrP_Ref = linspace(pLim[0], pLim[1], int(1e4))
arrK_Ref = TrajFunc(arrP_Ref).T

# plot
figure(figsize=(20,10), dpi=120)

subplot(221, projection=None if nAx==2 else "3d")
if nAx==2: plot(arrK_Ref[:,0], arrK_Ref[:,1], "--", label="K_Ref")
if nAx==3: plot(arrK_Ref[:,0], arrK_Ref[:,1], arrK_Ref[:,2], "--", label="K_Ref")
if nAx==2: plot(arrK[:,0], arrK[:,1], ".-", label="K_Imp")
if nAx==3: plot(arrK[:,0], arrK[:,1], arrK[:,2], ".-", label="K_Imp")
xlim(-0.5,0.5)
ylim(-0.5,0.5)
axis("equal")
grid("on")
legend()
title("k-Space")

subplot(222)
for iAx in range(nAx):
    plot(arrG[:,iAx]/(42.58e6)*(nPix/fov), ".-")
grid("on")
title("Gradient")

subplot(223, projection=None if nAx==2 else "3d")
if nAx==2: plot(arrG[:,0], arrG[:,1], ".-")
if nAx==3: plot(arrG[:,0], arrG[:,1], arrG[:,2], ".-")
axis("equal")
grid("on")
title("g-Space")

subplot(224)
plot(norm(arrS,axis=-1)/(42.58e6)*(nPix/fov), ".-")
ylim(sLim/(42.58e6)*(nPix/fov)*0.9, sLim/(42.58e6)*(nPix/fov)*1.1)
grid("on")
title(f"Slewrate, max:{max(norm(arrS,axis=-1))/(42.58e6)*(nPix/fov):.3f}")

show()
