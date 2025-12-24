#pragma once

#include "Intp.h"

class SplineIntp : public Intp
{
public:
    SplineIntp() {}

    explicit SplineIntp(const vd& vdX, const vd& vdY)
    {
        fit(vdX, vdY);
    }

    virtual bool fit(const vd& vdX, const vd& vdY)
    {
        m_vdX = vdX;
        m_vdY = vdY;

        if (!validate(m_vdX, m_vdY))
        {
            m_vdX.clear();
            m_vdY.clear();
            throw std::invalid_argument("validate(vdX, vdY)");
        }

        m_lIdxCache = 0;

        const int64_t lN = int64_t(m_vdX.size());

        vd vdH(lN - 1);
        for (int64_t i = 0; i < lN - 1; ++i)
            vdH[i] = m_vdX[i + 1] - m_vdX[i];

        // Step 1: Set up the tridiagonal system
        vd vdAlpha(lN, 0.0);
        for (int64_t i = 1; i < lN - 1; ++i)
            vdAlpha[i] = (3e0 / vdH[i]) * (m_vdY[i + 1] - m_vdY[i]) - (3e0 / vdH[i - 1]) * (m_vdY[i] - m_vdY[i - 1]);

        // Step 2: Solve tridiagonal system for c (second derivatives)
        vd vdL(lN, 1.0), vdMu(lN, 0.0), vdZ(lN, 0.0);
        m_vdC.resize(lN, 0.0);
        m_vdB.resize(lN - 1, 0.0);
        m_vdD.resize(lN - 1, 0.0);
        m_vdA = m_vdY;

        for (int64_t i = 1; i < lN - 1; ++i)
        {
            vdL[i] = 2e0 * (m_vdX[i + 1] - m_vdX[i - 1]) - vdH[i - 1] * vdMu[i - 1];
            vdMu[i] = vdH[i] / vdL[i];
            vdZ[i] = (vdAlpha[i] - vdH[i - 1] * vdZ[i - 1]) / vdL[i];
        }

        // Natural spline boundary conditions
        vdL[lN - 1] = 1.0;
        vdZ[lN - 1] = 0.0;
        m_vdC[lN - 1] = 0.0;

        // Back substitution
        for (int64_t i = lN - 2; i >= 0; --i)
        {
            m_vdC[i] = vdZ[i] - vdMu[i] * m_vdC[i + 1];
            m_vdB[i] = (m_vdA[i + 1] - m_vdA[i]) / vdH[i] - vdH[i] * (m_vdC[i + 1] + 2e0 * m_vdC[i]) / 3e0;
            m_vdD[i] = (m_vdC[i + 1] - m_vdC[i]) / (3e0 * vdH[i]);
        }

        return true;
    }

    virtual double eval(double dXEval, int64_t lOrder = 0) const // order: order of derivation, default is 0 (function value)
    {
        if (m_vdX.size() < 2) throw std::runtime_error("m_vdX.size()");

        int64_t lIdx = getIdx(dXEval);

        double dDx = dXEval - m_vdX[lIdx];
        if (lOrder == 0) return
        (
            m_vdA[lIdx]
            + m_vdB[lIdx] * dDx
            + m_vdC[lIdx] * dDx * dDx
            + m_vdD[lIdx] * dDx * dDx * dDx
        );
        if (lOrder == 1) return
        (
            m_vdB[lIdx]
            + m_vdC[lIdx] * 2e0 * dDx
            + m_vdD[lIdx] * 3e0 * dDx * dDx
        );
        if (lOrder == 2) return
        (
            m_vdC[lIdx] * 2e0
            + m_vdD[lIdx] * 6e0 * dDx
        );
        if (lOrder == 3) return
        (
            m_vdD[lIdx] * 6e0
        );
        return 0e0;
    }

private:
    vd m_vdA, m_vdB, m_vdC, m_vdD;
};
