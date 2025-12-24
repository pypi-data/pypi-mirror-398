#pragma once

#include "../utility/global.h"
#include "../utility/v3.h"
// #include "../mag/GradGen.h" // VS2010 does not like this...

/* 
 * Single trajectory define by a parameterized function getK()
 * and parameter bounding m_dP0, m_dP1
 */

class GradGen;

class TrajFunc
{
public:
    friend GradGen;
    
    TrajFunc() {}

    virtual ~TrajFunc () {}
    
    virtual bool getK(v3* pv3K, double dP) const = 0; // trajectory function
    
    virtual bool getDkDp(v3* pv3DkDp, double dP) const // 1st-ord differentiative of trajectory function
    {
        static const double dDp = 1e-7;
        v3 v3K_Nx1; getK(&v3K_Nx1, dP+dDp);
        v3 v3K_Pv1; getK(&v3K_Pv1, dP-dDp);
        *pv3DkDp = (v3K_Nx1-v3K_Pv1)/(2*dDp);

        return true;
    }

    virtual bool getD2kDp2(v3* pv3D2kDp2, double dP) const // 2nd-ord differentiative of trajectory function
    {
        static const double dDp = 1e-3;
        v3 v3K_Nx1; getK(&v3K_Nx1, dP+dDp);
        v3 v3K_This; getK(&v3K_This, dP);
        v3 v3K_Pv1; getK(&v3K_Pv1, dP-dDp);
        *pv3D2kDp2 = (v3K_Nx1-v3K_This*2+v3K_Pv1)/(dDp*dDp);
    
        return true;
    }
    
    double getP0() const { return m_dP0; }; // get the lower bound of traj. para.
    
    double getP1() const { return m_dP1; }; // get the higher bound of traj. para.

    bool getK0(v3* pv3K0) const { return getK(pv3K0, m_dP0); }
    
    bool getK1(v3* pv3K1) const { return getK(pv3K1, m_dP1); }

protected:
    double m_dP0, m_dP1;
};
