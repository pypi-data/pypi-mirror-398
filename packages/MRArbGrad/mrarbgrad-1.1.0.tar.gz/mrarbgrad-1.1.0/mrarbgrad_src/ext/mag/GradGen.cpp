#include <cassert>
#include <algorithm>
#include <cstdio>
#include "../utility/global.h"
#include "../utility/LinIntp.h"
#include "GradGen.h"
#include "../utility/SplineIntp.h"

int64_t g_lOv_Mag = -1; // oversample ratio, overwrite set value
bool g_bSFS_Mag = false; // Single Forward Sweep flag
bool g_bGradRep_Mag = true; // Gradient Reparameterization
bool g_bTrajRep_Mag = true; // use trajectory reparameterization for MAG solver
int64_t g_lNTrajSamp_Mag = 1000; // num. of samp. when doing Traj. Rep.

GradGen::GradGen
    (
        const TrajFunc* ptTraj,
        double dSLim, double dGLim,
        double dDt, int64_t lOs, 
        double dG0Norm, double dG1Norm
    ):
    m_sptfTraj(),
    m_ptfTraj(),
    m_dSLim(dSLim), 
    m_dGLim(dGLim), 
    m_dDt(dDt), 
    m_lOs(g_lOv_Mag>0?g_lOv_Mag:lOs), 
    m_dG0Norm(dG0Norm), 
    m_dG1Norm(dG1Norm)
{
    int64_t lSizeReserve = int64_t(100e-3/m_dDt*m_lOs); // reserve for 100ms

    m_vdP_Bac.reserve(lSizeReserve);
    m_vv3G_Bac.reserve(lSizeReserve);
    m_vdGNorm_Bac.reserve(lSizeReserve);

    m_vdP_For.reserve(lSizeReserve);
    m_vv3G_For.reserve(lSizeReserve);

    if (g_bTrajRep_Mag)
    {
        vv3 vv3TrajSamp(g_lNTrajSamp_Mag);
        double dP0 = ptTraj->getP0();
        double dP1 = ptTraj->getP1();
        for (int64_t i = 0; i < g_lNTrajSamp_Mag; ++i)
        {
            double dP = dP0 + (dP1-dP0) * (i)/double(g_lNTrajSamp_Mag-1);
            ptTraj->getK(&vv3TrajSamp[i], dP);
        }
        m_sptfTraj = Spline_TrajFunc(vv3TrajSamp);
        m_ptfTraj = &m_sptfTraj;
    }
    else
    {
        m_ptfTraj = ptTraj;
    }
}

GradGen::GradGen
    (
        const vv3& vv3TrajSamp,
        double dSLim, double dGLim,
        double dDt, int64_t lOs, 
        double dG0Norm, double dG1Norm
    ):
    m_sptfTraj(vv3TrajSamp),
    m_ptfTraj(&m_sptfTraj),
    m_dSLim(dSLim), 
    m_dGLim(dGLim), 
    m_dDt(dDt), 
    m_lOs(g_lOv_Mag>0?g_lOv_Mag:lOs), 
    m_dG0Norm(dG0Norm), 
    m_dG1Norm(dG1Norm)
{
    int64_t lSizeReserve = int64_t(100e-3/m_dDt*m_lOs); // reserve for 100ms

    m_vdP_Bac.reserve(lSizeReserve);
    m_vv3G_Bac.reserve(lSizeReserve);
    m_vdGNorm_Bac.reserve(lSizeReserve);

    m_vdP_For.reserve(lSizeReserve);
    m_vv3G_For.reserve(lSizeReserve);
}

GradGen::~GradGen()
{

}

bool GradGen::sovQDE(double* pdSol0, double* pdSol1, double dA, double dB, double dC)
{
    double dDelta = dB*dB - 4e0*dA*dC;
    if (pdSol0) *pdSol0 = (-dB-(dDelta<0?0:std::sqrt(dDelta)))/(2*dA);
    if (pdSol1) *pdSol1 = (-dB+(dDelta<0?0:std::sqrt(dDelta)))/(2*dA);
    return dDelta>=0;
}

double GradGen::getCurRad(double dP)
{
    v3 v3DkDp; m_ptfTraj->getDkDp(&v3DkDp, dP);
    v3 v3D2kDp2; m_ptfTraj->getD2kDp2(&v3D2kDp2, dP);
    double dNume = pow(v3::norm(v3DkDp), 3e0);
    double dDeno = v3::norm(v3::cross(v3DkDp, v3D2kDp2));
    return dNume/dDeno;
}

#if 1

