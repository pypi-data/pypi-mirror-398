#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <numpy/arrayobject.h>
#include <cstdio>
#include <ctime>
#include <algorithm>
#include "mag/GradGen.h"
#include "traj/TrajFunc.h"
#include "traj/MrTraj.h"
#include "traj/Spiral.h"
#include "traj/VarDenSpiral.h"
#include "traj/Rosette.h"
#include "traj/Shell3d.h"
#include "traj/Yarnball.h"
#include "traj/Seiffert.h"
#include "traj/Cones.h"
#include "utility/SplineIntp.h"

bool g_bTrajRev_Main (0);
bool g_bTrajGoldAng_Main (0);
bool g_bShuf_Main (0);
bool g_bMaxG0_Main (0);
bool g_bMaxG1_Main (0);

typedef std::vector<double> vd;
typedef std::vector<int64_t> vl;
typedef std::vector<v3> vv3;
typedef std::list<v3> lv3;
typedef std::list<double> ld;
typedef std::vector<vv3> vvv3;

PyObject* cvtVv3toNpa(vv3& vv3Src)
{
    int iD0 = vv3Src.size();
    // allocate numpy array
    PyObject* ppyoNpa;
    {
        npy_intp aDims[] = {iD0, 3};
        ppyoNpa = PyArray_ZEROS(2, aDims, NPY_FLOAT64, 0);
    }

    // fill the data in
    for (int64_t i = 0; i < (int)vv3Src.size(); ++i)
    {
        *(double*)PyArray_GETPTR2((PyArrayObject*)ppyoNpa, i, 0) = vv3Src[i].m_dX;
        *(double*)PyArray_GETPTR2((PyArrayObject*)ppyoNpa, i, 1) = vv3Src[i].m_dY;
        *(double*)PyArray_GETPTR2((PyArrayObject*)ppyoNpa, i, 2) = vv3Src[i].m_dZ;
    }

    return ppyoNpa;
}

PyObject* cvtVdtoNpa(const std::vector<double>& vdSrc)
{
    int iD0 = vdSrc.size();

    // allocate numpy array
    PyObject* ppyoNpa;
    {
        npy_intp aDims[] = {iD0};
        ppyoNpa = PyArray_ZEROS(1, aDims, NPY_FLOAT64, 0);
    }

    // fill the data in
    for (int64_t i = 0; i < (int)vdSrc.size(); ++i)
    {
        *(double*)PyArray_GETPTR1((PyArrayObject*)ppyoNpa, i) = vdSrc[i];
    }

    return ppyoNpa;
}

PyObject* cvtVvv3toList(vvv3& vvv3Src)
{
    PyObject* ppyoList = PyList_New(0);
    for (int64_t i = 0; i < (int)vvv3Src.size(); ++i)
    {
        PyObject* ppyoArr = cvtVv3toNpa(vvv3Src[i]);
        PyList_Append(ppyoList, ppyoArr);
        Py_DECREF(ppyoArr);
    }
    return ppyoList;
}

PyObject* cvtV3toNpa(v3& v3Src)
{
    // allocate numpy array
    PyObject* ppyoNpa;
    {
        npy_intp aDims[] = {3};
        ppyoNpa = PyArray_ZEROS(1, aDims, NPY_FLOAT64, 0);
    }

    // fill the data in
    *(double*)PyArray_GETPTR1((PyArrayObject*)ppyoNpa, 0) = v3Src.m_dX;
    *(double*)PyArray_GETPTR1((PyArrayObject*)ppyoNpa, 1) = v3Src.m_dY;
    *(double*)PyArray_GETPTR1((PyArrayObject*)ppyoNpa, 2) = v3Src.m_dZ;

    return ppyoNpa;
}

PyObject* cvtVv3toList(vv3& vv3Src)
{
    PyObject* ppyoList = PyList_New(0);
    for (int64_t i = 0; i < (int)vv3Src.size(); ++i)
    {
        PyObject* ppyoArr = cvtV3toNpa(vv3Src[i]);
        PyList_Append(ppyoList, ppyoArr);
        Py_DECREF(ppyoArr);
    }
    return ppyoList;
}

