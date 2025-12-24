#pragma once

#include <cmath>
#include <ctime>

template<typename T>
inline T round(T x)
{
    return (x >= 0) ? std::floor(x + T(0.5)) : std::ceil(x - T(0.5));
}

#undef M_PI
#define M_PI (3.14159265358979323846)

#define PRINT(X) printf("%s: %ld\n", #X, (int64_t)(X));
#define PRINT_F(X) printf("%s: %.3f\n", #X, (double)(X));
#define PRINT_E(X) printf("%s: %.3e\n", #X, (double)(X));

#define TIC \
    clock_t cTick = std::clock();\

#define TOC \
    cTick = std::clock() - cTick;\
    if (g_bDbgPrint) printf("Elapsed time: %.3f ms\n", (float)1e3*cTick/CLOCKS_PER_SEC);

extern bool g_bDbgPrint;
    