double GradGen::getDp(const v3& v3GPrev, const v3& v3GThis, double dDt, double dPPrev, double dPThis, double dSignDp)
{
    // solve `ΔP` by RK2
    double dDl = v3::norm(v3GThis)*dDt;
    // k1
    double dK1;
    {
        v3 v3DkDp; m_ptfTraj->getDkDp(&v3DkDp, dPThis);
        double dDlDp = v3::norm(v3DkDp)*dSignDp;
        dK1 = 1e0/dDlDp;
    }
    // k2
    double dK2;
    {
        v3 v3DkDp; m_ptfTraj->getDkDp(&v3DkDp, dPThis+dK1*dDl);
        double dDlDp = v3::norm(v3DkDp)*dSignDp;
        dK2 = 1e0/dDlDp;
    }
    double dDp = dDl*(0.5*dK1 + 0.5*dK2);
    return dDp;
}

#else // less accurate due to estimation of PNext

double GradGen::getDp(const v3& v3GPrev, const v3& v3GThis, double dDt, double dPPrev, double dPThis, double dSignDp)
{
    // solve `ΔP` by RK2
    double dDl = v3::norm(v3GThis)*dDt;
    v3 v3DkDp0; m_ptfTraj->getDkDp(&v3DkDp0, dPThis);
    v3 v3DkDp1; m_ptfTraj->getDkDp(&v3DkDp1, dPThis*2e0-dPPrev);
    double dDlDp0 = v3::norm(v3DkDp0)*dSignDp;
    double dDlDp1 = v3::norm(v3DkDp1)*dSignDp;
    return dDl*(1e0/dDlDp0 + 1e0/dDlDp1)/2e0;
}

#endif

bool GradGen::step(v3* pv3GUnit, double* pdGNormMin, double* pdGNormMax, double dP, double dSignDp, const v3& v3G, double dSLim, double dDt)
{
    // current gradient direction
    v3 v3DkDp; m_ptfTraj->getDkDp(&v3DkDp, dP);
    double dDlDp = v3::norm(v3DkDp)*dSignDp;
    if (pv3GUnit) *pv3GUnit = v3DkDp/dDlDp;
    
    // current gradient magnitude
    bool bQDESucc = sovQDE
    (
        pdGNormMin, pdGNormMax,
        1e0,
        -2e0*v3::inner(v3G, *pv3GUnit),
        v3::inner(v3G, v3G) - std::pow(dSLim*dDt, 2e0)
    );
    if (pdGNormMin) *pdGNormMin = fabs(*pdGNormMin);
    if (pdGNormMax) *pdGNormMax = fabs(*pdGNormMax);

    return bQDESucc;
}