bool cvtNpa2Vv3(PyObject* ppyoNpa, vv3* pvv3Out)
{
    PyArrayObject* ppyaoNpa = (PyArrayObject*)PyArray_FROM_OTF(ppyoNpa, NPY_FLOAT64, NPY_ARRAY_C_CONTIGUOUS);
    int64_t lN = PyArray_DIM(ppyaoNpa, 0);
    pvv3Out->resize(lN);

    for (int64_t i = 0; i < lN; ++i)
    {
        double* pdThis = (double*)PyArray_GETPTR2(ppyaoNpa, i, 0);
        pvv3Out->at(i).m_dX = pdThis[0];
        pvv3Out->at(i).m_dY = pdThis[1];
        pvv3Out->at(i).m_dZ = pdThis[2];
    }

    Py_DECREF(ppyaoNpa); // what if decref another?
    return true;
}

bool cvtNpa2Vd(PyObject* ppyoNpa, vd* pvdOut)
{
    int64_t lN = PyArray_DIM((PyArrayObject*)ppyoNpa, 0);
    pvdOut->resize(lN);

    for (int64_t i = 0; i < lN; ++i)
    {
        pvdOut->at(i) = *(double*)PyArray_GETPTR1((PyArrayObject*)ppyoNpa, i);
    }
    return true;
}

bool inline checkNarg(int64_t lNarg, int64_t lNargExp)
{
    if (lNarg != lNargExp)
    {
        printf("wrong num. of arg, narg=%ld, %ld expected\n", lNarg, lNargExp);
        abort();
        return false;
    }
    return true;
}

bool getGeoGradPara(PyObject* const* args, MrTraj::GeoPara* psGeoPara, MrTraj::GradPara* psGradPara)
{
    *psGeoPara = 
    {
        (bool)PyLong_AsLong(args[0]),
        (double)PyFloat_AsDouble(args[1]),
        (int64_t)PyLong_AsLong(args[2])
    };

    *psGradPara = 
    {
        (double)PyFloat_AsDouble(args[3]),
        (double)PyFloat_AsDouble(args[4]),
        (double)PyFloat_AsDouble(args[5]),
        g_bMaxG0_Main,
        g_bMaxG1_Main
    };

    return true;
}

class ExFunc: public TrajFunc
{
public:
    ExFunc
    (
        PyObject* ppyoGetK,
        PyObject* ppyoGetDkDp,
        PyObject* ppyoGetD2kDp2,
        double dP0, double dP1
    )
    {
        m_ppyoGetK = ppyoGetK;
        m_ppyoGetDkDp = ppyoGetDkDp;
        m_ppyoGetD2kDp2 = ppyoGetD2kDp2;
        m_dP0 = dP0;
        m_dP1 = dP1;
    }
    
    bool getK(v3* pv3K, double dP) const
    {
        PyObject* ppyoP = PyFloat_FromDouble(dP);
        PyObject* ppyoV3 = PyObject_CallOneArg(m_ppyoGetK, ppyoP);
        Py_DECREF(ppyoP);
        PyObject* _ppyoV3 = ppyoV3;
        ppyoV3 = PyArray_FROM_OTF(ppyoV3, NPY_FLOAT64, NPY_ARRAY_CARRAY);
        Py_DECREF(_ppyoV3);
        if (PyArray_SIZE((PyArrayObject*)ppyoV3) != 3)
        {
            PyErr_SetString(PyExc_RuntimeError, "the return value of getK / getDkDp / getD2kDp2 must be size-3.\n");
            PyErr_PrintEx(-1);
            std::abort();
            return false;
        }

        pv3K->m_dX = *(double*)PyArray_GETPTR1((PyArrayObject*)ppyoV3, 0);
        pv3K->m_dY = *(double*)PyArray_GETPTR1((PyArrayObject*)ppyoV3, 1);
        pv3K->m_dZ = *(double*)PyArray_GETPTR1((PyArrayObject*)ppyoV3, 2);

        return true;
    }

