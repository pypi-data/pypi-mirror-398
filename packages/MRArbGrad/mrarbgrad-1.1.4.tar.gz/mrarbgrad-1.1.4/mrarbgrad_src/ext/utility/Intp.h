#pragma once

#include <stdint.h>
#include <vector>
#include <stdexcept>
#include <cmath>
#include <algorithm>

class Intp
{
public:
    typedef std::vector<double> vd;
    
    enum SearchMode
    {
        EBinary = 0,
        ECached,
        EUniform
    } m_eSearchMode;

    Intp() : m_eSearchMode(EBinary), m_lIdxCache(0) {}
    virtual ~Intp() {}

    virtual bool fit(const vd& vdX, const vd& vdY) = 0;

    virtual double eval(double dXEval, int64_t lOrder = 0) const = 0;

protected:
    vd m_vdX, m_vdY;
    mutable int64_t m_lIdxCache;

    static bool validate(vd& vdX, vd& vdY)
    {
        if (vdX.size() != vdY.size() || vdX.size() < 2) return false;
        int64_t lN = int64_t(vdX.size());
        if (lN == 2 && vdX[0] == vdX[1]) return false;
        for (int64_t i = 2; i < lN; ++i)
        {
            if ((vdX[i]-vdX[i - 1]) * (vdX[i - 1]-vdX[i - 2]) < 0) return false;
        }
        if (vdX.back() < vdX.front())
        {
            std::reverse(vdX.begin(), vdX.end());
            std::reverse(vdY.begin(), vdY.end());
        }
        return true;
    }

    int64_t getIdx(const double& dXEval) const
    {
        const int64_t lN = int64_t(m_vdX.size());
        if (lN < 2) throw std::runtime_error("lN");

        int64_t lIdx;

        if (m_eSearchMode == EBinary)
        {
            int64_t lIdxLow = 0;
            int64_t lIdxHigh = lN - 1;
            while (lIdxHigh - lIdxLow > 1)
            {
                int64_t mid = (lIdxLow + lIdxHigh) / 2;
                if (m_vdX[mid] > dXEval) lIdxHigh = mid;
                else                     lIdxLow = mid;
            }
            lIdx = lIdxLow;
            return lIdx;
        }
        if (m_eSearchMode == ECached)
        {
            if (m_lIdxCache < 0) m_lIdxCache = 0;
            if (m_lIdxCache > lN - 2) m_lIdxCache = lN - 2;
            lIdx = m_lIdxCache;
            while (lIdx > 0 && m_vdX[lIdx] > dXEval) --lIdx;
            while (lIdx + 1 < lN - 1 && m_vdX[lIdx + 1] < dXEval) ++lIdx;
            m_lIdxCache = lIdx;
            return lIdx;
        }
        if (m_eSearchMode == EUniform)
        {
            const double x0 = m_vdX.front();
            const double x1 = m_vdX.back();
            lIdx = int64_t((dXEval - x0) / (x1 - x0) * (lN - 1));
            if (lIdx < 0) lIdx = 0;
            if (lIdx > lN - 2) lIdx = lN - 2;
            return lIdx;
        }

        throw std::invalid_argument("m_eSearchMode");
    }
};