#include "v3.h"
#include <array>

v3::v3() :m_dX(0e0), m_dY(0e0), m_dZ(0e0) {}
v3::v3(double dX, double dY, double dZ) :m_dX(dX), m_dY(dY), m_dZ(dZ) {}
v3::~v3() {}

v3 v3::operator+(const v3 &rhs) const
{
    return v3
    (
        this->m_dX + rhs.m_dX,
        this->m_dY + rhs.m_dY,
        this->m_dZ + rhs.m_dZ
    );
}

v3& v3::operator+=(const v3 &rhs)
{
    this->m_dX += rhs.m_dX;
    this->m_dY += rhs.m_dY;
    this->m_dZ += rhs.m_dZ;
    return *this;
}

v3 v3::operator+(const double &rhs) const
{
    return v3
    (
        this->m_dX + rhs,
        this->m_dY + rhs,
        this->m_dZ + rhs
    );
}

v3& v3::operator+=(const double &rhs)
{
    this->m_dX += rhs;
    this->m_dY += rhs;
    this->m_dZ += rhs;
    return *this;
}

v3 v3::operator-(const v3 &rhs) const
{
    return v3
    (
        this->m_dX - rhs.m_dX,
        this->m_dY - rhs.m_dY,
        this->m_dZ - rhs.m_dZ
    );
}

v3& v3::operator-=(const v3 &rhs)
{
    this->m_dX -= rhs.m_dX;
    this->m_dY -= rhs.m_dY;
    this->m_dZ -= rhs.m_dZ;
    return *this;
}

v3 v3::operator-(const double &rhs) const
{
    return v3
    (
        this->m_dX - rhs,
        this->m_dY - rhs,
        this->m_dZ - rhs
    );
}

v3& v3::operator-=(const double &rhs)
{
    this->m_dX -= rhs;
    this->m_dY -= rhs;
    this->m_dZ -= rhs;
    return *this;
}

v3 v3::operator*(const v3 &rhs) const
{
    return v3
    (
        this->m_dX * rhs.m_dX,
        this->m_dY * rhs.m_dY,
        this->m_dZ * rhs.m_dZ
    );
}

v3& v3::operator*=(const v3 &rhs)
{
    this->m_dX *= rhs.m_dX;
    this->m_dY *= rhs.m_dY;
    this->m_dZ *= rhs.m_dZ;
    return *this;
}

v3 v3::operator*(const double &rhs) const
{
    return v3
    (
        this->m_dX * rhs,
        this->m_dY * rhs,
        this->m_dZ * rhs
    );
}

v3& v3::operator*=(const double &rhs)
{
    this->m_dX *= rhs;
    this->m_dY *= rhs;
    this->m_dZ *= rhs;
    return *this;
}

v3 v3::operator/(const v3 &rhs) const
{
    return v3
    (
        this->m_dX / rhs.m_dX,
        this->m_dY / rhs.m_dY,
        this->m_dZ / rhs.m_dZ
    );
}

v3& v3::operator/=(const v3 &rhs)
{
    this->m_dX /= rhs.m_dX;
    this->m_dY /= rhs.m_dY;
    this->m_dZ /= rhs.m_dZ;
    return *this;
}

v3 v3::operator/(const double &rhs) const
{
    return v3
    (
        this->m_dX / rhs,
        this->m_dY / rhs,
        this->m_dZ / rhs
    );
}

v3& v3::operator/=(const double &rhs)
{
    this->m_dX /= rhs;
    this->m_dY /= rhs;
    this->m_dZ /= rhs;
    return *this;
}

bool v3::operator==(const v3 &rhs) const
{
    return bool
    (
        this->m_dX == rhs.m_dX &&
        this->m_dY == rhs.m_dY &&
        this->m_dZ == rhs.m_dZ
    );
}

bool v3::operator!=(const v3 &rhs) const
{
    return bool
    (
        this->m_dX != rhs.m_dX ||
        this->m_dY != rhs.m_dY ||
        this->m_dZ != rhs.m_dZ
    );
}

double v3::norm(const v3& v3_tObj)
{
    return sqrt
    (
        v3_tObj.m_dX*v3_tObj.m_dX +
        v3_tObj.m_dY*v3_tObj.m_dY +
        v3_tObj.m_dZ*v3_tObj.m_dZ
    );
}