    bool getDkDp(v3* pv3K, double dP) const
    {
        if (m_ppyoGetDkDp == Py_None)
        {
            return TrajFunc::getDkDp(pv3K, dP);
        }

        PyObject* ppyoP = PyFloat_FromDouble(dP);
        PyObject* ppyoV3 = PyObject_CallOneArg(m_ppyoGetDkDp, ppyoP);
        Py_DECREF(ppyoP);
        PyObject* _ppyoV3 = ppyoV3;
        ppyoV3 = PyArray_FROM_OTF(ppyoV3, NPY_FLOAT64, NPY_ARRAY_CARRAY);
        Py_DECREF(_ppyoV3);
        if (PyArray_SIZE((PyArrayObject*)ppyoV3) != 3)
        {
            PyErr_SetString(PyExc_RuntimeError, "the return value of getK / getDkDp / getD2kDp2 must be size-3.\n");
            PyErr_PrintEx(-1);
            std::abort();
            return false;
        }

        pv3K->m_dX = *(double*)PyArray_GETPTR1((PyArrayObject*)ppyoV3, 0);
        pv3K->m_dY = *(double*)PyArray_GETPTR1((PyArrayObject*)ppyoV3, 1);
        pv3K->m_dZ = *(double*)PyArray_GETPTR1((PyArrayObject*)ppyoV3, 2);

        return true;
    }

    bool getD2kDp2(v3* pv3K, double dP) const
    {
        if (m_ppyoGetD2kDp2 == Py_None)
        {
            return TrajFunc::getD2kDp2(pv3K, dP);
        }
        
        PyObject* ppyoP = PyFloat_FromDouble(dP);
        PyObject* ppyoV3 = PyObject_CallOneArg(m_ppyoGetD2kDp2, ppyoP);
        Py_DECREF(ppyoP);
        PyObject* _ppyoV3 = ppyoV3;
        ppyoV3 = PyArray_FROM_OTF(ppyoV3, NPY_FLOAT64, NPY_ARRAY_CARRAY);
        Py_DECREF(_ppyoV3);
        if (PyArray_SIZE((PyArrayObject*)ppyoV3) != 3)
        {
            PyErr_SetString(PyExc_RuntimeError, "the return value of getK / getDkDp / getD2kDp2 must be size-3.\n");
            PyErr_PrintEx(-1);
            std::abort();
            return false;
        }

        pv3K->m_dX = *(double*)PyArray_GETPTR1((PyArrayObject*)ppyoV3, 0);
        pv3K->m_dY = *(double*)PyArray_GETPTR1((PyArrayObject*)ppyoV3, 1);
        pv3K->m_dZ = *(double*)PyArray_GETPTR1((PyArrayObject*)ppyoV3, 2);

        return true;
    }
protected:
    PyObject* m_ppyoGetK;
    PyObject* m_ppyoGetDkDp;
    PyObject* m_ppyoGetD2kDp2;
};

class ExTraj: public MrTraj
{
public:
    ExTraj(const GeoPara& sGeoPara, const GradPara& sGradPara, PyObject* ppyoGetK, PyObject* ppyoGetDkDp, PyObject* ppyoGetD2kDp2, double dP0, double dP1):
        ptfTrajFunc(NULL)
    {
        m_sGeoPara = sGeoPara;
        m_sGradPara = sGradPara;
        m_lNAcq = 1;
        
        ptfTrajFunc = new ExFunc
        (
            ppyoGetK,
            ppyoGetDkDp,
            ppyoGetD2kDp2,
            dP0,
            dP1
        );

        TIC;
        calGRO(&m_lv3Grad, &m_ldP, *ptfTrajFunc, m_sGradPara, 8);
        TOC;
    }

    ExTraj(const GeoPara& sGeoPara, const GradPara& sGradPara, const vv3& vv3K):
        ptfTrajFunc(NULL)
    {
        m_sGeoPara = sGeoPara;
        m_sGradPara = sGradPara;
        m_lNAcq = 1;

        TIC;
        calGRO(&m_lv3Grad, &m_ldP, vv3K, m_sGradPara, 8);
        TOC;
    }

    ~ExTraj()
    {
        if (ptfTrajFunc)
        {
            delete ptfTrajFunc;
            ptfTrajFunc = NULL;
        }
    }

    bool getM0PE(v3* pv3M0PE, int64_t lIAcq) const
    {
        bool bRet = true;
        bRet &= ptfTrajFunc->getK0(pv3M0PE);
        return bRet;
    }

    bool getGRO(lv3* plv3GRO, int64_t lIAcq) const
    {
        bool bRet = true;
        *plv3GRO = m_lv3Grad;
        return bRet;
    }

