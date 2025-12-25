#include <cstdint>

#include <stop_token>

#include "c_api.h"
#include "ops.h"
#include "optimize.h"
#include "vec.h"

struct bitfsm_opt_stop_token {
  std::stop_source source;
};

void bitfsm_opt_get_limits(struct bitfsm_opt_limits* limits) {
  limits->max_carries = bitfsm_opt::kMaxCarries;
  limits->max_constants = bitfsm_opt::kMaxConstants;
  limits->max_parameters = bitfsm_opt::kMaxParameters;
  limits->max_operations = bitfsm_opt::kMaxOperations;
  limits->max_instructions = BITFSM_OPT_MAX_INSTRUCTIONS;
}

struct bitfsm_opt_stop_token* bitfsm_opt_new_stop_token(void) {
  return new (std::nothrow) bitfsm_opt_stop_token;
}

void bitfsm_opt_delete_stop_token(struct bitfsm_opt_stop_token* stop_token) {
  delete stop_token;
}

void bitfsm_opt_request_stop(struct bitfsm_opt_stop_token* stop_token) {
  if (stop_token != nullptr) {
    stop_token->source.request_stop();
  }
}

int bitfsm_opt_stop_requested(struct bitfsm_opt_stop_token* stop_token) {
  return stop_token != nullptr && stop_token->source.stop_requested();
}

int bitfsm_opt_optimize(struct bitfsm_opt_options* options,
                        struct bitfsm_opt_stop_token* stop_token,
                        struct bitfsm_opt_program* program) {
  std::stop_token token;
  if (stop_token != nullptr) {
    token = stop_token->source.get_token();
  }
  using namespace bitfsm_opt;
  ResultCode res;
  if (options->instruction_set == BITFSM_OPT_ALL_ISNS) {
    res = Optimize<Vec, StdOperations>(*options, *program, token);
  } else if (options->instruction_set == BITFSM_OPT_REDUCED_ISNS) {
    res = Optimize<Vec, ReducedOperations>(*options, *program, token);
  } else {
    res = ResultCode::kInvalid;
  }
  return static_cast<int>(res);
}
