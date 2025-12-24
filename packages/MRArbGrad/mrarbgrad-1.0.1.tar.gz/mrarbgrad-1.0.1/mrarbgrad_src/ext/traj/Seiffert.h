#pragma once

#include "TrajFunc.h"
#include "MrTraj.h"
#include <vector>
#include <list>

#define LOOKUP_TABLE (0)

static bool cvtXyz2Ang(double* pdTht, double* pdPhi, const v3& v3Xyz)
{
    const double& dX = v3Xyz.m_dX;
    const double& dY = v3Xyz.m_dY;
    const double& dZ = v3Xyz.m_dZ;
    double dXY = std::sqrt(dX*dX + dY*dY);
    *pdTht = std::atan2(dXY, dZ);
    *pdPhi = std::atan2(dY, dX);

    return true;
}

class Seiffert_Trajfunc: public TrajFunc
{
public:
    typedef std::vector<double> vd;
    typedef std::list<double> ld;

    Seiffert_Trajfunc(double dM, double dUMax):
        m_lNPhi(100000)
    {
        m_dM = dM;
        m_dUMax = dUMax;

        initJacElip(m_dM);

        m_dP0 = 0e0;
        m_dP1 = dUMax;
        m_dThtBias = 0e0; m_dPhiBias = 0e0;
        v3 v3EndPt; getK(&v3EndPt, dUMax);
        cvtXyz2Ang(&m_dThtBias, &m_dPhiBias, v3EndPt);
    }
    
    bool getK(v3* pv3K, double dU) const
    {
        double dSn, dCn;
        calJacElip(&dSn, &dCn, dU);

        double dRho = 0.5e0 * (dU/m_dUMax);
        pv3K->m_dX = dRho * dSn * std::cos(dU*std::sqrt(m_dM));
        pv3K->m_dY = dRho * dSn * std::sin(dU*std::sqrt(m_dM));
        pv3K->m_dZ = dRho * dCn;

        v3::rotate(pv3K, 2, -m_dPhiBias, *pv3K);
        v3::rotate(pv3K, 1, -m_dThtBias, *pv3K);

        return true;
    }
    
protected:
    double m_dM, m_dUMax;

    // precompute for AGM
    ld m_ldA, m_ldB, m_ldC; 

    // precompute lookup table for phi
    const int64_t m_lNPhi; vd m_vdPhi;
    double m_dUPeriod;
    
    double m_dThtBias, m_dPhiBias;

    bool initJacElip(double dM)
    {
        if (dM<0e0 || dM>1e0)
        {
            printf("ArgError, dM=%lf\n", dM);
            abort();
        }

        // calculate a, b, c value of AGM
        m_ldA.clear(); m_ldA.push_back(1e0);
        m_ldB.clear(); m_ldB.push_back(std::sqrt(1e0-dM));
        m_ldC.clear(); m_ldC.push_back(0e0);
        while (std::fabs(*m_ldB.rbegin() - *m_ldA.rbegin()) > 1e-8)
        {
            const double& dA_Old = *std::prev(m_ldA.end());
            const double& dB_Old = *std::prev(m_ldB.end());
            m_ldA.push_back((dA_Old + dB_Old) / 2e0);
            m_ldB.push_back(std::sqrt(dA_Old * dB_Old));
            m_ldC.push_back((dA_Old - dB_Old) / 2e0);
        }

        #if LOOKUP_TABLE
        // calculate corresponding phi of m
        int64_t lN = m_ldA.size() - 1;

        double dElipInt = calCompElipInt(dM);
        m_dUPeriod = 4e0*dElipInt;
        m_vdPhi.resize(m_lNPhi);
        for (int64_t i = 0; i < m_lNPhi; ++i)
        {
            double dU = m_dUPeriod * i/(double)m_lNPhi;

            // calculate phi with AGM
            ld::const_reverse_iterator ildA = m_ldA.rbegin();
            ld::const_reverse_iterator ildC = m_ldC.rbegin();
            double dPhi = std::pow(2e0,double(lN)) * (*ildA) * dU;
            for (int64_t j = 0; j < lN; ++j)
            {
                dPhi = (1e0/2e0)*(dPhi + std::asin((*ildC)/(*ildA)*std::sin(dPhi)));
                ++ildA;
                ++ildC;
            }
            m_vdPhi[i] = dPhi;
        }
        #endif

        return true;
    }
    
    bool calJacElip(double* pdSn, double* pdCn, double dU) const
    {
        #if LOOKUP_TABLE
        double dIPhi = m_lNPhi * dU/m_dUPeriod;
        double dIPhi0 = std::floor(dIPhi);
        double dIPhi1 = std::ceil(dIPhi);
        if (dIPhi1 == dIPhi0) // test
        {
            double dPhi = m_vdPhi[(int64_t)dIPhi%m_lNPhi];
            *pdSn = std::sin(dPhi);
            *pdCn = std::cos(dPhi);
        }
        else
        {
            double dPhi0 = m_vdPhi[int64_t(dIPhi0)%m_lNPhi];
            double dPhi1 = m_vdPhi[int64_t(dIPhi1)%m_lNPhi];

            *pdSn = std::sin(dPhi0)*(dIPhi1-dIPhi) + std::sin(dPhi1)*(dIPhi-dIPhi0);
            *pdCn = std::cos(dPhi0)*(dIPhi1-dIPhi) + std::cos(dPhi1)*(dIPhi-dIPhi0);
        }
        #else
        // calculate phi with AGM
        int64_t lN = m_ldA.size() - 1;
        ld::const_reverse_iterator ildA = m_ldA.rbegin();
        ld::const_reverse_iterator ildC = m_ldC.rbegin();
        double dPhi = std::pow(2e0,double(lN)) * (*ildA) * dU;
        for (int64_t j = 0; j < lN; ++j)
        {
            dPhi = (1e0/2e0)*(dPhi + std::asin((*ildC)/(*ildA)*std::sin(dPhi)));
            ++ildA;
            ++ildC;
        }
        *pdSn = std::sin(dPhi);
        *pdCn = std::cos(dPhi);
        #endif
        
        return true;
    }