    bool getPRO(ld* ldP, int64_t lIAcq) const // get parameter sequence of GRO
    {
        bool bRet = true;
        *ldP = m_ldP;
        return bRet;
    }

    int64_t getNWait(int64_t lIAcq) const
    {
        return 0;
    }

    int64_t getNSamp(int64_t lIAcq) const
    {
        return m_lv3Grad.size();
    }

private:
    TrajFunc* ptfTrajFunc;
    lv3 m_lv3Grad;
    ld m_ldP;
};

PyObject* calGrad4ExFunc(PyObject* self, PyObject* const* args, Py_ssize_t narg)
{
    checkNarg(narg, 11);

    MrTraj::GeoPara sGeoPara;
    MrTraj::GradPara sGradPara;
    getGeoGradPara(args, &sGeoPara, &sGradPara);

    double dP0 = (double)PyFloat_AsDouble(args[9]);
    double dP1 = (double)PyFloat_AsDouble(args[10]);

    ExTraj traj
    (
        sGeoPara, sGradPara,
        args[6], args[7], args[8], 
        dP0, dP1
    );

    lv3 lv3G;
    traj.getGRO(&lv3G, 0);
    ld ldP;
    traj.getPRO(&ldP, 0);

    vv3 vv3G(lv3G.begin(), lv3G.end());
    vd vdP(ldP.begin(), ldP.end());
    return Py_BuildValue("OO", cvtVv3toNpa(vv3G), cvtVdtoNpa(vdP));
}

PyObject* calGrad4ExSamp(PyObject* self, PyObject* const* args, Py_ssize_t narg)
{
    checkNarg(narg, 7);

    MrTraj::GeoPara sGeoPara;
    MrTraj::GradPara sGradPara;
    getGeoGradPara(args, &sGeoPara, &sGradPara);

    vv3 vv3K; cvtNpa2Vv3(args[6], &vv3K);

    ExTraj traj
    (
        sGeoPara, sGradPara,
        vv3K
    );
    
    lv3 lv3G;
    traj.getGRO(&lv3G, 0);
    ld ldP;
    traj.getPRO(&ldP, 0);

    vv3 vv3G(lv3G.begin(), lv3G.end());
    vd vdP(ldP.begin(), ldP.end());
    return Py_BuildValue("OO", cvtVv3toNpa(vv3G), cvtVdtoNpa(vdP));
}

bool getG(MrTraj* pmt, vv3* pvv3M0PE, vvv3* pvvv3GRO, bool bShuf)
{
    bool bRet = true;
    int64_t lNAcq = pmt->getNAcq();
    double dDt = pmt->getGradPara().dDt;
    pvv3M0PE->resize(lNAcq);
    pvvv3GRO->resize(lNAcq);

    bShuf &= g_bShuf_Main;
	vl vlShufIdx; MrTraj::genRandIdx(&vlShufIdx, lNAcq);
    for (int64_t i = 0; i < lNAcq; ++i)
    {
        int64_t _i = bShuf?vlShufIdx[i]:i;
        
        // get M0PE and GRO
        v3 v3M0PE; bRet &= pmt->getM0PE(&v3M0PE, _i);
        lv3 lv3GRO; bRet &= pmt->getGRO(&lv3GRO, _i);
        int64_t lNWait = pmt->getNWait(_i);
        int64_t lNSamp = pmt->getNSamp(_i);

        // crop gradient as requested
        lv3::iterator ilv3GRO = lv3GRO.begin();
        for (int64_t j = 0; j < lNWait; ++j)
        {
            v3M0PE += (*ilv3GRO + *std::next(ilv3GRO))*dDt/2e0;
            ilv3GRO = lv3GRO.erase(ilv3GRO);
        }
        {
            int64_t n = lv3GRO.size()-lNSamp;
            while (n--) lv3GRO.pop_back();
        }

        // reverse gradient if needed
        if (g_bTrajRev_Main) bRet &= GradGen::revGrad(&v3M0PE, &lv3GRO, v3M0PE, lv3GRO, dDt);

        pvv3M0PE->at(i) = v3M0PE;
        pvvv3GRO->at(i) = vv3(lv3GRO.begin(), lv3GRO.end());
    }
    return bRet;
}

