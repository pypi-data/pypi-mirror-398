#ifndef BITFSM_OPT_OPS_H_
#define BITFSM_OPT_OPS_H_

#include "directives.h"
#include "pack.h"

namespace bitfsm_opt {

// All structs declared in this file satisfy the Operation concept from opcode.h.

struct Variable {
  static constexpr bool kCarry = false;
  static constexpr bool kCommutative = false;
  static constexpr unsigned kArity = 0;
  static constexpr unsigned kCost = 0;
  static constexpr char kName[12] = "var";

  template<typename Vec>
  BITFSM_ALWAYS_INLINE
  static Vec Apply(Vec v1, [[maybe_unused]] Vec v2) {
    // The arguments to a variable op are the variable itself.
    return v1;
  }
};

struct Zero {
  static constexpr bool kCarry = false;
  static constexpr bool kCommutative = false;
  static constexpr unsigned kArity = 0;
  static constexpr unsigned kCost = 0;
  static constexpr char kName[12] = "zero";

  template<typename Vec>
  BITFSM_ALWAYS_INLINE
  static Vec Apply([[maybe_unused]] Vec v1, [[maybe_unused]] Vec v2) {
    return Vec::Zero();
  }
};

struct Not {
  static constexpr bool kCarry = false;
  static constexpr bool kCommutative = false;
  static constexpr unsigned kArity = 1;
  static constexpr unsigned kCost = 1;
  static constexpr char kName[12] = "not";

  template<typename Vec>
  BITFSM_ALWAYS_INLINE
  static Vec Apply(Vec v1, [[maybe_unused]] Vec v2) {
    return Vec::Not(v1);
  }
};

struct And {
  static constexpr bool kCarry = false;
  static constexpr bool kCommutative = true;
  static constexpr unsigned kArity = 2;
  static constexpr unsigned kCost = 1;
  static constexpr char kName[12] = "and";

  template<typename Vec>
  BITFSM_ALWAYS_INLINE
  static Vec Apply(Vec v1, Vec v2) {
    return Vec::And(v1, v2);
  }
};

struct Or {
  static constexpr bool kCarry = false;
  static constexpr bool kCommutative = true;
  static constexpr unsigned kArity = 2;
  static constexpr unsigned kCost = 1;
  static constexpr char kName[12] = "or";

  template<typename Vec>
  BITFSM_ALWAYS_INLINE
  static Vec Apply(Vec v1, Vec v2) {
    return Vec::Or(v1, v2);
  }
};

struct Xor {
  static constexpr bool kCarry = false;
  static constexpr bool kCommutative = true;
  static constexpr unsigned kArity = 2;
  static constexpr unsigned kCost = 1;
  static constexpr char kName[12] = "xor";

  template<typename Vec>
  BITFSM_ALWAYS_INLINE
  static Vec Apply(Vec v1, Vec v2) {
    return Vec::Xor(v1, v2);
  }
};

struct AndNot {
  static constexpr bool kCarry = false;
  static constexpr bool kCommutative = false;
  static constexpr unsigned kArity = 2;
  static constexpr unsigned kCost = 1;
  static constexpr char kName[12] = "andn";

  template<typename Vec>
  BITFSM_ALWAYS_INLINE
  static Vec Apply(Vec v1, Vec v2) {
    return Vec::AndNot(v1, v2);
  }
};

struct Negate {
  static constexpr bool kCarry = true;
  static constexpr bool kCommutative = false;
  static constexpr unsigned kArity = 1;
  static constexpr unsigned kCost = 3;
  static constexpr char kName[12] = "neg";

  template<typename Vec>
  BITFSM_ALWAYS_INLINE
  static Vec Apply(Vec v1, [[maybe_unused]] Vec v2) {
    return Vec::Negate(v1);
  }
};

// x << 1
struct LeftShift {
  static constexpr bool kCarry = true;
  static constexpr bool kCommutative = false;
  static constexpr unsigned kArity = 1;
  static constexpr unsigned kCost = 3;
  static constexpr char kName[12] = "lsl";