    static double calCompElipInt(double dM)
    {
        ld ldA, ldB;
        ldA.push_back(1e0);
        ldB.push_back(std::sqrt(1e0 - dM));
        while (std::fabs(ldB.back() - ldA.back()) > 1e-8)
        {
            double aNew = (ldA.back() + ldB.back()) / 2e0;
            double bNew = std::sqrt(ldA.back() * ldB.back());
            ldA.push_back(aNew);
            ldB.push_back(bNew);
        }
        double dRes = M_PI / 2e0 / ldA.back();
        return dRes;
    }
};

class Seiffert: public MrTraj
{
public:
    Seiffert(const GeoPara& sGeoPara, const GradPara& sGradPara, double dM, double dUMax)
    // m = 0.07 is optimized for diaphony
    // Umax = 20 can achieve similar readout time as original paper
    {
        m_sGeoPara = sGeoPara;
        m_sGradPara = sGradPara;
        const int64_t& lNPix = m_sGeoPara.lNPix;
        const bool& bMaxG0 = m_sGradPara.bMaxG0;
        const bool& bMaxG1 = m_sGradPara.bMaxG1;
        m_lNAcq = (int64_t)round(-2.53819233e-03*lNPix*lNPix + 8.53447761e+01*lNPix); // fitted

        m_ptfBaseTraj = new Seiffert_Trajfunc(dM, dUMax);
        if(!m_ptfBaseTraj) throw std::runtime_error("out of memory");

        calGrad(&m_v3BaseM0PE, &m_lv3BaseGRO, NULL, &m_lNWait, &m_lNSamp, *m_ptfBaseTraj, m_sGradPara, bMaxG0&&bMaxG1?2:8);
    }
    
    virtual ~Seiffert()
    {
        delete m_ptfBaseTraj;
    }

    bool getM0PE(v3* pv3M0PE, int64_t lIAcq) const
    {
        bool bRet = true;
        vl vlAx; vd vdAng;
        bRet &= getRotAng(&vlAx, &vdAng, lIAcq);
        bRet &= appRotAng(pv3M0PE, m_v3BaseM0PE, vlAx, vdAng);

        return bRet;
    }
    
    bool getGRO(lv3* plv3GRO, int64_t lIAcq) const
    {
        bool bRet = true;
        vl vlAx; vd vdAng;
        bRet &= getRotAng(&vlAx, &vdAng, lIAcq);
        bRet &= appRotAng(plv3GRO, m_lv3BaseGRO, vlAx, vdAng);

        return bRet;
    }

    int64_t getNWait(int64_t lIAcq) const
    {
        return m_lNWait;
    }

    int64_t getNSamp(int64_t lIAcq) const
    {
        return m_lNSamp;
    }
    
protected:
    TrajFunc* m_ptfBaseTraj;
    v3 m_v3BaseM0PE;
    lv3 m_lv3BaseGRO;
    int64_t m_lNWait;
    int64_t m_lNSamp;

    bool getRotAng(vl* pvlAx, vd* pvdAng, int64_t lIAcq) const
    {
        pvlAx->resize(3);
        pvdAng->resize(3);

        // randomly rotate around z-axis
        pvlAx->at(0) = 2;
        pvdAng->at(0) = lIAcq*(lIAcq+1)*GOLDANG;

        // rotate endpoint to Fibonaci Points
        v3 v3FibPt;
        {
            int64_t lNf = m_lNAcq;
            double dK = double(lIAcq%m_lNAcq) - lNf/2;

            double dSf = dK/(lNf/2);
            double dCf = std::sqrt((lNf/2+dK)*(lNf/2-dK)) / (lNf/2);
            double dPhi = (1e0+std::sqrt(5e0)) / 2e0;
            double dTht = 2e0*M_PI*dK/dPhi;

            v3FibPt.m_dX = dCf*std::sin(dTht);
            v3FibPt.m_dY = dCf*std::cos(dTht);
            v3FibPt.m_dZ = dSf;
        }
        double dTht, dPhi; cvtXyz2Ang(&dTht, &dPhi, v3FibPt);

        pvlAx->at(1) = 1;
        pvdAng->at(1) = dTht;
        pvlAx->at(2) = 2;
        pvdAng->at(2) = dPhi;

        return true;
    }

    template<typename T>
    bool appRotAng(T* ptDst, const T& tSrc, vl vlAx, vd vdAng) const
    {
        bool bRet = true;

        if (vlAx.size() != vdAng.size()) throw std::invalid_argument("pllAx->size() != pldAng->size()");

        *ptDst = tSrc;
        for(int64_t i = 0; i < (int64_t)vlAx.size(); ++i)
        {
            bRet &= v3::rotate(ptDst, vlAx[i], vdAng[i], *ptDst);
        }

        return bRet;
    }
};

#undef LOOKUP_TABLE
