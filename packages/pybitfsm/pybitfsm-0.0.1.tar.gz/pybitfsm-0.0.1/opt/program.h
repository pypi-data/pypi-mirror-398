#ifndef BITFSM_OPT_PROGRAM_H_
#define BITFSM_OPT_PROGRAM_H_

#include "c_api.h"

namespace bitfsm_opt {

// Alias the interface struct to bitfsm_opt::Program.
using Program = bitfsm_opt_program;

} // namespace bitfsm_opt

inline bool operator==(const bitfsm_opt_program& a, const bitfsm_opt_program& b) {
  using Instruction = bitfsm_opt_instruction;
  if (a.size != b.size) {
    return false;
  }
  for (unsigned i = 0; i < a.size; i++) {
    const Instruction& ai = a.instructions[i];
    const Instruction& bi = b.instructions[i];
    if (std::strcmp(ai.name, bi.name) != 0 ||
        ai.num_args != bi.num_args ||
        std::memcmp(ai.args, bi.args, sizeof(ai.args[0]) * ai.num_args) != 0 ||
        ai.num_uses != bi.num_uses) {
      return false;
    }
  }
  return true;
}

inline std::ostream& operator<<(std::ostream& os, const bitfsm_opt_program& p) {
  using Instruction = bitfsm_opt_instruction;
  std::ios_base::fmtflags flags(os.flags());
  os << std::endl;
  for (unsigned i = 0; i < p.size; i++) {
    const Instruction& isn = p.instructions[i];
    os << "%" << std::dec << i << " = " << isn.name;
    for (unsigned j = 0; j < isn.num_args; j++) {
      unsigned arg = isn.args[j];
      if (std::strcmp(isn.name, "const") == 0) {
        os << " 0x" << std::hex << arg;
      } else if (std::strcmp(isn.name, "param") == 0) {
        os << " " << std::dec << arg;
      } else {
        os << " %" << std::dec << arg;
      }
    }
    os << " [uses=" << std::dec << (unsigned) isn.num_uses << "]";
    os << std::endl;
  }
  os.flags(flags);
  return os;
}

#endif // BITFSM_OPT_PROGRAM_H_
