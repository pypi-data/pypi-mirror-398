#pragma once

#include "Intp.h"

class LinIntp : public Intp
{
public:
    LinIntp() {}

    LinIntp(const vd& vdX, const vd& vdY)
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

        const int64_t lN = static_cast<int64_t>(m_vdX.size());
        m_vdSlope.resize(lN - 1);

        for (int64_t i = 0; i < lN - 1; ++i)
        {
            const double dDX = m_vdX[i + 1] - m_vdX[i];
            m_vdSlope[i] = (m_vdY[i + 1] - m_vdY[i]) / dDX;
        }

        return true;
    }

    virtual double eval(double dXEval, int64_t lOrder = 0) const
    {
        if (m_vdX.size() < 2) throw std::runtime_error("m_vdX.size()");

        const int64_t lIdx = getIdx(dXEval);
        const double dDX = dXEval - m_vdX[lIdx];

        if (lOrder == 0)
        {
            return m_vdY[lIdx] + m_vdSlope[lIdx] * dDX;
        }
        if (lOrder == 1)
        {
            return m_vdSlope[lIdx];
        }

        return 0e0;
    }

private:
    vd m_vdSlope;
};
