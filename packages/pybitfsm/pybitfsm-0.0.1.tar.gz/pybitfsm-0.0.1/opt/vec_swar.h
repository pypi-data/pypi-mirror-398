#ifndef BITFSM_OPT_VEC_SWAR_H
#define BITFSM_OPT_VEC_SWAR_H

#include <cassert>
#include <cstdint>

#include <wyhash.h>

#include "directives.h"

namespace bitfsm_opt {

// Vectors implementing 7-bit SWAR on pairs of 64-bit words.
//
// Based on "Processing with Full-Word Instructions" by Leslie Lamport.
// https://lamport.azurewebsites.net/pubs/multiple-byte.pdf
struct VecSwar {
  // Bit width of each element, including the padding bit.
  static constexpr unsigned kElementBits = 8;

  // Number of elements per 64-bit word.
  static constexpr unsigned kElementsPerWord = 8;

  // Number of elements in each vector.
  static constexpr unsigned kNumElements = 16;

  // Mask for the value bits in the elements.
  static constexpr uint64_t kElementMask = UINT64_C(0x7f7f7f7f7f7f7f7f);

  // A word with the value '1' in each element.
  static constexpr uint64_t kOneBits = UINT64_C(0x0101010101010101);

  std::uint64_t hi;
  std::uint64_t lo;

  BITFSM_ALWAYS_INLINE
  static VecSwar Create(std::uint8_t values[kNumElements]) {
    std::uint64_t hi, lo;
    memcpy(&lo, values, sizeof(lo));
    lo &= kElementMask;
    memcpy(&hi, values + sizeof(lo), sizeof(hi));
    hi &= kElementMask;
    return {hi, lo};
  }

  BITFSM_ALWAYS_INLINE
  static VecSwar Zero() {
    return {0, 0};
  }

  BITFSM_ALWAYS_INLINE
  static VecSwar Not(VecSwar v1) {
    return {.hi = v1.hi ^ kElementMask, .lo = v1.lo ^ kElementMask};
  }

  BITFSM_ALWAYS_INLINE
  static VecSwar And(VecSwar v1, VecSwar v2) {
    return {.hi = v1.hi & v2.hi, .lo = v1.lo & v2.lo};
  }

  BITFSM_ALWAYS_INLINE
  static VecSwar Or(VecSwar v1, VecSwar v2) {
    return {.hi = v1.hi | v2.hi, .lo = v1.lo | v2.lo};
  }

  BITFSM_ALWAYS_INLINE
  static VecSwar Xor(VecSwar v1, VecSwar v2) {
    return {.hi = v1.hi ^ v2.hi, .lo = v1.lo ^ v2.lo};
  }

  BITFSM_ALWAYS_INLINE
  static VecSwar AndNot(VecSwar v1, VecSwar v2) {
    return {.hi = v1.hi & ~v2.hi, .lo = v1.lo & ~v2.lo};
  }

  BITFSM_ALWAYS_INLINE
  static VecSwar Negate(VecSwar v1) {
    return {
      .hi = ((v1.hi ^ kElementMask) + kOneBits) & kElementMask,
      .lo = ((v1.lo ^ kElementMask) + kOneBits) & kElementMask,
    };
  }

  BITFSM_ALWAYS_INLINE
  static std::uint64_t PrefixXor1(std::uint64_t x) {
    x ^= ((x << 1) & kElementMask);
    x ^= ((x << 2) & UINT64_C(0x7c7c7c7c7c7c7c7c));
    x ^= ((x << 4) & UINT64_C(0x7070707070707070));
    return x;
  }

  BITFSM_ALWAYS_INLINE
  static VecSwar PrefixXor(VecSwar v1) {
    return {.hi = PrefixXor1(v1.hi), .lo = PrefixXor1(v1.lo)};
  }

  BITFSM_ALWAYS_INLINE
  static VecSwar Add(VecSwar v1, VecSwar v2) {
    return {
      .hi = (v1.hi + v2.hi) & kElementMask,
      .lo = (v1.lo + v2.lo) & kElementMask,
    };
  }

  BITFSM_ALWAYS_INLINE
  static VecSwar Add1(VecSwar v1, VecSwar v2) {
    return {
      .hi = (v1.hi + v2.hi + kOneBits) & kElementMask,
      .lo = (v1.lo + v2.lo + kOneBits) & kElementMask,
    };
  }

  BITFSM_ALWAYS_INLINE
  static VecSwar Subtract(VecSwar v1, VecSwar v2) {
    return {
      .hi = (v1.hi + (v2.hi ^ kElementMask) + kOneBits) & kElementMask,
      .lo = (v1.lo + (v2.lo ^ kElementMask) + kOneBits) & kElementMask,
    };
  }

  BITFSM_ALWAYS_INLINE
  static VecSwar Subtract1(VecSwar v1, VecSwar v2) {
    return {
      .hi = (v1.hi + (v2.hi ^ kElementMask)) & kElementMask,
      .lo = (v1.lo + (v2.lo ^ kElementMask)) & kElementMask,
    };
  }

  BITFSM_ALWAYS_INLINE
  static VecSwar Broadcast(std::uint8_t value) {
    std::uint64_t x = (kOneBits * value) & kElementMask;
    return {x, x};
  }

  BITFSM_ALWAYS_INLINE
  static int Equal(VecSwar a, VecSwar b) {
    if (a.hi == b.hi) [[unlikely]] {
      return a.lo == b.lo;
    }
    return 0;
  }

  BITFSM_ALWAYS_INLINE
  static std::uint8_t Extract(VecSwar src, unsigned index) {
    std::uint64_t word = index < kElementsPerWord ? src.lo : src.hi;
    unsigned shift = kElementBits * (index % kElementsPerWord);
    return word >> shift;
  }

  BITFSM_ALWAYS_INLINE
  static VecSwar CopyElement(VecSwar dest, unsigned d, VecSwar src,
                             unsigned s) {
    VecSwar result = {.hi = dest.hi, .lo = dest.lo};
    unsigned shift = kElementBits * (d % kElementsPerWord);
    std::uint64_t element = std::uint64_t(Extract(src, s)) << shift;
    std::uint64_t mask = UINT64_C(0xff) << shift;
    if (d < kElementsPerWord) {
      result.lo = (result.lo & ~mask) | element;
    } else {
      result.hi = (result.hi & ~mask) | element;
    }
    return result;
  }

  BITFSM_ALWAYS_INLINE
  static int Mismatch(VecSwar a, VecSwar b) {
    if (a.lo != b.lo) {
      return std::countr_zero(a.lo ^ b.lo) >> 3;
    } else if (a.hi != b.hi) {
      return kElementsPerWord + (std::countr_zero(a.hi ^ b.hi) >> 3);
    }
    return -1;
  }
};

static_assert(sizeof(VecSwar) == VecSwar::kNumElements,
              "VecSwar::kNumElements is incorrect");

bool operator==(const VecSwar a, const VecSwar b) {
  return VecSwar::Equal(a, b);
}

}; // namespace bitfsm_opt

namespace std {
  template<>
  struct hash<bitfsm_opt::VecSwar> {
    std::size_t operator()(const bitfsm_opt::VecSwar v) const {
      return wyhash(&v, sizeof(v), 0, _wyp);
    }
  };
}

#endif // BITFSM_OPT_VEC_SWAR_H
