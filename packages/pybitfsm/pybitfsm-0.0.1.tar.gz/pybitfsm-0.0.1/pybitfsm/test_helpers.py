import ctypes
import inspect
from typing import List, Tuple

from . import c_api
from .types import Program, TargetFunction


def assemble(function: TargetFunction,
             *instructions: Tuple[str, List[int], int]) -> c_api.AssemblyProgram:
    '''Constructs a program from a Python function and a corresponding
    set of instruction mnemonics, represented as tuples.

    Each instruction mnemonic has the form `(name, args, uses)`, e.g.
    `('add', [0, 3], 2)` for an instruction that adds register 0 and register 3,
    and is used by two other instructions.

    '''
    asm = c_api.AssemblyProgram(
        size=len(instructions),
        instructions=c_api.AssemblyProgram.INSTRUCTION_ARRAY(*[
            c_api.Instruction(
                name=ctypes.c_char_p(name),
                args=c_api.Instruction.ARG_ARRAY(*args),
                num_args=len(args),
                num_uses=uses,
            )
            for name, args, uses in instructions
        ])
    )
    return Program(function, inspect.signature(function), asm)