v3 v3::cross(const v3& v3_tObj0, const v3& v3_tObj1)
{
    return v3
    (
        v3_tObj0.m_dY*v3_tObj1.m_dZ - v3_tObj0.m_dZ*v3_tObj1.m_dY,
        -v3_tObj0.m_dX*v3_tObj1.m_dZ + v3_tObj0.m_dZ*v3_tObj1.m_dX,
        v3_tObj0.m_dX*v3_tObj1.m_dY - v3_tObj0.m_dY*v3_tObj1.m_dX
    );
}

double v3::inner(const v3& v3_tObj0, const v3& v3_tObj1)
{
    return double
    (
        v3_tObj0.m_dX*v3_tObj1.m_dX +
        v3_tObj0.m_dY*v3_tObj1.m_dY +
        v3_tObj0.m_dZ*v3_tObj1.m_dZ
    );
}

v3 v3::pow(const v3& v3_tObj, double dPow)
{
    return v3
    (
        std::pow(v3_tObj.m_dX, dPow),
        std::pow(v3_tObj.m_dY, dPow),
        std::pow(v3_tObj.m_dZ, dPow)
    );
}

bool v3::genRotMat(std::array<v3,3>* pav3RotMat, int iAx, double dAng)
{
    switch (iAx)
    {
    case 0:
        (*pav3RotMat)[0] = v3(1e0, 0e0, 0e0);
        (*pav3RotMat)[1] = v3(0e0, std::cos(dAng), -std::sin(dAng));
        (*pav3RotMat)[2] = v3(0e0, std::sin(dAng), std::cos(dAng));
        break;
    case 1:
        (*pav3RotMat)[0] = v3(std::cos(dAng), 0e0, std::sin(dAng));
        (*pav3RotMat)[1] = v3(0e0, 1e0, 0e0);
        (*pav3RotMat)[2] = v3(-std::sin(dAng), 0e0, std::cos(dAng));
        break;
    case 2:
        (*pav3RotMat)[0] = v3(std::cos(dAng), -std::sin(dAng), 0e0);
        (*pav3RotMat)[1] = v3(std::sin(dAng), std::cos(dAng), 0e0);
        (*pav3RotMat)[2] = v3(0e0, 0e0, 1e0);
        break;
    default:
        return false;
    }

    return true;
}

bool v3::rotate
(
    v3* pv3Dst,
    int iAx, double dAng,
    const v3& v3Src
)
{
    bool bRet = true;

    std::array<v3,3> av3RotMat;
    bRet &= genRotMat(&av3RotMat, iAx, dAng);

    *pv3Dst = v3
    (
        v3::inner(av3RotMat[0], v3Src),
        v3::inner(av3RotMat[1], v3Src),
        v3::inner(av3RotMat[2], v3Src)
    );

    return bRet;
}

bool v3::rotate
(
    vv3* pvv3Dst,
    int iAx, double dAng,
    const vv3& vv3Src
)
{
    bool bRet = true;

    std::array<v3,3> av3RotMat;
    bRet &= genRotMat(&av3RotMat, iAx, dAng);

    // apply rotation matrix
    vv3 _vv3Dst(vv3Src.size()); // for self-in self-out compatible
    vv3::const_iterator ivv3CoordSrc = vv3Src.begin();
    vv3::iterator ivv3CoordDst = _vv3Dst.begin();
    while (ivv3CoordSrc != vv3Src.end())
    {
        ivv3CoordDst->m_dX = v3::inner(av3RotMat[0], *ivv3CoordSrc);
        ivv3CoordDst->m_dY = v3::inner(av3RotMat[1], *ivv3CoordSrc);
        ivv3CoordDst->m_dZ = v3::inner(av3RotMat[2], *ivv3CoordSrc);

        ++ivv3CoordSrc;
        ++ivv3CoordDst;
    }
    *pvv3Dst = _vv3Dst;

    return bRet;
}

bool v3::rotate
(
    lv3* plv3Dst,
    int iAx, double dAng,
    const lv3& lv3Src
)
{
    bool bRet = true;

    std::array<v3,3> av3RotMat;
    bRet &= genRotMat(&av3RotMat, iAx, dAng);

    // apply rotation matrix
    lv3 _lv3Dst; // for self-in self-out compatible
    lv3::const_iterator ilv3CoordSrc = lv3Src.begin();
    while (ilv3CoordSrc != lv3Src.end())
    {
        _lv3Dst.push_back
        (
            v3
            (
                v3::inner(av3RotMat[0], *ilv3CoordSrc),
                v3::inner(av3RotMat[1], *ilv3CoordSrc),
                v3::inner(av3RotMat[2], *ilv3CoordSrc)
            )
        );

        ++ilv3CoordSrc;
    }
    *plv3Dst = _lv3Dst;

    return bRet;
}