#pragma once

#include <vector>
#include <list>
#include <tuple>
#include <cmath>
#include <stdexcept>
#include <algorithm>
#include "../utility/global.h"
#include "../utility/v3.h"
#include "../traj/TrajFunc.h"
#include "../utility/SplineIntp.h"

// virtual TrajFunc, take in discrete samples and construct a Segmentied Cubic Polynomial function
class Spline_TrajFunc: public TrajFunc
{
public:
    typedef std::vector<v3> vv3;
    typedef std::vector<double> vd;

    Spline_TrajFunc() {}

    Spline_TrajFunc(const vv3& vv3K)
    {
        int64_t lNTrajSamp = vv3K.size();

        vd vdP(lNTrajSamp);
        vdP[0] = 0;
        for (int64_t i = 1; i < lNTrajSamp; ++i)
        {
            vdP[i] = vdP[i-1] + v3::norm(vv3K[i] - vv3K[i-1]);
        }

        vd vdX(lNTrajSamp), vdY(lNTrajSamp), vdZ(lNTrajSamp);
        for (int64_t i = 0; i < lNTrajSamp; ++i)
        {
           vdX[i] =  vv3K[i].m_dX;
           vdY[i] =  vv3K[i].m_dY;
           vdZ[i] =  vv3K[i].m_dZ;
        }

        m_intpX.m_eSearchMode = Intp::ECached;
        m_intpY.m_eSearchMode = Intp::ECached;
        m_intpZ.m_eSearchMode = Intp::ECached;

        m_intpX.fit(vdP, vdX); 
        m_intpY.fit(vdP, vdY);
        m_intpZ.fit(vdP, vdZ);

        m_dP0 = *vdP.begin();
        m_dP1 = *vdP.rbegin();
    }
    
    bool getK(v3* pv3K, double dP) const
    {
        pv3K->m_dX = m_intpX.eval(dP);
        pv3K->m_dY = m_intpY.eval(dP);
        pv3K->m_dZ = m_intpZ.eval(dP);

        return true;
    }

    bool getDkDp(v3* pv3K, double dP) const
    {
        pv3K->m_dX = m_intpX.eval(dP, 1);
        pv3K->m_dY = m_intpY.eval(dP, 1);
        pv3K->m_dZ = m_intpZ.eval(dP, 1);

        return true;
    }

    bool getD2kDp2(v3* pv3K, double dP) const
    {
        pv3K->m_dX = m_intpX.eval(dP, 2);
        pv3K->m_dY = m_intpY.eval(dP, 2);
        pv3K->m_dZ = m_intpZ.eval(dP, 2);

        return true;
    }
protected:
    SplineIntp m_intpX, m_intpY, m_intpZ;
};

class GradGen
{
public:
    typedef std::vector<int64_t> vl;
    typedef std::vector<double> vd;
    typedef std::list<int64_t> ll;
    typedef std::list<double> ld;

    typedef std::vector<v3> vv3;
    typedef std::vector<vv3> vvv3;
    typedef std::list<v3> lv3;
    typedef std::list<vv3> lvv3;

    GradGen
    (
        const TrajFunc* ptTraj,
        double dSLim, double dGLim,
        double dDt=10e-6, int64_t lOs=10, 
        double dG0Norm=0e0, double dG1Norm=0e0
    );
    GradGen
    (
        const vv3& vv3TrajSamp,
        double dSLim, double dGLim,
        double dDt=10e-6, int64_t lOs=10, 
        double dG0Norm=0e0, double dG1Norm=0e0
    );
    ~GradGen();
    bool compute(lv3* plv3G, ld* pldP=NULL);
    template <typename dtype, typename cv3>
    static bool decomp
    (
        std::vector<dtype>* pvfGx,
        std::vector<dtype>* pvfGy,
        std::vector<dtype>* pvfGz,
        const cv3& cv3G,
        bool bResize = false,
        bool bFillZero = true
    );
    static bool ramp_front(lv3* plv3GRamp, const v3& v3G0, const v3& v3G0Des, double dSLim, double dDt);
    static double ramp_front(lv3* plv3GRamp, const v3& v3G0, const v3& v3G0Des, int64_t lNSamp, double dDt);
    static bool ramp_back(lv3* plv3GRamp, const v3& v3G1, const v3& v3G1Des, double dSLim, double dDt);
    static double ramp_back(lv3* plv3GRamp, const v3& v3G1, const v3& v3G1Des, int64_t lNSamp, double dDt);
    static bool revGrad(v3* pv3M0Dst, lv3* plv3Dst, const v3& v3M0Src, const lv3& lv3Src, double dDt);
    static bool calM0(v3* pv3M0, const lv3& lv3Grad, double dDt, const v3& v3GBegin=v3(0,0,0), const v3& v3GEnd=v3(0,0,0));
private:
    Spline_TrajFunc m_sptfTraj;
    const TrajFunc* m_ptfTraj;
    const double m_dSLim, m_dGLim;
    const double m_dDt;
    const int64_t m_lOs;
    const double m_dG0Norm, m_dG1Norm;

    // reserved vector for faster computation
    vd m_vdP_Bac;
    vv3 m_vv3G_Bac;
    vd m_vdGNorm_Bac;

    vd m_vdP_For;
    vv3 m_vv3G_For;

    bool sovQDE(double* pdSol0, double* pdSol1, double dA, double dB, double dC);
    double getCurRad(double dP);
    double getDp(const v3& v3GPrev, const v3& v3GThis, double dDt, double dPPrev, double dPThis, double dSignDp);
    double getDp(const v3& v3G, double dDt, double dP, double dSignDp);
    bool step(v3* pv3GUnit, double* pdGNormMin, double* pdGNormMax, double dP, double dSignDp, const v3& v3G, double dSLim, double dDt);
};

// definition must be in `.h` file (compiler limitation)
template <typename dtype, typename cv3>
bool GradGen::decomp
(
    std::vector<dtype>* pvfGx,
    std::vector<dtype>* pvfGy,
    std::vector<dtype>* pvfGz,
    const cv3& cv3G,
    bool bResize,
    bool bFillZero
)
{
    if (bResize)
    {
        pvfGx->resize(cv3G.size());
        pvfGy->resize(cv3G.size());
        pvfGz->resize(cv3G.size());
    }
    if (bFillZero)
    {
        std::fill(pvfGx->begin(), pvfGx->end(), (dtype)0);
        std::fill(pvfGy->begin(), pvfGy->end(), (dtype)0);
        std::fill(pvfGz->begin(), pvfGz->end(), (dtype)0);
    }
    typename std::vector<dtype>::iterator ivfGx = pvfGx->begin();
    typename std::vector<dtype>::iterator ivfGy = pvfGy->begin();
    typename std::vector<dtype>::iterator ivfGz = pvfGz->begin();
    typename cv3::const_iterator icv3G = cv3G.begin();
    while (icv3G != cv3G.end())
    {
        *ivfGx = dtype(icv3G->m_dX);
        *ivfGy = dtype(icv3G->m_dY);
        *ivfGz = dtype(icv3G->m_dZ);
        ++ivfGx;
        ++ivfGy;
        ++ivfGz;
        ++icv3G;
    }
    return true;
}