bool GradGen::compute(lv3* plv3G, ld* pldP)
{
    bool bRet = true;
    double dP0 = m_ptfTraj->getP0();
    double dP1 = m_ptfTraj->getP1();
    ld ldP; if (!pldP) pldP = &ldP;
    bool bQDESucc = true; (void)bQDESucc;
    int64_t lNit = 0;

    // backward
    v3 v3G1Unit; bRet &= m_ptfTraj->getDkDp(&v3G1Unit, dP1);
    v3G1Unit = v3G1Unit * (dP0>dP1?1e0:-1e0);
    v3G1Unit = v3G1Unit / v3::norm(v3G1Unit);
    double dG1Norm = m_dG1Norm;
    dG1Norm = std::min(dG1Norm, m_dGLim);
    dG1Norm = std::min(dG1Norm, std::sqrt(m_dSLim*getCurRad(dP1)));
    v3 v3G1 = v3G1Unit * dG1Norm;

    m_vdP_Bac.clear(); m_vdP_Bac.push_back(dP1);
    m_vv3G_Bac.clear(); m_vv3G_Bac.push_back(v3G1);
    m_vdGNorm_Bac.clear(); m_vdGNorm_Bac.push_back(v3::norm(v3G1));
    while (!g_bSFS_Mag)
    {
        double dP = m_vdP_Bac.back();
        v3 v3G = m_vv3G_Bac.back();
        
        // update grad
        v3 v3GUnit;
        double dGNorm;
        bQDESucc = step(&v3GUnit, NULL, &dGNorm, dP, (dP0-dP1)/std::fabs(dP0-dP1), v3G, m_dSLim, m_dDt/m_lOs);
        dGNorm = std::min(dGNorm, m_dGLim);
        dGNorm = std::min(dGNorm, std::sqrt(m_dSLim*getCurRad(dP)));
        v3G = v3GUnit*dGNorm;

        // update para
        dP += getDp(m_vv3G_Bac.back(), v3G, m_dDt/m_lOs, m_vdP_Bac.back(), dP, (dP0-dP1)/std::fabs(dP0-dP1));

        // stop or append
        if (std::fabs(m_vdP_Bac.back() - dP1) >= (1-1e-6)*std::fabs(dP0 - dP1))
        {
            // printf("bac: dP/dP1 = %lf/%lf\n", dP, dP1); // test
            break;
        }
        else
        {
            // printf("bac: dP = %lf\n", dP); // test
            m_vdP_Bac.push_back(dP);
            m_vv3G_Bac.push_back(v3G);
            m_vdGNorm_Bac.push_back(v3::norm(v3G));
        }
    }

    std::reverse(m_vdP_Bac.begin(), m_vdP_Bac.end());
    std::reverse(m_vdGNorm_Bac.begin(), m_vdGNorm_Bac.end());

    LinIntp intp;
    // SplineIntp intp;
    intp.m_eSearchMode = Intp::ECached;
    if (!g_bSFS_Mag) intp.fit(m_vdP_Bac, m_vdGNorm_Bac);
    
    lNit += m_vdP_Bac.size();

    // forward
    v3 v3G0Unit; bRet &= m_ptfTraj->getDkDp(&v3G0Unit, dP0);
    v3G0Unit = v3G0Unit * (dP1>dP0?1e0:-1e0);
    v3G0Unit = v3G0Unit / v3::norm(v3G0Unit);
    double dG0Norm = m_dG0Norm;
    dG0Norm = std::min(dG0Norm, m_dGLim);
    dG0Norm = std::min(dG0Norm, std::sqrt(m_dSLim*getCurRad(dP0)));
    dG0Norm = std::min(dG0Norm, g_bSFS_Mag?1e15:intp.eval(dP0));
    v3 v3G0 = v3G0Unit * dG0Norm;

    m_vdP_For.clear(); m_vdP_For.push_back(dP0);
    m_vv3G_For.clear(); m_vv3G_For.push_back(v3G0);
    while (1)
    {
        double dP = m_vdP_For.back();
        v3 v3G = m_vv3G_For.back();

        // update grad
        v3 v3GUnit;
        double dGNorm;
        bQDESucc = step(&v3GUnit, NULL, &dGNorm, dP, (dP1-dP0)/std::fabs(dP1-dP0), v3G, m_dSLim, m_dDt/m_lOs);
        if (g_bSFS_Mag)
        {
            dGNorm = std::min(dGNorm, m_dGLim);
            dGNorm = std::min(dGNorm, std::sqrt(m_dSLim*getCurRad(dP)));
        }
        else
        {
            double dGNormBac = intp.eval(dP);
            dGNorm = std::min(dGNorm, dGNormBac);
            if (dGNormBac<=0)
            {
                dGNorm *= -1;
                v3GUnit *= -1;
            }
        }
        v3G = v3GUnit*dGNorm;

        // update para
        dP += getDp(m_vv3G_For.back(), v3G, m_dDt/m_lOs, m_vdP_For.back(), dP, (dP1-dP0)/std::fabs(dP1-dP0));

        // stop or append
        if (std::fabs(m_vdP_For.back() - dP0) >= (1-1e-6)*std::fabs(dP1 - dP0)) // || dGNorm <= 0)
        {
            // printf("for: dP/dP1 = %lf/%lf\n", dP, dP1); // test
            break;
        }
        else
        {
            // printf("for: dP = %lf\n", dP); // test
            m_vdP_For.push_back(dP);
            m_vv3G_For.push_back(v3G);
        }
    }
    lNit += m_vdP_For.size();
    
    if (g_bDbgPrint)
    {
        int64_t MAG_Nit = lNit;
        PRINT(MAG_Nit);
    }

    // deoversamp the para. vec.
    {
        pldP->clear();
        int64_t n = m_vdP_For.size();
        for (int64_t i = 0; i < n; ++i)
        {
            if(i%m_lOs==m_lOs/2) pldP->push_back(m_vdP_For[i]);
        }
    }

    // derive gradient
    if (g_bGradRep_Mag)
    {
        plv3G->clear();
        v3 v3K1, v3K0; 
        ld::iterator ildP = std::next(pldP->begin());
        int64_t n = pldP->size();
        for (int64_t i = 1; i < n; ++i)
        {
            bRet &= m_ptfTraj->getK(&v3K1, *ildP);
            bRet &= m_ptfTraj->getK(&v3K0, *std::prev(ildP));
            plv3G->push_back((v3K1 - v3K0)/m_dDt);
            ++ildP;
        }
    }
    else
    {
        plv3G->clear();
        int64_t n = m_vv3G_For.size();
        for (int64_t i = 0; i < n; ++i)
        {
            if(i%m_lOs==0) plv3G->push_back(m_vv3G_For[i]);
        }
    }
    pldP->pop_front();

    return bRet;
}

