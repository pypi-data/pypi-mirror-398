#ifndef BITFSM_OPT_C_API_H_
#define BITFSM_OPT_C_API_H_

#include <stdint.h>

#include "directives.h"

// Maximum number of length of a superoptimized program. "Instructions" includes
// both operations like "add", "and", and "xor", as well as placeholders for
// constants and input parameters.
#define BITFSM_OPT_MAX_INSTRUCTIONS 16

#ifdef __cplusplus
extern "C" {
#endif

// An instruction in a superoptimized program.
struct bitfsm_opt_instruction {
  // Mnemonic for the instruction type.
  //
  // The full instruction set is listed below. The symbols 'X' and 'Y'
  // represent the output of prior instructions. They are represented in
  // the `args` array as the zero-based index of the instruction that produced
  // the output being referenced.
  //
  //   const C       constant byte value C
  //   param N       value of the input parameter with index N
  //   not X         inverse of all bits in X
  //   and X, Y      bitwise and of X and Y
  //   or X, Y       bitwise or of X and Y
  //   xor X, Y      bitwise exclusive-or of X and Y
  //   andn X, Y     bitwise and of X with ~Y, i.e. Y with all bits inverted
  //   neg X         twos-complement negation of X, i.e. -X or (~X + 1)
  //   lsl X         X shifted left by 1 bit with the least significant bit
  //                   zeroed, i.e. (X << 1) or (X + X)
  //   lsl1 X        X shifted left by 1 bit with the least significant bit set,
  //                   i.e. ((X << 1) | 1) or (X + X + 1). This is equivalent to
  //                   the instruction "add1 X, X".
  //   add X, Y      sum of X and Y
  //   add1 X, Y     sum of X and Y with the initial carry-in set to 1,
  //                   i.e. (X + Y + 1), or (X - ~Y).
  //   sub X, Y      twos-complement difference of X and Y, i.e. (X - Y)
  //   sub1 X, Y     twos-complement difference of X and Y with the initial
  //                   borrow-in set to 1, i.e. (X - Y - 1) or ~(Y - X).
  //   prefix_xor X  prefix parity of each bit in X. That is,
  //                   each bit Z[i] of the result Z is equal to
  //                   X[i] XOR X[i-1] XOR X[i-2] XOR .. XOR X[0].
  //                 Can be computed by carryless multiplication of X with ~0,
  //                   e.g. with PCLMULLQLQDQ on amd64, or PMULL on arm64.
  const char* name; // TODO: Use char name[16] to avoid exporting pointers.

  // This instruction's operands. Only the first 'num_args' entries are valid.
  //
  // The arguments' interpretation depends on the instruction name:
  //
  // - For "const" instructions, the argument is the constant value.
  // - For "param" instructions, the argument is a zero-based parameter index.
  // - Otherwise, the argument is the index of the instruction that produces
  //   the value to use as the operand.
  unsigned char args[2];

  // Number of operands for this instruction.
  unsigned char num_args;

  // The number of other instructions that use this instruction as an operand.
  // The final instruction always has num_uses == 1, to represent that it is
  // the output from the program.
  unsigned char num_uses;
};

// A program generated via superoptimization.
struct bitfsm_opt_program {
  // Number of instructions in the program.
  unsigned size;

  // List of instructions in the program, in program order.
  //
  // The maximum number of elements in `instructions` can be found
  // using the `max_instructions` field set by bitfsm_opt_get_limits().
  struct bitfsm_opt_instruction instructions[BITFSM_OPT_MAX_INSTRUCTIONS];
};

// The set of instructions that may be used in generated programs.
enum bitfsm_opt_instruction_set {
  // An instruction set that contains:
  // - bitwise operations (AND, OR, XOR, ANDN, and NOT);
  // - basic arithmetic (add, subtract, left-shift, and negate);
  // - prefix-xor, i.e. clmul(x, -1);
  // - extended basic arithmetic and prefix-xor with the initial carry-in,
  //   borrow-in, or xor-in set to 1.
  //
  // This instruction set trades longer optimizer run times for the ability
  // to save one or two NOT instructions on short programs.
  BITFSM_OPT_ALL_ISNS = 0,

  // An instruction set that contains:
  // - bitwise operations (AND, OR, XOR, ANDN, and NOT);
  // - basic arithmetic (add, subtract, left-shift, and negate);
  // - prefix-xor, i.e. clmul(x, -1);
  //
  // This instruction set trades shorter optimizer run times for small
  // missed optimization opportunities on short programs.
  BITFSM_OPT_REDUCED_ISNS = 1,
};

// Configuration and tuning options for the superoptimizer.
struct bitfsm_opt_options {
  // Bitwise function to superoptimize.
  //
  // Each invocation receives `num_parameters` (see below) 8-bit values,
  // plus a pointer to an 8-bit mask. The function should return the expected
  // result, and may set any bits of the mask to zero to indicate that the
  // corresponding bit of the result may be either 0 or 1.
  //
  // The function may modify its arguments. If it does, the modifications will
  // be reflected in the test dataset. This can be used to apply preconditions
  // to the input of the function being superoptimized, e.g. to ensure that
  // both arguments do not have '1' bits in the same bit positions.
  uint8_t (*func)(uint8_t* args, uint8_t* mask);

  // Progress callback. If the callback is non-null, it is called periodically
  // with information about the superoptimizer's progress.
  //
  // The parameters are:
  //
  // - `progress_data`: user data pointer provided in the options. See below.
  // - `level`: length of the programs being explored, as a number of instructions.
  //            The number of instructions excludes constants and parameters.
  // - `frac`: fraction of the programs of length `level` that have been generated.
  // - `program`: best program discovered so far.
  // - `version`: counter incremented whenever a new best program is discovered.
  void (*progress)(void* progress_data, unsigned level, float frac,
                   struct bitfsm_opt_program* program, uint64_t version);

  // User data pointer to pass to the progress callback. May be null.
  void* progress_data;

  // The instruction set to use for the generated program. Must be set to
  // one of the members of 'enum bitfsm_opt_instruction_set'.
  //
  // This option is only consumed by the C API. Users of the C++ API should
  // select the instruction set using the 'Ops' template parameter instead.
  unsigned instruction_set;

  // Array of constants that can be used by the superoptimizer. The number of
  // entries is given by the value of the `num_constants` field, which must be
  // no greater than the value of `max_constants` from `bitfsm_opt_get_limits()`.
  uint8_t const* constants;

  // Number of entries in the 'constants' array.
  // Must not exceed the value of `max_constants` from `bitfsm_opt_get_limits()`.
  unsigned num_constants;

  // Number of parameters received by the function being superoptimized.
  // Must not exceed the value of `max_parameters` from `bitfsm_opt_get_limits()`.
  unsigned num_parameters;

  // The maximum number of carry-generating instructions that can be included
  // in the superoptimized program.
  // Must not exceed the value of `max_carries` from `bitfsm_opt_get_limits()`.
  unsigned max_carries;

  // The maximum number of operations in the superoptimized program.
  // Must not exceed the value of `max_operations` from `bitfsm_opt_get_limits()`.
  unsigned max_operations;

  // Maximum program length to generate serially before switching to parallel
  // generation.
  //
  // Should only be set for testing. Otherwise, should be initialized to 0.
  unsigned max_sequential_size;
};

// Numeric limits for the superoptimizer interfaces.
struct bitfsm_opt_limits {
  // The maximum valid value of `max_carries` in `bitfsm_opt_options`.
  unsigned max_carries;

  // The maximum valid value of `max_constants` in `bitfsm_opt_options`.
  unsigned max_constants;

  // The maximum valid value of `max_parameters` in `bitfsm_opt_options`.
  unsigned max_parameters;

  // The maximum valid value of `max_operations` in `bitfsm_opt_options`.
  unsigned max_operations;

  // The number of elements in the `instructions` array in `bitfsm_opt_program`.
  unsigned max_instructions;
};

// Code representing the result of a call to bitfsm_opt_optimize().
enum bitfsm_opt_result {
  // Found at least one program matching the provided function.
  BITFSM_OPT_FOUND = 0,

  // Did not find any programs matching the provided function.
  BITFSM_OPT_NOT_FOUND = 1,

  // One or more of the provided options were invalid.
  BITFSM_OPT_INVALID = 2,
};

// Thread-safe handle used to cancel a running call to bitfsm_opt_optimize().
struct bitfsm_opt_stop_token;

// TODO: directive.h
// TODO: Windows support?
// TODO: Systems other than Windows.
#define BITFSM_OPT_PUBLIC __attribute__((visibility ("default")))

// Returns numeric limits used by the superoptimizer interfaces.
// See `bitfsm_opt_limits` for more information.
BITFSM_EXPORT
void bitfsm_opt_get_limits(struct bitfsm_opt_limits* limits);

// Allocates a new stop token. Must be freed using bitfsm_opt_delete_stop_token().
// Returns NULL if allocation fails.
BITFSM_EXPORT
struct bitfsm_opt_stop_token* bitfsm_opt_new_stop_token(void);

// Frees a stop token allocated with bitfsm_opt_new_stop_token().
// If `stop_token` is NULL, then no operation is performed.
BITFSM_EXPORT
void bitfsm_opt_delete_stop_token(struct bitfsm_opt_stop_token* stop_token);

// Requests the computation using `token` to stop asynchronously.
// If `stop_token` is NULL, then no operation is performed.
BITFSM_EXPORT
void bitfsm_opt_request_stop(struct bitfsm_opt_stop_token* stop_token);

// Returns non-zero if an asynchronous stop has been requested for `token`,
// or zero if no stop has been requested.
// If `stop_token` is NULL, then the result is zero.
BITFSM_EXPORT
int bitfsm_opt_stop_requested(struct bitfsm_opt_stop_token* stop_token);

// Superoptimizes the input function with the constraints given in `options`,
// storing the best discovered program (if any) in `program`.
//
// A return value of `BITFSM_OPT_FOUND` indicates that a matching program was
// found, while a result of `BITFSM_OPT_NOT_FOUND` means no match was found.
// Any other return value indicates an issue with the input options -- see
// the `bitfsm_opt_result` enumeration for more information.
//
// If `stop_token` is not NULL, then it holds a handle that can be used to
// stop the superoptimizer asynchronously by calling bitfsm_opt_request_stop().
// If an asynchronous stop occurs, then the best program found prior to the
// stop request is returned.
BITFSM_EXPORT
int bitfsm_opt_optimize(struct bitfsm_opt_options* options,
                        struct bitfsm_opt_stop_token* stop_token,
                        struct bitfsm_opt_program* program);

#ifdef __cplusplus
}
#endif

#endif // BITFSM_OPT_C_API_H_
