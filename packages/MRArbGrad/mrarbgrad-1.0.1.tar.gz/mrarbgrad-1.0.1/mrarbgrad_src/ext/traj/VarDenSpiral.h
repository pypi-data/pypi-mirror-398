#pragma once

#include "TrajFunc.h"
#include "MrTraj_2D.h"

class VarDenSpiral_TrajFunc: public TrajFunc
{
public:
    VarDenSpiral_TrajFunc(double dRhoPhi0, double dRhoPhi1)
    {
        m_dRhoPhi0 = dRhoPhi0;
        m_dRhoPhi1 = dRhoPhi1;

        m_dP0 = 0e0;
        m_dP1 = (std::log(m_dRhoPhi1)-std::log(m_dRhoPhi0)) / (2e0*(m_dRhoPhi1-m_dRhoPhi0));
    }

    bool getK(v3* pv3K, double dP) const
    {
        double& dPhi = dP;
        double dRho = m_dRhoPhi0*(std::exp(2e0*(m_dRhoPhi1 - m_dRhoPhi0)*dPhi) - 1e0) / (2e0*(m_dRhoPhi1 - m_dRhoPhi0));
        pv3K->m_dX = dRho * std::cos(dPhi);
        pv3K->m_dY = dRho * std::sin(dPhi);
        pv3K->m_dZ = 0e0;

        return true;
    }
protected:
    double m_dRhoPhi0;
    double m_dRhoPhi1;
};

class VarDenSpiral: public MrTraj_2D
{
public:
    VarDenSpiral(const GeoPara& sGeoPara, const GradPara& sGradPara, double dRhoPhi0, double dRhoPhi1)
    {
        if (dRhoPhi0==dRhoPhi1) throw std::invalid_argument("dRhoPhi0==dRhoPhi1");

        m_sGeoPara = sGeoPara;
        m_sGradPara = sGradPara;
        const bool& bMaxG0 = m_sGradPara.bMaxG0;
        const bool& bMaxG1 = m_sGradPara.bMaxG1;
        m_lNRot = calNRot(std::max(dRhoPhi0, dRhoPhi1), m_sGeoPara.lNPix);
        m_lNStack = m_sGeoPara.bIs3D ? m_sGeoPara.lNPix : 1;
        m_lNAcq = m_lNRot*m_lNStack;

        m_dRotAngInc = calRotAngInc(m_lNRot);
        m_ptfBaseTraj = new VarDenSpiral_TrajFunc(dRhoPhi0, dRhoPhi1);
        if(!m_ptfBaseTraj) throw std::runtime_error("out of memory");
        
        calGrad(&m_v3BaseM0PE, &m_lv3BaseGRO, NULL, &m_lNWait, &m_lNSamp, *m_ptfBaseTraj, m_sGradPara, bMaxG0&&bMaxG1?2:8);
    }
    
    virtual ~VarDenSpiral()
    {
        delete m_ptfBaseTraj;
    }

protected:
    TrajFunc* m_ptfBaseTraj;
};
