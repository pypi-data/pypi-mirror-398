#pragma once

#include "TrajFunc.h"
#include "MrTraj_2D.h"

class Spiral_TrajFunc: public TrajFunc
{
public:
    Spiral_TrajFunc(double dRhoPhi)
    {
        m_dRhoPhi = dRhoPhi;

        m_dP0 = 0e0;
        m_dP1 = 0.5e0/m_dRhoPhi;
    }

    bool getK(v3* pv3K, double dP) const
    {
        double& dPhi = dP;
        double dRho = m_dRhoPhi*dPhi;
        pv3K->m_dX = dRho * std::cos(dPhi);
        pv3K->m_dY = dRho * std::sin(dPhi);
        pv3K->m_dZ = 0e0;

        return true;
    }
protected:
    double m_dRhoPhi;
};

class Spiral: public MrTraj_2D
{
public:
    Spiral(const GeoPara& sGeoPara, const GradPara& sGradPara, double dRhoPhi)
    {
        m_sGeoPara = sGeoPara;
        m_sGradPara = sGradPara;
        const bool& bMaxG0 = m_sGradPara.bMaxG0;
        const bool& bMaxG1 = m_sGradPara.bMaxG1;
        m_lNRot = calNRot(dRhoPhi, m_sGeoPara.lNPix);
        m_lNStack = m_sGeoPara.bIs3D ? m_sGeoPara.lNPix : 1;
        m_lNAcq = m_lNRot*m_lNStack;

        m_dRotAngInc = calRotAngInc(m_lNRot);
        m_ptfBaseTraj = new Spiral_TrajFunc(dRhoPhi);
        if(!m_ptfBaseTraj) throw std::runtime_error("out of memory");

        calGrad(&m_v3BaseM0PE, &m_lv3BaseGRO, NULL, &m_lNWait, &m_lNSamp, *m_ptfBaseTraj, m_sGradPara, bMaxG0&&bMaxG1?2:8);
    }
    
    virtual ~Spiral()
    {
        delete m_ptfBaseTraj;
    }

protected:
    TrajFunc* m_ptfBaseTraj;
};
