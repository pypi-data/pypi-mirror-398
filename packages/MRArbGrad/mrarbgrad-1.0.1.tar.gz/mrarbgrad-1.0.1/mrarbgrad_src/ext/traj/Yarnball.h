#pragma once

#include "TrajFunc.h"
#include "MrTraj.h"

class Yarnball_TrajFunc: public TrajFunc
{
public:
    Yarnball_TrajFunc(double dRhoPhi, double dTht0)
    {
        m_dPhiSqrtTht = std::sqrt(2e0);
        m_dRhoSqrtTht = std::sqrt(2e0)*dRhoPhi;
        m_dTht0 = dTht0;

        m_dP0 = 0e0;
        m_dP1 = 1e0/(std::sqrt(8e0)*dRhoPhi);
    }

    ~Yarnball_TrajFunc()
    {}

    bool getK(v3* pv3K, double dP) const
    {
        const double& dSqrtTht = dP;
        double dTht = dSqrtTht*dSqrtTht * (dSqrtTht>=0?1e0:-1e0);
        double dRho = m_dRhoSqrtTht * dSqrtTht;
        double dPhi = m_dPhiSqrtTht * dSqrtTht;

        pv3K->m_dX = dRho * std::sin(dTht+m_dTht0) * std::cos(dPhi);
        pv3K->m_dY = dRho * std::sin(dTht+m_dTht0) * std::sin(dPhi);
        pv3K->m_dZ = dRho * std::cos(dTht+m_dTht0);

        return true;
    }
protected:
    double m_dPhiSqrtTht, m_dRhoSqrtTht;
    double m_dTht0;
};

class Yarnball: public MrTraj
{
public:
    Yarnball(const GeoPara& sGeoPara, const GradPara& sGradPara, double dRhoPhi)
    {
        m_sGeoPara = sGeoPara;
        m_sGradPara = sGradPara;
        const bool& bMaxG0 = m_sGradPara.bMaxG0;
        const bool& bMaxG1 = m_sGradPara.bMaxG1;
        m_lNRot = calNRot(dRhoPhi, m_sGeoPara.lNPix);
        m_dRotInc = calRotAngInc(m_lNRot);
        m_lNAcq = m_lNRot*m_lNRot;
        
        m_vptfBaseTraj.resize(m_lNRot);
        m_vv3BaseM0PE.resize(m_lNRot);
        m_vlv3BaseGRO.resize(m_lNRot);
        m_vlNWait.resize(m_lNRot);
        m_vlNSamp.resize(m_lNRot);

        for(int64_t i = 0; i < m_lNRot; ++i)
        {
            double dTht0 = i*m_dRotInc;
            m_vptfBaseTraj[i] = new Yarnball_TrajFunc(dRhoPhi, dTht0);
            if(!m_vptfBaseTraj[i]) throw std::runtime_error("out of memory");

            calGrad(&m_vv3BaseM0PE[i], &m_vlv3BaseGRO[i], NULL, &m_vlNWait[i], &m_vlNSamp[i], *m_vptfBaseTraj[i], m_sGradPara, bMaxG0&&bMaxG1?2:8);
        }
    }
    
    virtual ~Yarnball()
    {
        for(int64_t i = 0; i < (int64_t)m_vptfBaseTraj.size(); ++i)
        {
            delete m_vptfBaseTraj[i];
        }
    }

    bool getM0PE(v3* pv3M0PE, int64_t lIAcq) const
    {
        bool bRet = true;
        const double& dPhiInc = m_dRotInc;
        int64_t lISet = lIAcq%m_lNRot;
        int64_t lIRot = lIAcq/m_lNRot;

        *pv3M0PE = m_vv3BaseM0PE[lISet];
        bRet &= v3::rotate(pv3M0PE, 2, dPhiInc*lIRot, *pv3M0PE);

        return bRet;
    }

    bool getGRO(lv3* plv3GRO, int64_t lIAcq) const
    {
        bool bRet = true;
        const double& dPhiInc = m_dRotInc;
        int64_t lISet = lIAcq%m_lNRot;
        int64_t lIRot = lIAcq/m_lNRot;

        *plv3GRO = m_vlv3BaseGRO[lISet];
        bRet &= v3::rotate(plv3GRO, 2, dPhiInc*lIRot, *plv3GRO);
        
        return bRet;
    }

    int64_t getNWait(int64_t lIAcq) const
    {
        int64_t lISet = lIAcq%m_lNRot;
        return m_vlNWait[lISet];
    }

    int64_t getNSamp(int64_t lIAcq) const
    {
        int64_t lISet = lIAcq%m_lNRot;
        return m_vlNSamp[lISet];
    }

protected:
    int64_t m_lNRot;
    double m_dRotInc;

    vptf m_vptfBaseTraj;
    vv3 m_vv3BaseM0PE;
    vlv3 m_vlv3BaseGRO;
    vl m_vlNWait;
    vl m_vlNSamp;
};
