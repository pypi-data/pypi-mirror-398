import mrarbgrad as mag
from numpy import *
from matplotlib.pyplot import *
from numpy.linalg import norm

gamma = 42.5756e6
fov = 0.256
nPix = 256
sLim = 50 * gamma * fov/nPix
gLim = 20e-3 * gamma * fov/nPix
dtGrad = 10e-6
dtADC = 2.5e-6
argCom = dict(dFov=fov, lNPix=nPix, dSLim=sLim, dGLim=gLim, dDt=dtGrad)

mag.setSolverMtg(0) # set solver, 0 for proposed method, 1 for baseline method, baseline method may be removed due to copyright reason
mag.setTrajRev(0) # reverse the trajectory
mag.setGoldAng(1) # enable golden-angle interleaving (only for 2D)
mag.setShuf(0) # enable TR-shuffling
mag.setMaxG0(0) # use maximum possible initial gradient amplitude
mag.setMaxG1(0) # use maximum possible final gradient amplitude
mag.setExGEnd(0) # restrict end-value of the graident exactly the same as requested (turn off only for benchmark purpose)
mag.setMagOv(8) # set oversampling ratio (default: 8, reduce only if hardware performance is too low to support real-time)
mag.setMagSFS(0) # disable DTFBS (experimental)
mag.setMagGradRep(1) # enable gradient reparameterization (experimental)
mag.setMagTrajRep(1) # enable trajectory reparameterization (experimental)
mag.setDbgPrint(1) # enable debug info (for benchmark purpose)

# calculate gradient
# lstArrK0, lstArrGrad = mag.getG_Spiral(bIs3D=0, **argCom); nAx = 2
# lstArrK0, lstArrGrad = mag.getG_VarDenSpiral(bIs3D=0, **argCom); nAx = 2
# lstArrK0, lstArrGrad = mag.getG_Rosette(bIs3D=0, **argCom); nAx = 2
# lstArrK0, lstArrGrad = mag.getG_Rosette_Trad(**argCom, dOm1=10*pi, dOm2=8*pi, dTmax=1, dTacq=2e-03); nAx = 2
# lstArrK0, lstArrGrad = mag.getG_Shell3d(**argCom); nAx = 3
lstArrK0, lstArrGrad = mag.getG_Yarnball(**argCom); nAx = 3
# lstArrK0, lstArrGrad = mag.getG_Seiffert(**argCom); nAx = 3
# lstArrK0, lstArrGrad = mag.getG_Cones(**argCom); nAx = 3

print("")
print(f"Intlea Num.: {len(lstArrGrad)}")
nRO_Max = amax([arrG.shape[0] for arrG in lstArrGrad])
print(f"Tacq: {nRO_Max*dtGrad*1e3:.3f} ms")
tTR = (nRO_Max*dtGrad + 2e-3)
print(f"TR: {tTR*1e3:.3f} ms")
tScan = tTR*len(lstArrGrad)
print(f"Tscan: {tScan:.3e} s")

# derive shape parameter
if nAx==2:
    lstArrK0 = [arrK0[:2] for arrK0 in lstArrK0]
    lstArrGrad = [arrG[:,:2] for arrG in lstArrGrad]
nRO, nAx = lstArrGrad[0].shape

# derive slewrate
lstArrSlew = [diff(arrG, axis=0)/dtGrad for arrG in lstArrGrad]
sMax = max(norm(concatenate(lstArrSlew)/gamma*nPix/fov, axis=-1))
gMax = max(norm(concatenate(lstArrGrad)/gamma*nPix/fov, axis=-1))

# derive trajectory
lstArrK = []
for arrK0, arrGrad in zip(lstArrK0, lstArrGrad):
    arrK, _ = mag.cvtGrad2Traj(arrGrad, dtGrad, dtADC)
    arrK += arrK0
    lstArrK.append(arrK)

iArrK = len(lstArrK)*2//3

# k-space and g-space
figure(figsize=(18,9), dpi=120)

subplot(221, projection="3d" if nAx==3 else None)
plot(*lstArrK[iArrK].T, ".-")
axis("equal")
grid("on")
title(f"kspace {1}/{len(lstArrGrad)}")

subplot(223, projection="3d" if nAx==3 else None)
plot(*lstArrGrad[iArrK].T, ".-")
axis("equal")
grid("on")
title("gspace")

# gradient and slewrate
subplot(222)
for iAx in range(nAx):
    plot(lstArrGrad[iArrK][:,iAx]/gamma*nPix/fov, ".-")
grid("on")
title(f"Gradient")

subplot(224)
plot(norm(lstArrSlew[iArrK],axis=-1)/gamma*nPix/fov, ".-", c="tab:blue")
ylim(sLim/gamma*nPix/fov*0.9, sLim/gamma*nPix/fov*1.1)
grid("on")

twinx()
plot(norm(lstArrGrad[iArrK],axis=-1)/gamma*nPix/fov*1e3, ".-", c="tab:orange")
ylim(gLim/gamma*nPix/fov*0.9*1e3, gLim/gamma*nPix/fov*1.1*1e3)
grid("on")
title(f"Grad & Slew amp., max grad:{gMax*1e3:.3f}, max slew:{sMax:.3f}")

subplots_adjust(0.05,0.1,0.95,0.9, 0.2, 0.2)

show()
