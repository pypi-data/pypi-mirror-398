#ifndef BITFSM_OPT_OPCODE_H_
#define BITFSM_OPT_OPCODE_H_

#include <cstdint>
#include <string>
#include <type_traits>

#include "directives.h"
#include "ops.h"
#include "pack.h"

namespace bitfsm_opt {

// Concept for a struct describing an operation.
template<typename T>
concept Operation = requires(T, unsigned r1, unsigned r2) {
  // kCarry is true if the operation propagates state between bit positions.
  // For example, addition and subtraction carry, as does left shift.
  T::kCarry;
  requires std::is_same_v<decltype(T::kCarry), const bool>;

  // kCommutative is true if the operation's operands may be swapped without
  // affecting the result.
  T::kCommutative;
  requires std::is_same_v<decltype(T::kCommutative), const bool>;

  // kArity is the number of operands expected by the operation.
  // The minimum supported arity is 0, and the maximum is 2.
  requires T::kArity >= 0 && T::kArity <= 2;

  // kCost is a cost assigned to the operation when it appears in a program.
  // Programs with lower total costs are preferred.
  requires T::kCost >= 0 && T::kCost <= UINT8_MAX;

  // kName is a short null-terminated name for the operation, stored in 12 bytes.
  T::kName;
  requires std::is_same_v<decltype(T::kName), const char[12]>;

  // TODO: Figure out how to check a template method in a concept.
  //
  // Apply(v1, v2) returns the result of applying the operation element-wise
  // to the elements in vectors v1 and v2.
  //
  //{ T::Apply(v1, v2) } -> std::same_as<Vec>;
};

// An OpCode binds an operation to a unique numeric code and parameter order.
//
// OpCodes are derived automatically using OpCodes<>. This ensures that
// numeric codes are not reused, and all non-commutative operations have a
// swapped implementation derived automatically.
template<Operation Op, std::uint8_t kCode_, bool kFlipped_>
struct OpCode {
  using Impl = Op;
  static constexpr unsigned kCode = kCode_;
  static constexpr bool kCarry = Op::kCarry;
  static constexpr bool kCommutative = Op::kCommutative;
  static constexpr bool kFlipped = kFlipped_;
  static constexpr unsigned kArity = Op::kArity;
  static constexpr unsigned kCost = Op::kCost;
  static constexpr const char* kName = Op::kName;

  template<typename Vec>
  BITFSM_ALWAYS_INLINE
  static Vec Apply(Vec v1, Vec v2) {
    if constexpr (kFlipped_) {
      return Op::Apply(v2, v1);
    } else {
      return Op::Apply(v1, v2);
    }
  }
};

template<typename ...>
struct OpCodesImpl {};

// Recursive case: transforms a compile-time list of operations into a
// list of op codes, assigning each a unique identifier and generating
// clones of commutative operations with their parameters swapped.
template<typename Op, typename... Acc, typename... Ops>
struct OpCodesImpl<Pack<Acc...>, Pack<Op, Ops...>>
    : OpCodesImpl<
        typename std::conditional<
          (Op::kArity == 2 && !Op::kCommutative),
          Pack<Acc...,
               OpCode<Op, sizeof...(Acc), false>,
               OpCode<Op, sizeof...(Acc) + 1, true>>,
          Pack<Acc..., OpCode<Op, sizeof...(Acc), false>>
        >::type,
        Pack<Ops...>>
{};

// Base case: all operations have been consumed from the pack.
template<typename... Acc>
struct OpCodesImpl<Pack<Acc...>, Pack<>> {
  using type = Pack<Acc...>;
};

// OpCodes<...>::type transforms a list of operation types into a pack
// holding a list of corresponding op codes.
//
// For example,
//
//   OpCodes<Not, And, AndNot>::type> ==
//     Pack<OpCode<Not,    0, false>,
//          OpCode<And,    1, false>,
//          OpCode<AndNot, 2, false>,
//          OpCode<AntNot, 3, true>>
template<typename Operations>
struct OpCodes : OpCodesImpl<Pack<>, Operations> {};

} // namespace bitfsm_opt

#endif // BITFSM_OPT_OPCODE_H_
