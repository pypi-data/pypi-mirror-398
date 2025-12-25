#ifndef BITFSM_OPT_BITS_H_
#define BITFSM_OPT_BITS_H_

#include <cassert>
#include <climits>
#include <cstdint>

#include <bit>
#include <concepts>

#include "directives.h"

namespace bitfsm_opt {

// Clears the lowest bit of x, returning 0 if x is 0.
template<std::unsigned_integral T>
BITFSM_ALWAYS_INLINE
constexpr T ClearLowBit(T x) {
  return x & (x - 1);
}

// Returns a copy of 'x' with the byte order reversed.
BITFSM_ALWAYS_INLINE
std::uint32_t ReverseBytes(std::uint32_t x) {
#if __cpp_lib_byteswap >= 202110
  return std::byteswap(x); // Requires C++23
#elif defined(__GNUC__) || defined(__clang__)
  return __builtin_bswap32(x);
#elif defined(_MSC_VER)
  return _byteswap_ulong(x);
#else
  static_assert(CHAR_BIT == 8, "Unsupported platform - bytes must be 8 bits");
  return ((x << 24) |
          ((x & 0x0000ff00) << 8) |
          ((x & 0x00ff0000) >> 8) |
          (x >> 24));
#endif
}

// Returns the number of 1 bits in x.
//
// If x is greater than 0xfffe (i.e. if x is not a 16-bit value,
// or if more than 15 bits are set), then the results are undefined.
template<std::unsigned_integral T>
BITFSM_ALWAYS_INLINE
constexpr T PopCount15(T x) {
  assert(x <= 0xfffe);

  // Only use std::popcount() when we can guarantee it lowers to a
  // fast inline code path. We don't want to spill all registers
  // to call __popcountdi2()!

#if (defined(__x86_64__) || defined(_M_X64)) && defined(__POPCNT__)
  return std::popcount(x);
#elif defined(__aarch64__) || defined(_M_ARM64)
  return std::popcount(x);
#else
  // Based on Hacker's Delight, 2nd Edition, page 87.
  std::uint64_t y = x * UINT64_C(0x0008000400020001);
  y = y >> 3;
  y = y & UINT64_C(0x1111111111111111);
  y = y * UINT64_C(0x1111111111111111);
  return y >> 60;
#endif
}

} // namespace bitfsm_opt

#endif // BITFSM_OPT_BITS_H_
