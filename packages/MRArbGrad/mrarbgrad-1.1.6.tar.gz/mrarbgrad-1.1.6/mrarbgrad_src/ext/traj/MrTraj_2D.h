#pragma once

#include "MrTraj.h"
#include "../mag/GradGen.h"

class MrTraj_2D: public MrTraj
{
public:
    MrTraj_2D() {}
    
    virtual ~MrTraj_2D()
    {}
    
    bool getM0PE(v3* pv3M0PE, int64_t lIAcq) const
    {
        bool bRet = true;
        int64_t lIStack = lIAcq%m_lNStack;
        int64_t lIRot = lIAcq/m_lNStack;
        
        *pv3M0PE = m_v3BaseM0PE;
        pv3M0PE->m_dZ += getK0z(lIStack, m_lNStack);
        
        bRet &= v3::rotate(pv3M0PE, 2, m_dRotAngInc*lIRot, *pv3M0PE);

        return bRet;
    }

    bool getGRO(lv3* plv3GRO, int64_t lIAcq) const
    {
        bool bRet = true;
        // int64_t lIStack = lIAcq%m_lNStack;
        int64_t lIRot = lIAcq/m_lNStack;

        bRet &= v3::rotate(plv3GRO, 2, m_dRotAngInc*lIRot, m_lv3BaseGRO);

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

    int64_t getNRot()
    { return m_lNRot; }

    int64_t getNStack()
    { return m_lNStack; }

    double getRotAngInc()
    { return m_dRotAngInc; }

    bool setRotAngInc(double dRotAngInc=GOLDANG)
    {
        m_dRotAngInc = dRotAngInc;
        return true;
    }

protected:
    int64_t m_lNRot, m_lNStack;
    double m_dRotAngInc;

    v3 m_v3BaseM0PE;
    lv3 m_lv3BaseGRO;
    int64_t m_lNWait;
    int64_t m_lNSamp;

    static double getK0z(int64_t lIStack, int64_t lNStack=256)
    {
        return lIStack/(double)lNStack - (lNStack/2)/(double)lNStack;
    }
};