PyObject* getG_Spiral(PyObject* self, PyObject* const* args, Py_ssize_t narg)
{
    checkNarg(narg, 7);

    MrTraj::GeoPara sGeoPara;
    MrTraj::GradPara sGradPara;
    getGeoGradPara(args, &sGeoPara, &sGradPara);

    double dRhoPhi = (double)PyFloat_AsDouble(args[6]);
    Spiral traj(sGeoPara, sGradPara, dRhoPhi);
    if (g_bTrajGoldAng_Main) traj.setRotAngInc(traj.getNRot());

    vv3 vv3K0;
    vvv3 vvv3Grad;
    getG(&traj, &vv3K0, &vvv3Grad, !g_bTrajGoldAng_Main);

    return Py_BuildValue("OO", cvtVv3toList(vv3K0), cvtVvv3toList(vvv3Grad));
}

PyObject* getG_VarDenSpiral(PyObject* self, PyObject* const* args, Py_ssize_t narg)
{
    checkNarg(narg, 8);

    MrTraj::GeoPara sGeoPara;
    MrTraj::GradPara sGradPara;
    getGeoGradPara(args, &sGeoPara, &sGradPara);

    double dRhoPhi0 = (double)PyFloat_AsDouble(args[6]);
    double dRhoPhi1 = (double)PyFloat_AsDouble(args[7]);
    VarDenSpiral traj(sGeoPara, sGradPara, dRhoPhi0, dRhoPhi1);
    if (g_bTrajGoldAng_Main) traj.setRotAngInc(traj.getNRot());

    vv3 vv3K0;
    vvv3 vvv3Grad;
    getG(&traj, &vv3K0, &vvv3Grad, !g_bTrajGoldAng_Main);

    return Py_BuildValue("OO", cvtVv3toList(vv3K0), cvtVvv3toList(vvv3Grad));
}

PyObject* getG_Rosette(PyObject* self, PyObject* const* args, Py_ssize_t narg)
{
    checkNarg(narg, 9);

    MrTraj::GeoPara sGeoPara;
    MrTraj::GradPara sGradPara;
    getGeoGradPara(args, &sGeoPara, &sGradPara);

    double dOm1 = (double)PyFloat_AsDouble(args[6]);
    double dOm2 = (double)PyFloat_AsDouble(args[7]);
    double dTmax = (double)PyFloat_AsDouble(args[8]);

    Rosette traj(sGeoPara, sGradPara, dOm1, dOm2, dTmax);
    // printf("Rosette DTE: %e s\n", traj.getAvrDTE());
    if (g_bTrajGoldAng_Main) traj.setRotAngInc(traj.getNRot());

    vv3 vv3K0;
    vvv3 vvv3Grad;
    getG(&traj, &vv3K0, &vvv3Grad, !g_bTrajGoldAng_Main);

    return Py_BuildValue("OO", cvtVv3toList(vv3K0), cvtVvv3toList(vvv3Grad));
}

PyObject* getG_Rosette_Trad(PyObject* self, PyObject* const* args, Py_ssize_t narg)
{
    checkNarg(narg, 10);

    MrTraj::GeoPara sGeoPara;
    MrTraj::GradPara sGradPara;
    getGeoGradPara(args, &sGeoPara, &sGradPara);

    double dOm1 = (double)PyFloat_AsDouble(args[6]);
    double dOm2 = (double)PyFloat_AsDouble(args[7]);
    double dTmax = (double)PyFloat_AsDouble(args[8]);
    double dDTE = (double)PyFloat_AsDouble(args[9]);

    Rosette_Trad traj(sGeoPara, sGradPara, dOm1, dOm2, dTmax, dDTE);
    if (g_bTrajGoldAng_Main) traj.setRotAngInc(traj.getNRot());

    vv3 vv3K0;
    vvv3 vvv3Grad;
    getG(&traj, &vv3K0, &vvv3Grad, !g_bTrajGoldAng_Main);

    return Py_BuildValue("OO", cvtVv3toList(vv3K0), cvtVvv3toList(vvv3Grad));
}

