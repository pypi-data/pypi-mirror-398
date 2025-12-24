from numpy import *
from matplotlib.pyplot import *
from numpy.typing import NDArray
from typing import Callable
import mrarbgrad.ext as ext

goldang = (3-sqrt(5))*pi

def calGrad4ExFunc\
(
    bIs3D: bool = False,
    dFov: float64 = 0.256,
    lNPix: int64 = 256,
    
    dSLim: float64 = 50 * 42.5756e6 * 0.256 / 256,
    dGLim: float64 = 50e-3 * 42.5756e6 * 0.256 / 256,
    dDt: float64 = 10e-6,
    
    getK: Callable|None = None,
    getDkDp: Callable|None = None,
    getD2kDp2: Callable|None = None,
    
    p0:float64 = 0e0, 
    p1:float64 = 1e0, 
) -> tuple[NDArray, NDArray]:
    '''
    :return: gradient waveform, corresponding parameter
    :rtype: tuple[NDArray, NDArray]
    '''
    return ext.calGrad4ExFunc\
    (
        int64(bIs3D),
        float64(dFov),
        int64(lNPix),
        
        float64(dSLim), 
        float64(dGLim), 
        float64(dDt), 
        
        getK,
        getDkDp,
        getD2kDp2,
        
        float64(p0),
        float64(p1), 
    )

def calGrad4ExSamp\
(
    bIs3D: bool = False,
    dFov: float64 = 0.256,
    lNPix: int64 = 256,
    
    dSLim: float64 = 50 * 42.5756e6 * 0.256 / 256,
    dGLim: float64 = 50e-3 * 42.5756e6 * 0.256 / 256,
    dDt: float64 = 10e-6,
    
    arrK: NDArray = np.empty((0,3)),
) -> tuple[NDArray, NDArray]:
    '''
    :return: gradient waveform, corresponding parameter
    :rtype: tuple[NDArray, NDArray]
    '''
    return ext.calGrad4ExSamp\
    (
        int64(bIs3D),
        float64(dFov),
        int64(lNPix),
        
        float64(dSLim), 
        float64(dGLim), 
        float64(dDt), 
        
        arrK
    )
    
def getG_Spiral\
(
    bIs3D: bool = False,
    dFov: float64 = 0.256,
    lNPix: int64 = 256,
    
    dSLim: float64 = 50 * 42.5756e6 * 0.256 / 256,
    dGLim: float64 = 50e-3 * 42.5756e6 * 0.256 / 256,
    dDt: float64 = 10e-6,
    
    dRhoPhi: float64 = 0.5 / (4 * pi)
) -> tuple[list[NDArray], list[NDArray]]:
    '''
    :return: list of trajectory start, list of gradient waveforms
    :rtype: tuple[list[NDArray], list[NDArray]]
    '''
    return ext.getG_Spiral\
    (
        int64(bIs3D),
        float64(dFov),
        int64(lNPix),
        
        float64(dSLim),
        float64(dGLim),
        float64(dDt),
        
        float64(dRhoPhi)
    )

def getG_VarDenSpiral\
(
    bIs3D: bool = False,
    dFov: float64 = 0.256,
    lNPix: int64 = 256,
    
    dSLim: float64 = 50 * 42.5756e6 * 0.256 / 256,
    dGLim: float64 = 50e-3 * 42.5756e6 * 0.256 / 256,
    dDt: float64 = 10e-6,
    
    dRhoPhi0: float64 = 0.5 / (8 * pi),
    dRhoPhi1: float64 = 0.5 / (2 * pi),
) -> tuple[list[NDArray], list[NDArray]]:
    '''
    :return: list of trajectory start, list of gradient waveforms
    :rtype: tuple[list[NDArray], list[NDArray]]
    '''
    return ext.getG_VarDenSpiral\
    (
        int64(bIs3D),
        float64(dFov),
        int64(lNPix),
        
        float64(dSLim),
        float64(dGLim),
        float64(dDt),
        
        float64(dRhoPhi0),
        float64(dRhoPhi1)
    )

def getG_Rosette\
(
    bIs3D: bool = False,
    dFov: float64 = 0.256,
    lNPix: int64 = 256,
    
    dSLim: float64 = 50 * 42.5756e6 * 0.256 / 256,
    dGLim: float64 = 50e-3 * 42.5756e6 * 0.256 / 256,
    dDt: float64 = 10e-6,
    
    dOm1: float64 = 5*pi, 
    dOm2: float64 = 3*pi, 
    dTmax: float64 = 1e0,
) -> tuple[list[NDArray], list[NDArray]]:
    '''
    :return: list of trajectory start, list of gradient waveforms
    :rtype: tuple[list[NDArray], list[NDArray]]
    '''
    return ext.getG_Rosette\
    (
        int64(bIs3D),
        float64(dFov),
        int64(lNPix),
        
        float64(dSLim),
        float64(dGLim),
        float64(dDt),
        
        float64(dOm1),
        float64(dOm2),
        float64(dTmax)
    )

