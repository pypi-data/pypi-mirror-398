#ifndef M4RI_M4RI_CONFIG_H
#define M4RI_M4RI_CONFIG_H

// Defines determined during configuration of m4ri.
#define __M4RI_HAVE_MM_MALLOC		1
#define __M4RI_HAVE_POSIX_MEMALIGN	0
#define __M4RI_HAVE_SSE2		0
#if 1 && defined(__SSE2__) && __SSE2__
#undef __M4RI_HAVE_SSE2
#define __M4RI_HAVE_SSE2		1
#endif
#define __M4RI_HAVE_OPENMP		1
#define __M4RI_CPU_L1_CACHE		0
#define __M4RI_CPU_L2_CACHE		0
#define __M4RI_CPU_L3_CACHE		0
#define __M4RI_DEBUG_DUMP		(0 || 0)
#define __M4RI_DEBUG_MZD		0
#define __M4RI_HAVE_LIBPNG              0

#define __M4RI_CC                       "x86_64-w64-mingw32-gcc"
#define __M4RI_CFLAGS                   "-fopenmp -fPIC -O3"
#define __M4RI_OPENMP_CFLAGS            "-fopenmp"

// Helper macros.
#define __M4RI_USE_MM_MALLOC		(__M4RI_HAVE_MM_MALLOC && __M4RI_HAVE_SSE2)
#define __M4RI_USE_POSIX_MEMALIGN	(__M4RI_HAVE_POSIX_MEMALIGN && __M4RI_HAVE_SSE2)
#define __M4RI_DD_QUIET			(0 && !0)

#define __M4RI_ENABLE_MZD_CACHE         0
#define __M4RI_ENABLE_MMC               1

#if defined(__MINGW32__) || defined(__MINGW64__)
#define random rand
#define srandom srand
#endif

#endif // M4RI_M4RI_CONFIG_H