PyObject* getG_Shell3d(PyObject* self, PyObject* const* args, Py_ssize_t narg)
{
    checkNarg(narg, 7);

    MrTraj::GeoPara sGeoPara;
    MrTraj::GradPara sGradPara;
    getGeoGradPara(args, &sGeoPara, &sGradPara);

    double dRhoTht = (double)PyFloat_AsDouble(args[6]);
    Shell3d traj(sGeoPara, sGradPara, dRhoTht);

    vv3 vv3K0;
    vvv3 vvv3Grad;
    getG(&traj, &vv3K0, &vvv3Grad, true);

    return Py_BuildValue("OO", cvtVv3toList(vv3K0), cvtVvv3toList(vvv3Grad));
}

PyObject* getG_Yarnball(PyObject* self, PyObject* const* args, Py_ssize_t narg)
{
    checkNarg(narg, 7);

    MrTraj::GeoPara sGeoPara;
    MrTraj::GradPara sGradPara;
    getGeoGradPara(args, &sGeoPara, &sGradPara);

    double dRhoPhi = (double)PyFloat_AsDouble(args[6]);
    Yarnball traj(sGeoPara, sGradPara, dRhoPhi);

    vv3 vv3K0;
    vvv3 vvv3Grad;
    getG(&traj, &vv3K0, &vvv3Grad, true);

    return Py_BuildValue("OO", cvtVv3toList(vv3K0), cvtVvv3toList(vvv3Grad));
}

PyObject* getG_Seiffert(PyObject* self, PyObject* const* args, Py_ssize_t narg)
{
    checkNarg(narg, 8);

    MrTraj::GeoPara sGeoPara;
    MrTraj::GradPara sGradPara;
    getGeoGradPara(args, &sGeoPara, &sGradPara);

    double dM = (double)PyFloat_AsDouble(args[6]);
    double dUMax = (double)PyFloat_AsDouble(args[7]);
    Seiffert traj(sGeoPara, sGradPara, dM, dUMax);

    vv3 vv3K0;
    vvv3 vvv3Grad;
    getG(&traj, &vv3K0, &vvv3Grad, true);

    return Py_BuildValue("OO", cvtVv3toList(vv3K0), cvtVvv3toList(vvv3Grad));
}

PyObject* getG_Cones(PyObject* self, PyObject* const* args, Py_ssize_t narg)
{
    checkNarg(narg, 7);

    MrTraj::GeoPara sGeoPara;
    MrTraj::GradPara sGradPara;
    getGeoGradPara(args, &sGeoPara, &sGradPara);

    double dRhoPhi = (double)PyFloat_AsDouble(args[6]);
    Cones traj(sGeoPara, sGradPara, dRhoPhi);

    vv3 vv3K0;
    vvv3 vvv3Grad;
    getG(&traj, &vv3K0, &vvv3Grad, true);

    return Py_BuildValue("OO", cvtVv3toList(vv3K0), cvtVvv3toList(vvv3Grad));
}