def getG_Rosette_Trad\
(
    bIs3D: bool = False,
    dFov: float64 = 0.256,
    lNPix: int64 = 256,
    
    dSLim: float64 = 50 * 42.5756e6 * 0.256 / 256,
    dGLim: float64 = 50e-3 * 42.5756e6 * 0.256 / 256,
    dDt: float64 = 10e-6,
    
    dOm1: float64 = 5*pi, 
    dOm2: float64 = 3*pi, 
    dTmax: float64 = 1e0,
    dTacq: float64 = 2.523e-3,
) -> tuple[list[NDArray], list[NDArray]]:
    '''
    :return: list of trajectory start, list of gradient waveforms
    :rtype: tuple[list[NDArray], list[NDArray]]
    '''
    return ext.getG_Rosette_Trad\
    (
        int64(bIs3D),
        float64(dFov),
        int64(lNPix),
        
        float64(dSLim),
        float64(dGLim),
        float64(dDt),
        
        float64(dOm1),
        float64(dOm2),
        float64(dTmax),
        float64(dTacq)
    )

def getG_Shell3d\
(
    bIs3D: bool = False,
    dFov: float64 = 0.256,
    lNPix: int64 = 256,
    
    dSLim: float64 = 50 * 42.5756e6 * 0.256 / 256,
    dGLim: float64 = 50e-3 * 42.5756e6 * 0.256 / 256,
    dDt: float64 = 10e-6,
    
    dRhoTht: float64 = 0.5 / (2 * pi),
) -> tuple[list[NDArray], list[NDArray]]:
    '''
    :return: list of trajectory start, list of gradient waveforms
    :rtype: tuple[list[NDArray], list[NDArray]]
    '''
    return ext.getG_Shell3d\
    (
        int64(bIs3D),
        float64(dFov),
        int64(lNPix),
        
        float64(dSLim),
        float64(dGLim),
        float64(dDt),
        
        float64(dRhoTht),
    )

def getG_Yarnball\
(
    bIs3D: bool = False,
    dFov: float64 = 0.256,
    lNPix: int64 = 256,
    
    dSLim: float64 = 50 * 42.5756e6 * 0.256 / 256,
    dGLim: float64 = 50e-3 * 42.5756e6 * 0.256 / 256,
    dDt: float64 = 10e-6,
    
    dRhoPhi: float64 = 0.5 / (2 * pi),
) -> tuple[list[NDArray], list[NDArray]]:
    '''
    :return: list of trajectory start, list of gradient waveforms
    :rtype: tuple[list[NDArray], list[NDArray]]
    '''
    return ext.getG_Yarnball\
    (
        int64(bIs3D),
        float64(dFov),
        int64(lNPix),
        
        float64(dSLim),
        float64(dGLim),
        float64(dDt),
        
        float64(dRhoPhi),
    )

def getG_Seiffert\
(
    bIs3D: bool = False,
    dFov: float64 = 0.256,
    lNPix: int64 = 256,
    
    dSLim: float64 = 50 * 42.5756e6 * 0.256 / 256,
    dGLim: float64 = 50e-3 * 42.5756e6 * 0.256 / 256,
    dDt: float64 = 10e-6,
    
    dM: float64 = 0.07, 
    dUMax: float64 = 20.0, 
) -> tuple[list[NDArray], list[NDArray]]:
    '''
    :return: list of trajectory start, list of gradient waveforms
    :rtype: tuple[list[NDArray], list[NDArray]]
    '''
    return ext.getG_Seiffert\
    (
        int64(bIs3D),
        float64(dFov),
        int64(lNPix),
        
        float64(dSLim),
        float64(dGLim),
        float64(dDt),
        
        float64(dM),
        float64(dUMax),
    )

def getG_Cones\
(
    bIs3D: bool = False,
    dFov: float64 = 0.256,
    lNPix: int64 = 256,
    
    dSLim: float64 = 50 * 42.5756e6 * 0.256 / 256,
    dGLim: float64 = 50e-3 * 42.5756e6 * 0.256 / 256,
    dDt: float64 = 10e-6,
    
    dRhoPhi: float64 = 0.5 / (4 * pi),
) -> tuple[list[NDArray], list[NDArray]]:
    '''
    :return: list of trajectory start, list of gradient waveforms
    :rtype: tuple[list[NDArray], list[NDArray]]
    '''
    return ext.getG_Cones\
    (
        int64(bIs3D),
        float64(dFov),
        int64(lNPix),
        
        float64(dSLim),
        float64(dGLim),
        float64(dDt),
        
        float64(dRhoPhi),
    )

def setSolverMtg(x): ext.setSolverMtg(x)
def setTrajRev(x): ext.setTrajRev(x)
def setGoldAng(x): ext.setGoldAng(x)
def setShuf(x): ext.setShuf(x)
def setMaxG0(x): ext.setMaxG0(x)
def setMaxG1(x): ext.setMaxG1(x)
def setExGEnd(x): ext.setExGEnd(x)
def setMagOv(x): ext.setMagOv(x)
def setMagSFS(x): ext.setMagSFS(x)
def setMagGradRep(x): ext.setMagGradRep(x)
def setMagTrajRep(x): ext.setMagTrajRep(x)
def setDbgPrint(x): ext.setDbgPrint(x)
