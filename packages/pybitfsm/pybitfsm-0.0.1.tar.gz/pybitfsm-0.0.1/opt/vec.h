#ifndef BITFSM_OPT_VEC_H_
#define BITFSM_OPT_VEC_H_

#if defined(BITFSM_OPT_USE_AVX2) || defined(BITFSM_OPT_USE_SWAR)
  // Nothing to do, we have selected the implementation manually.
#else
  #define BITFSM_OPT_USE_SWAR
#endif

#if defined(BITFSM_OPT_USE_AVX2)
  #include "vec_avx2.h"
  namespace bitfsm_opt {
    using Vec = bitfsm_opt::VecAvx2;
  }
#else
  #include "vec_swar.h"
  namespace bitfsm_opt {
    using Vec = bitfsm_opt::VecSwar;
  }
#endif

#endif // BITFSM_OPT_VEC_H_