PyObject* setSolverMtg(PyObject* self, PyObject* const* args, Py_ssize_t narg)
{
    extern bool g_bUseMtg_MrTraj;
    checkNarg(narg, 1);
    g_bUseMtg_MrTraj = PyLong_AsLong(args[0]);
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* setTrajRev(PyObject* self, PyObject* const* args, Py_ssize_t narg)
{
    checkNarg(narg, 1);
    g_bTrajRev_Main = PyLong_AsLong(args[0]);
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* setGoldAng(PyObject* self, PyObject* const* args, Py_ssize_t narg)
{
    checkNarg(narg, 1);
    g_bTrajGoldAng_Main = PyLong_AsLong(args[0]);
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* setShuf(PyObject* self, PyObject* const* args, Py_ssize_t narg)
{
    checkNarg(narg, 1);
    g_bShuf_Main = PyLong_AsLong(args[0]);
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* setMaxG0(PyObject* self, PyObject* const* args, Py_ssize_t narg)
{
    checkNarg(narg, 1);
    g_bMaxG0_Main = PyLong_AsLong(args[0]);
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* setMaxG1(PyObject* self, PyObject* const* args, Py_ssize_t narg)
{
    checkNarg(narg, 1);
    g_bMaxG1_Main = PyLong_AsLong(args[0]);
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* setExGEnd(PyObject* self, PyObject* const* args, Py_ssize_t narg)
{
    extern bool g_bFixGEnd_MrTraj;
    
    checkNarg(narg, 1);
    g_bFixGEnd_MrTraj = PyLong_AsLong(args[0]);
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* setMagOv(PyObject* self, PyObject* const* args, Py_ssize_t narg)
{
    extern int64_t g_lOv_Mag;
    checkNarg(narg, 1);
    g_lOv_Mag = PyLong_AsLong(args[0]);
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* setMagSFS(PyObject* self, PyObject* const* args, Py_ssize_t narg)
{
    extern bool g_bSFS_Mag;
    checkNarg(narg, 1);
    g_bSFS_Mag = PyLong_AsLong(args[0]);
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* setMagGradRep(PyObject* self, PyObject* const* args, Py_ssize_t narg)
{
    extern bool g_bGradRep_Mag;
    checkNarg(narg, 1);
    g_bGradRep_Mag = PyLong_AsLong(args[0]);
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* setMagTrajRep(PyObject* self, PyObject* const* args, Py_ssize_t narg)
{
    extern bool g_bTrajRep_Mag;
    checkNarg(narg, 1);
    g_bTrajRep_Mag = PyLong_AsLong(args[0]);
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* setDbgPrint(PyObject* self, PyObject* const* args, Py_ssize_t narg)
{
    extern bool g_bDbgPrint;
    checkNarg(narg, 1);
    g_bDbgPrint = PyLong_AsLong(args[0]);
    Py_INCREF(Py_None);
    return Py_None;
}

vv3 vv3Test;
PyObject* getTestVal(PyObject* self, PyObject* const* args, Py_ssize_t narg)
{
    checkNarg(narg, 0);
    return Py_BuildValue("O", cvtVv3toNpa(vv3Test));
}

static PyMethodDef aMeth[] = 
{
    {"calGrad4ExFunc", (PyCFunction)calGrad4ExFunc, METH_FASTCALL, ""},
    {"calGrad4ExSamp", (PyCFunction)calGrad4ExSamp, METH_FASTCALL, ""},
    {"getG_Spiral", (PyCFunction)getG_Spiral, METH_FASTCALL, ""},
    {"getG_VarDenSpiral", (PyCFunction)getG_VarDenSpiral, METH_FASTCALL, ""},
    {"getG_Rosette", (PyCFunction)getG_Rosette, METH_FASTCALL, ""},
    {"getG_Rosette_Trad", (PyCFunction)getG_Rosette_Trad, METH_FASTCALL, ""},
    {"getG_Shell3d", (PyCFunction)getG_Shell3d, METH_FASTCALL, ""},
    {"getG_Yarnball", (PyCFunction)getG_Yarnball, METH_FASTCALL, ""},
    {"getG_Seiffert", (PyCFunction)getG_Seiffert, METH_FASTCALL, ""},
    {"getG_Cones", (PyCFunction)getG_Cones, METH_FASTCALL, ""},
    {"setSolverMtg", (PyCFunction)setSolverMtg, METH_FASTCALL, ""},
    {"setTrajRev", (PyCFunction)setTrajRev, METH_FASTCALL, ""},
    {"setGoldAng", (PyCFunction)setGoldAng, METH_FASTCALL, ""},
    {"setShuf", (PyCFunction)setShuf, METH_FASTCALL, ""},
    {"setMaxG0", (PyCFunction)setMaxG0, METH_FASTCALL, ""},
    {"setMaxG1", (PyCFunction)setMaxG1, METH_FASTCALL, ""},
    {"setExGEnd", (PyCFunction)setExGEnd, METH_FASTCALL, ""},
    {"getTestVal", (PyCFunction)getTestVal, METH_FASTCALL, ""},
    {"setMagOv", (PyCFunction)setMagOv, METH_FASTCALL, ""},
    {"setMagSFS", (PyCFunction)setMagSFS, METH_FASTCALL, ""},
    {"setMagGradRep", (PyCFunction)setMagGradRep, METH_FASTCALL, ""},
    {"setMagTrajRep", (PyCFunction)setMagTrajRep, METH_FASTCALL, ""},
    {"setDbgPrint", (PyCFunction)setDbgPrint, METH_FASTCALL, ""},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

static struct PyModuleDef sMod = 
{
    PyModuleDef_HEAD_INIT,
    "ext",   /* name of module */
    NULL,
    -1,
    aMeth
};

PyMODINIT_FUNC
PyInit_ext(void)
{
    import_array();
    return PyModule_Create(&sMod);
}