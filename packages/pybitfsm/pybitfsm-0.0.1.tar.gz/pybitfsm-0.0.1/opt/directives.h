#ifndef BITFSM_OPT_DIRECTIVES_H_
#define BITFSM_OPT_DIRECTIVES_H_

// BITFSM_ALWAYS_INLINE marks a function that all callers must inline.
// BITFSM_NEVER_INLINE marks a function that no caller may inline.
#if defined(_MSC_VER)
  #define BITFSM_ALWAYS_INLINE __forceinline
  #define BITFSM_NEVER_INLINE __declspec(noinline)
#elif defined(__GNUC__) || defined(__clang__)
  #define BITFSM_ALWAYS_INLINE __attribute__((always_inline)) inline
  #define BITFSM_NEVER_INLINE __attribute__((noinline))
#else
  #define BITFSM_ALWAYS_INLINE
  #define BITFSM_NEVER_INLINE
#endif

// BITFSM_EXPORT marks a function as exported from a library using
// the default ABI.
#if defined(_WIN32) || defined(__CYGWIN__)
  #if defined(__GNUC__)
    #define BITFSM_DLLEXPORT __attribute__((dllexport))
    #define BITFSM_DLLIMPORT __attribute__((dllimport))
  #else
    #define BITFSM_DLLEXPORT __declspec(dllexport)
    #define BITFSM_DLLIMPORT __declspec(dllimport)
  #endif
  #ifdef BITFSM_DLL
    #define BITFSM_EXPORT BITFSM_DLLEXPORT
  #else
    #define BITFSM_EXPORT BITFSM_DLLIMPORT
  #endif
#elif defined(__GNUC__) || defined(__clang__)
  #define BITFSM_EXPORT __attribute__((visibility ("default")))
#else
  #define BITFSM_EXPORT
#endif

// BITFSM_DO_NOT_UNROLL inhibits unrolling of the subsequent loop.
#if defined(__clang__)
  #define BITFSM_DO_NOT_UNROLL #pragma nounroll
#elif defined(__GNUC__)
  #define BITFSM_DO_NOT_UNROLL #pragma GCC unroll 1
#else
  #define BITFSM_DO_NOT_UNROLL
#endif

#endif // BITFSM_OPT_DIRECTIVES_H_
