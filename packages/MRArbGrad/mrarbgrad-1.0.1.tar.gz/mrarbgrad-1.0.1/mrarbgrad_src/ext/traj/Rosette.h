#pragma once

#include "TrajFunc.h"
#include "MrTraj_2D.h"

class Rosette_TrajFunc: public TrajFunc
{
public:
    Rosette_TrajFunc(double dOm1, double dOm2, double dTmax=1e0)
    {
        /*
         * NOTE:
         * When Tmax=1, Om1=Npi, Om2=(N-2)pi,
         * there will be N petal because Om1
         * controls how fast the rho changes.
         */
        m_dOm1 = dOm1;
        m_dOm2 = dOm2;
        m_dTmax = dTmax;

        m_dP0 = 0e0;
        m_dP1 = m_dTmax;
    }

    bool getK(v3* pv3K, double dP) const
    {
        double& dT = dP;
        double dRho = 0.5e0*std::sin(m_dOm1*dT);
        pv3K->m_dX = dRho * std::cos(m_dOm2*dT);
        pv3K->m_dY = dRho * std::sin(m_dOm2*dT);
        pv3K->m_dZ = 0e0;

        return true;
    }
protected:
    double m_dOm1, m_dOm2, m_dTmax;
};

class Rosette: public MrTraj_2D
{
public:
    Rosette(const GeoPara& sGeoPara, const GradPara& sGradPara, double dOm1, double dOm2, double dTmax)
    {
        m_sGeoPara = sGeoPara;
        m_sGradPara = sGradPara;
        const bool& bMaxG0 = m_sGradPara.bMaxG0;
        const bool& bMaxG1 = m_sGradPara.bMaxG1;

        m_ptfBaseTraj = new Rosette_TrajFunc(dOm1, dOm2, dTmax);
        if(!m_ptfBaseTraj) throw std::runtime_error("out of memory");
        m_lNRot = calNRot(m_ptfBaseTraj, 0e0, (M_PI/2e0)/dOm1, m_sGeoPara.lNPix);
        m_lNStack = m_sGeoPara.bIs3D ? m_sGeoPara.lNPix : 1;
        m_lNAcq = m_lNRot*m_lNStack;

        m_dRotAngInc = calRotAngInc(m_lNRot);
        
        calGrad(&m_v3BaseM0PE, &m_lv3BaseGRO, NULL, &m_lNWait, &m_lNSamp, *m_ptfBaseTraj, m_sGradPara, bMaxG0&&bMaxG1?2:8);
    }
    
    virtual ~Rosette()
    {
        delete m_ptfBaseTraj;
    }

protected:
    TrajFunc* m_ptfBaseTraj;
};

class Rosette_Trad: public MrTraj_2D
{
public:
    Rosette_Trad(const GeoPara& sGeoPara, const GradPara& sGradPara, double dOm1, double dOm2, double dTmax, double dDTE)
    {
        m_sGeoPara = sGeoPara;
        m_sGradPara = sGradPara;

        m_ptfBaseTraj = new Rosette_TrajFunc(dOm1, dOm2, dTmax);
        if(!m_ptfBaseTraj) throw std::runtime_error("out of memory");
        m_lNRot = calNRot(m_ptfBaseTraj, 0e0, (M_PI/2e0)/dOm1, m_sGeoPara.lNPix);
        m_lNStack = m_sGeoPara.bIs3D ? m_sGeoPara.lNPix : 1;
        m_lNAcq = m_lNRot*m_lNStack;

        m_dRotAngInc = calRotAngInc(m_lNRot);

        // readout
        double dTacq = dDTE*dOm1/M_PI;
        int64_t lNSamp = dTacq/m_sGradPara.dDt;
        for(int64_t i = 0; i < lNSamp; ++i)
        {
            m_lv3BaseGRO.push_back(v3());
            m_ptfBaseTraj->getDkDp(&*m_lv3BaseGRO.rbegin(), dTmax*i/(double)lNSamp); // derivative to p
            *m_lv3BaseGRO.rbegin() *= dTmax/dTacq; // derivative to t
        }
        lv3 lv3GRampFront; GradGen::ramp_front(&lv3GRampFront, *m_lv3BaseGRO.begin(), v3(0,0,0), m_sGradPara.dSLim, m_sGradPara.dDt);
        lv3 lv3GRampBack; GradGen::ramp_back(&lv3GRampBack, *m_lv3BaseGRO.rbegin(), v3(0,0,0), m_sGradPara.dSLim, m_sGradPara.dDt);

        m_lNWait = lv3GRampFront.size();
        m_lNSamp = m_lv3BaseGRO.size();

        // calculate M0 of PE
        m_ptfBaseTraj->getK0(&m_v3BaseM0PE);
        v3 v3M0Ramp; GradGen::calM0(&v3M0Ramp, lv3GRampFront, m_sGradPara.dDt, v3(0,0,0), *m_lv3BaseGRO.begin());
        m_v3BaseM0PE -= v3M0Ramp;
        
        // concate ramp gradient
        m_lv3BaseGRO.splice(m_lv3BaseGRO.begin(), lv3GRampFront);
        m_lv3BaseGRO.splice(m_lv3BaseGRO.end(), lv3GRampBack);
    }
    
    virtual ~Rosette_Trad()
    {
        delete m_ptfBaseTraj;
    }

protected:
    TrajFunc* m_ptfBaseTraj;
};
