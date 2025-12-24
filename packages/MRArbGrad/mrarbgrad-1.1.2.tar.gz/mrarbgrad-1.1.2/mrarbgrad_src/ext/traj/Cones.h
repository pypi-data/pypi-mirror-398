#pragma once

#include "TrajFunc.h"
#include "MrTraj.h"

class Cones;

class Cones_TrajFun: public TrajFunc
{
public:
    friend Cones;

    Cones_TrajFun(double dRhoPhi, double dTht0)
    {
        m_dRhoPhi = dRhoPhi;
        m_dTht0 = dTht0;
        m_dP0 = 0e0;
        m_dP1 = 0.5e0/m_dRhoPhi;
    }

    bool getK(v3* pv3K, double dPhi) const
    {
        double dRho = m_dRhoPhi*dPhi;

        pv3K->m_dX = dRho * std::sin(m_dTht0) * std::cos(dPhi);
        pv3K->m_dY = dRho * std::sin(m_dTht0) * std::sin(dPhi);
        pv3K->m_dZ = dRho * std::cos(m_dTht0);

        return true;
    }

protected:
    double m_dRhoPhi;
    double m_dTht0;
};

class Cones: public MrTraj
{
public:
    typedef std::list<int64_t> ll;

    Cones(const GeoPara& sGeoPara, const GradPara& sGradPara, double dRhoPhi)
    {
        m_sGeoPara = sGeoPara;
        m_sGradPara = sGradPara;
        const int64_t& lNPix = m_sGeoPara.lNPix;
        const bool& bMaxG0 = m_sGradPara.bMaxG0;
        const bool& bMaxG1 = m_sGradPara.bMaxG1;

        // caluclate gradient
        m_lNSet = getNLayer_Cones(lNPix);
        m_vptfBaseTraj.resize(m_lNSet);
        m_vv3BaseM0PE.resize(m_lNSet);
        m_vlv3BaseGRO.resize(m_lNSet);
        m_vlNWait.resize(m_lNSet);
        m_vlNSamp.resize(m_lNSet);
        
        for (int64_t i = 0; i < m_lNSet; ++i)
        {
            double dTht0 = getTht0_Cones(i, m_lNSet);
            m_vptfBaseTraj[i] = new Cones_TrajFun(dRhoPhi, dTht0);
            if(!m_vptfBaseTraj[i]) throw std::runtime_error("out of memory");

            calGrad(&m_vv3BaseM0PE[i], &m_vlv3BaseGRO[i], NULL, &m_vlNWait[i], &m_vlNSamp[i], *m_vptfBaseTraj[i], m_sGradPara, bMaxG0&&bMaxG1?2:8);
        }
        
        // list of `ISet` and `IRot`
        m_vlNRot.resize(m_lNSet);
        m_lNAcq = 0;
        ll llSetIdx, llRotIdx;
        for (int64_t i = 0; i < m_lNSet; ++i)
        {
            m_vlNRot[i] = calNRot
            (
                m_vptfBaseTraj[i], 
                m_vptfBaseTraj[i]->getP0(), 
                m_vptfBaseTraj[i]->getP1(),
                lNPix
            );

            for (int64_t j = 0; j < m_vlNRot[i]; ++j)
            {
                llSetIdx.push_back(i);
                llRotIdx.push_back(j);
            }

            m_lNAcq += m_vlNRot[i];
        }
        m_vlSetIdx = vl(llSetIdx.begin(), llSetIdx.end());
        m_vlRotIdx = vl(llRotIdx.begin(), llRotIdx.end());
    }

    virtual ~Cones()
    {
        for(int64_t i = 0; i < (int64_t)m_vptfBaseTraj.size(); ++i)
        {
            delete m_vptfBaseTraj[i];
        }
    }

    bool getM0PE(v3* pv3M0PE, int64_t lIAcq) const
    {
        bool bRet = true;
        lIAcq %= m_lNAcq;
        int64_t lISet = m_vlSetIdx[lIAcq];
        int64_t lIRot = m_vlRotIdx[lIAcq];
        double dPhiInc = calRotAngInc(m_vlNRot[lISet]);

        *pv3M0PE = m_vv3BaseM0PE[lISet];
        bRet &= v3::rotate(pv3M0PE, 2, dPhiInc*lIRot, *pv3M0PE);

        return bRet;
    }
    
    bool getGRO(lv3* plv3GRO, int64_t lIAcq) const
    {
        bool bRet = true;
        lIAcq %= m_lNAcq;
        int64_t lISet = m_vlSetIdx[lIAcq];
        int64_t lIRot = m_vlRotIdx[lIAcq];
        double dPhiInc = calRotAngInc(m_vlNRot[lISet]);

        *plv3GRO = m_vlv3BaseGRO[lISet];
        bRet &= v3::rotate(plv3GRO, 2, dPhiInc*lIRot, *plv3GRO);

        return bRet;
    }

    int64_t getNWait(int64_t lIAcq) const
    {
        return m_vlNWait[m_vlSetIdx[lIAcq]];
    }

    int64_t getNSamp(int64_t lIAcq) const
    {
        return m_vlNSamp[m_vlSetIdx[lIAcq]];
    }

protected:
    double m_dRhoPhi;
    int64_t m_lNSet;
    vl m_vlNRot;
    vl m_vlSetIdx;
    vl m_vlRotIdx;

    vptf m_vptfBaseTraj;
    vv3 m_vv3BaseM0PE;
    vlv3 m_vlv3BaseGRO;
    vl m_vlNWait;
    vl m_vlNSamp;

    static int64_t getNLayer_Cones(int64_t lNPix)
    {
        return (int64_t)std::ceil(lNPix*M_PI/2e0);
    }

    static double getTht0_Cones(int64_t lILayer, int64_t lNLayer)
    {
        double dThtInc = M_PI / (lNLayer-1);
        return lILayer*dThtInc;
    }
};
