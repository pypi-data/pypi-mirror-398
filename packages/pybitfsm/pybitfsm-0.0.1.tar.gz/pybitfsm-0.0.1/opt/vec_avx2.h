#ifndef BITFSM_OPT_VEC_AVX2_H
#define BITFSM_OPT_VEC_AVX2_H

#include <cstdint>

#include <immintrin.h>

#include <wyhash.h>

#include "directives.h"

namespace bitfsm_opt {

struct VecAvx2 {
  static constexpr unsigned kNumElements = 32;

  __m256i v;

  BITFSM_ALWAYS_INLINE
  static VecAvx2 Create(std::uint8_t values[kNumElements]) {
    return {_mm256_loadu_si256((__m256i*) values)};
  }

  BITFSM_ALWAYS_INLINE
  static VecAvx2 Zero() {
    return {_mm256_setzero_si256()};
  }

  BITFSM_ALWAYS_INLINE
  static VecAvx2 Not(VecAvx2 v1) {
    __m256i v = _mm256_xor_si256(v1.v, _mm256_set1_epi32(-1));
    return {v};
  }

  BITFSM_ALWAYS_INLINE
  static VecAvx2 And(VecAvx2 v1, VecAvx2 v2) {
    return {_mm256_and_si256(v1.v, v2.v)};
  }

  BITFSM_ALWAYS_INLINE
  static VecAvx2 Or(VecAvx2 v1, VecAvx2 v2) {
    return {_mm256_or_si256(v1.v, v2.v)};
  }

  BITFSM_ALWAYS_INLINE
  static VecAvx2 Xor(VecAvx2 v1, VecAvx2 v2) {
    return {_mm256_xor_si256(v1.v, v2.v)};
  }

  BITFSM_ALWAYS_INLINE
  static VecAvx2 AndNot(VecAvx2 v1, VecAvx2 v2) {
    return {_mm256_andnot_si256(v2.v, v1.v)}; // AVX2's ANDN is opposite of ours
  }

  BITFSM_ALWAYS_INLINE
  static VecAvx2 Negate(VecAvx2 v1) {
    __m256i v = _mm256_sub_epi8(_mm256_setzero_si256(), v1.v);
    return {v};
  }

  BITFSM_ALWAYS_INLINE
  static VecAvx2 PrefixXor(VecAvx2 v1) {
    __m256i y, x = v1.v;

    // x ^= x << 1;
    x = _mm256_xor_si256(_mm256_add_epi8(x, x), x);

    // y = x << 2; x ^= y;
    y = _mm256_and_si256(_mm256_slli_epi32(x, 2), _mm256_set1_epi32(0xfcfcfcfc));
    x = _mm256_xor_si256(x, y);

    // y = x << 4; x ^= y;
    y = _mm256_and_si256(_mm256_slli_epi32(x, 4), _mm256_set1_epi32(0xf0f0f0f0));
    x = _mm256_xor_si256(x, y);

    return {x};
  }

  BITFSM_ALWAYS_INLINE
  static VecAvx2 Add(VecAvx2 v1, VecAvx2 v2) {
    return {_mm256_add_epi8(v1.v, v2.v)};
  }

  BITFSM_ALWAYS_INLINE
  static VecAvx2 Add1(VecAvx2 v1, VecAvx2 v2) {
    __m256i sum = _mm256_add_epi8(v1.v, v2.v);
    __m256i v = _mm256_sub_epi8(sum, _mm256_set1_epi32(-1));
    return {v};
  }

  BITFSM_ALWAYS_INLINE
  static VecAvx2 Subtract(VecAvx2 v1, VecAvx2 v2) {
    return {_mm256_sub_epi8(v1.v, v2.v)};
  }

  BITFSM_ALWAYS_INLINE
  static VecAvx2 Subtract1(VecAvx2 v1, VecAvx2 v2) {
    __m256i diff = _mm256_sub_epi8(v1.v, v2.v);
    __m256i v = _mm256_add_epi8(diff, _mm256_set1_epi32(-1));
    return {v};
  }

  BITFSM_ALWAYS_INLINE
  static VecAvx2 Broadcast(std::uint8_t value) {
    return {_mm256_set1_epi8(value)};
  }

  BITFSM_ALWAYS_INLINE
  static int Equal(VecAvx2 a, VecAvx2 b) {
    // vtestps is 1 uop on Alder Lake, while vtest is 2 uops.
    __m256 eq = _mm256_castsi256_ps(_mm256_cmpeq_epi32(a.v, b.v));
    __m256 mask = _mm256_castsi256_ps(_mm256_set1_epi32(-1));
    return _mm256_testc_ps(eq, mask);
  }

  BITFSM_ALWAYS_INLINE
  static std::uint8_t Extract(VecAvx2 src, unsigned index) {
    char* from = reinterpret_cast<char*>(&src.v);
    return from[index];
  }

  // TODO: Document this
  BITFSM_ALWAYS_INLINE
  static VecAvx2 CopyElement(VecAvx2 dest, unsigned d, VecAvx2 src, unsigned s) {
    __m256i result = dest.v;
    char* to = reinterpret_cast<char*>(&result);
    char* from = reinterpret_cast<char*>(&src.v);
    to[d] = from[s];
    return {result};
  }

  // TODO: Document this
  BITFSM_ALWAYS_INLINE
  static int Mismatch(VecAvx2 a, VecAvx2 b) {
    unsigned mask = ~_mm256_movemask_epi8(_mm256_cmpeq_epi8(a.v, b.v));
    return mask ? std::countr_zero(mask) : -1;
  }
};

bool operator==(const VecAvx2 a, const VecAvx2 b) {
  return VecAvx2::Equal(a, b);
}

}; // namespace bitfsm_opt

namespace std {
  template<>
  struct hash<bitfsm_opt::VecAvx2> {
    std::size_t operator()(const bitfsm_opt::VecAvx2 v) const {
      return wyhash(&v, sizeof(v), 0, _wyp);
    }
  };
}

#endif // BITFSM_OPT_VEC_AVX2_H