bool GradGen::ramp_front(lv3* plv3GRamp, const v3& v3G0, const v3& v3G0Des, double dSLim, double dDt)
{
    v3 v3Dg = v3G0Des - v3G0;
    v3 v3DgUnit = v3::norm(v3Dg)!=0 ? v3Dg/v3::norm(v3Dg) : v3(0,0,0);
    int64_t lNSamp = (int64_t)std::ceil(v3::norm(v3Dg)/(dSLim*dDt));

    // derive ramp gradient
    plv3GRamp->clear();
    for (int64_t i = 1; i < lNSamp; ++i)
    {
        plv3GRamp->push_front(v3G0 + v3DgUnit * (dSLim*dDt) * i);
    }
    if (lNSamp>0) plv3GRamp->push_front(v3G0Des);
    
    return true;
}

double GradGen::ramp_front(lv3* plv3GRamp, const v3& v3G0, const v3& v3G0Des, int64_t lNSamp, double dDt)
{
    v3 v3Dg = v3G0Des - v3G0;
    v3 v3DgUnit = v3::norm(v3Dg)!=0 ? v3Dg/v3::norm(v3Dg) : v3(0,0,0);
    double dSLim = v3::norm(v3Dg)/(lNSamp*dDt);

    // derive ramp gradient
    plv3GRamp->clear();
    for (int64_t i = 1; i < lNSamp; ++i)
    {
        plv3GRamp->push_front(v3G0 + v3DgUnit * (dSLim*dDt) * i);
    }
    if (lNSamp>0) plv3GRamp->push_front(v3G0Des);

    return dSLim;
}

bool GradGen::ramp_back(lv3* plv3GRamp, const v3& v3G1, const v3& v3G1Des, double dSLim, double dDt)
{
    v3 v3Dg = v3G1Des - v3G1;
    v3 v3DgUnit = v3::norm(v3Dg)!=0 ? v3Dg/v3::norm(v3Dg) : v3(0,0,0);
    int64_t lNSamp = (int64_t)std::ceil(v3::norm(v3Dg)/(dSLim*dDt));

    // derive ramp gradient
    plv3GRamp->clear();
    for (int64_t i = 1; i < lNSamp; ++i)
    {
        plv3GRamp->push_back(v3G1 + v3DgUnit * (dSLim*dDt) * i);
    }
    if (lNSamp>0) plv3GRamp->push_back(v3G1Des);
    
    return true;
}

double GradGen::ramp_back(lv3* plv3GRamp, const v3& v3G1, const v3& v3G1Des, int64_t lNSamp, double dDt)
{
    v3 v3Dg = v3G1Des - v3G1;
    v3 v3DgUnit = v3::norm(v3Dg)!=0 ? v3Dg/v3::norm(v3Dg) : v3(0,0,0);
    double dSLim = v3::norm(v3Dg)/(lNSamp*dDt);

    // derive ramp gradient
    plv3GRamp->clear();
    for (int64_t i = 1; i < lNSamp; ++i)
    {
        plv3GRamp->push_back(v3G1 + v3DgUnit * (dSLim*dDt) * i);
    }
    if (lNSamp>0) plv3GRamp->push_back(v3G1Des);
    
    return dSLim;
}

bool GradGen::revGrad(v3* pv3M0Dst, lv3* plv3Dst, const v3& v3M0Src, const lv3& lv3Src, double dDt)
{
    bool bRet = true;

    if(lv3Src.size() <= 1) bRet = false;

    // derive Total M0
    *pv3M0Dst = v3M0Src;
    lv3::const_iterator ilv3Src = lv3Src.begin();
    for(int64_t i = 0; i < (int64_t)lv3Src.size()-1; ++i)
    {
        *pv3M0Dst += (*ilv3Src + *std::next(ilv3Src))*dDt/2e0;
        ++ilv3Src;
    }

    // reverse gradient
    *plv3Dst = lv3(lv3Src.rbegin(), lv3Src.rend());
    lv3::iterator ilv3Dst = plv3Dst->begin();
    while (ilv3Dst != plv3Dst->end())
    {
        *ilv3Dst *= -1;
        ++ilv3Dst;
    }

    return bRet;
}

bool GradGen::calM0(v3* pv3M0, const lv3& lv3Grad, double dDt, const v3& v3GBegin, const v3& v3GEnd)
{
    *pv3M0 = v3(0,0,0);
    const v3* pv3Grad = &v3GBegin;
    lv3::const_iterator ilv3Grad = lv3Grad.begin();
    while (ilv3Grad != lv3Grad.end())
    {
        *pv3M0 += (*pv3Grad + *ilv3Grad)*dDt/2e0;
        pv3Grad = &*ilv3Grad;
        ++ilv3Grad;
    }
    *pv3M0 += (*pv3Grad + v3GEnd)*dDt/2e0;

    return true;
}