  template<typename Vec>
  BITFSM_ALWAYS_INLINE
  static Vec Apply(Vec v1, [[maybe_unused]] Vec v2) {
    return Vec::Add(v1, v1); // (v1 << 1) == (v1 * 2) == (v1 + v1)
  }
};

// (x << 1) | 1
struct LeftShift1 {
  static constexpr bool kCarry = true;
  static constexpr bool kCommutative = false;
  static constexpr unsigned kArity = 1;
  static constexpr unsigned kCost = 3;
  static constexpr char kName[12] = "lsl1";

  template<typename Vec>
  BITFSM_ALWAYS_INLINE
  static Vec Apply(Vec v1, [[maybe_unused]] Vec v2) {
    return Vec::Add1(v1, v1); // (v1 << 1) | 1 == v1 + v1 + 1
  }
};

struct PrefixXor {
  static constexpr bool kCarry = true;
  static constexpr bool kCommutative = false;
  static constexpr unsigned kArity = 1;
  static constexpr unsigned kCost = 8;
  static constexpr char kName[12] = "prefix_xor";

  template<typename Vec>
  BITFSM_ALWAYS_INLINE
  static Vec Apply(Vec v1, [[maybe_unused]] Vec v2) {
    return Vec::PrefixXor(v1);
  }
};

struct PrefixXor1 {
  static constexpr bool kCarry = true;
  static constexpr bool kCommutative = false;
  static constexpr unsigned kArity = 1;
  static constexpr unsigned kCost = 8;
  static constexpr char kName[12] = "prefix_xor1";

  template<typename Vec>
  BITFSM_ALWAYS_INLINE
  static Vec Apply(Vec v1, [[maybe_unused]] Vec v2) {
    return Vec::Not(Vec::PrefixXor(v1));
  }
};

struct Add {
  static constexpr bool kCarry = true;
  static constexpr bool kCommutative = true;
  static constexpr unsigned kArity = 2;
  static constexpr unsigned kCost = 3;
  static constexpr char kName[12] = "add";

  template<typename Vec>
  BITFSM_ALWAYS_INLINE
  static Vec Apply(Vec v1, Vec v2) {
    return Vec::Add(v1, v2);
  }
};

struct Add1 {
  static constexpr bool kCarry = true;
  static constexpr bool kCommutative = true;
  static constexpr unsigned kArity = 2;
  static constexpr unsigned kCost = 3;
  static constexpr char kName[12] = "add1";

  template<typename Vec>
  BITFSM_ALWAYS_INLINE
  static Vec Apply(Vec v1, Vec v2) {
    return Vec::Add1(v1, v2);
  }
};

struct Subtract {
  static constexpr bool kCarry = true;
  static constexpr bool kCommutative = false;
  static constexpr unsigned kArity = 2;
  static constexpr unsigned kCost = 3;
  static constexpr char kName[12] = "sub";

  template<typename Vec>
  BITFSM_ALWAYS_INLINE
  static Vec Apply(Vec v1, Vec v2) {
    return Vec::Subtract(v1, v2);
  }
};

struct Subtract1 {
  static constexpr bool kCarry = true;
  static constexpr bool kCommutative = false;
  static constexpr unsigned kArity = 2;
  static constexpr unsigned kCost = 3;
  static constexpr char kName[12] = "sub1";

  template<typename Vec>
  BITFSM_ALWAYS_INLINE
  static Vec Apply(Vec v1, Vec v2) {
    return Vec::Subtract1(v1, v2);
  }
};

// The set of all standard bitwise operations.
using StdOperations = Pack<
  Variable,
  Zero,
  Not,
  And,
  Or,
  Xor,
  AndNot,
  Negate,
  LeftShift,
  LeftShift1,
  PrefixXor,
  PrefixXor1,
  Add,
  Add1,
  Subtract,
  Subtract1
  >;

// Standard bitwise operations, without fused negation operations.
using ReducedOperations = Pack<
  Variable,
  Zero,
  Not,
  And,
  Or,
  Xor,
  AndNot,
  Negate,
  LeftShift,
  PrefixXor,
  Add,
  Subtract
  >;

} // namespace bitfsm_opt

#endif // BITFSM_OPT_OPS_H_
