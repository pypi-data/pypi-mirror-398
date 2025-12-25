from collections.abc import Callable
import inspect
from typing import Optional

from . import c_api
from .types import Program


# Prefixes for temporary variables. The first prefix that doesn't
# collide with a parameter name will be chosen -- for example, if
# there is no parameter name matching 'e[[:digit:]]*', then the
# variables in the generated code will be named 'e1', 'e2', etc.
PREFIXES = ('e', 'v', 't', 'm', 'z')


def _get_variable_prefix(program: Program, prefixes: list[str]) -> str:
    '''Returns the first prefix from `prefixes` that is appropriate to
    use as a prefix for temporary variables in the program `program`.

    :param program: program to generate the mapping for
    :param prefixes: candidate strings to use as prefixes for the temporary
        candidate which does not collide with a program parameter is selected.
    :returns: the selected prefix

    '''
    signature = program.signature
    for prefix in prefixes:
        if (prefix not in signature.parameters and
            not any(name.startswith(prefix) and name[len(prefix):].isdigit()
                    for name in signature.parameters)):
            return prefix
    else:
        # This should not happen, so long as there are more (distinct) prefixes
        # than there are function parameters.
        raise ValueError('no unused prefix found')


def _get_instruction_indices(program: Program) -> list[Optional[int]]:
    '''Returns an instruction index mapping, where the value at index 'i' is
    None if the output of 'program.instructions[i]' is unused, or a small
    positive unique identifier for the instruction otherwise.

    '''
    live = 1
    instructions = program.instructions
    indices = [None] * len(instructions)
    for i, isn in enumerate(instructions):
        if isn.num_uses > 0:
            indices[i] = live
            live += 1
    return indices


def _format_instruction_mnemonics(program: Program, indices: list[Optional[int]]) -> list[str]:
    '''Formats `program` into a list of LLVM IR-style pseudo-assembly mnemonics.

    :param program: superoptimized program to format
    :param indices: register index mapping, such that 'indices[i]' provides the
        destination register for the instruction at index 'i'.
        See `_get_instruction_indices`.
    :returns: a list of pseudo-assembly instructions

    '''
    instructions = program.instructions
    align = 1 + int(len(instructions) >= 10)
    mnemonics: list[str] = []
    for i, isn in enumerate(instructions):
        if isn.num_uses == 0:
            continue
        mnemonic = [f'%{indices[i]:<{align}} = {isn.name.decode("ascii")} ']
        if isn.name == b'const':
            mnemonic.append(f'0x{isn.arguments[0]:02x}')
        elif isn.name == b'param':
            mnemonic.append(str(isn.arguments[0]))
        else:
            for j, arg in enumerate(isn.arguments):
                if j > 0:
                    mnemonic.append(', ')
                mnemonic.append(f'%{indices[arg]}')
        mnemonics.append(''.join(mnemonic))
    return mnemonics


def _format_instruction_comments(program: Program, indices: list[Optional[int]]) -> list[str]:
    '''Formats `program` as a list of assembly-style comments.

    :param program: superoptimized program to format
    :param indices: register index mapping, such that 'indices[i]' provides the
        destination register for the instruction at index 'i'.
        See `_get_instruction_indices`.
    :returns: a list of assembly-style comments

    '''

    prefix = _get_variable_prefix(program, PREFIXES)
    instructions = program.instructions
    names = [None] * len(instructions)
    comments: list[str] = []
    for i, isn in enumerate(instructions):
        if isn.num_uses == 0:
            continue
        comment = ['; ']
        if isn.name == b'const':
            names[i] = f'0b{isn.arguments[0]:08b}'
            comment.append(names[i])
        elif isn.name == b'param':
            names[i] = program.get_parameter(isn.arguments[0]).name
            comment.append(names[i])
        else:
            comment.append(f'{prefix}{indices[i]} = ')
            names[i] = f'{prefix}{indices[i]}'
            r1 = isn.arguments[0]
            r2 = isn.arguments[-1]
            if isn.name == b'not':
                comment.append(f'~{names[r1]}')
            elif isn.name == b'and':
                comment.append(f'{names[r1]} & {names[r2]}')
            elif isn.name == b'or':
                comment.append(f'{names[r1]} | {names[r2]}')
            elif isn.name == b'xor':
                comment.append(f'{names[r1]} ^ {names[r2]}')
            elif isn.name == b'andn':
                comment.append(f'{names[r1]} & ~{names[r2]}')
            elif isn.name == b'neg':
                comment.append(f'-{names[r1]}')
            elif isn.name == b'lsl':
                comment.append(f'{names[r1]} << 1, shift-in = 0')
            elif isn.name == b'lsl1':
                comment.append(f'{names[r1]} << 1, shift-in = 1')
            elif isn.name == b'add':
                comment.append(f'{names[r1]} + {names[r2]}, carry-in = 0')
            elif isn.name == b'add1':
                comment.append(f'{names[r1]} + {names[r2]}, carry-in = 1')
            elif isn.name == b'sub':
                comment.append(f'{names[r1]} - {names[r2]}, borrow-in = 0')
            elif isn.name == b'sub1':
                comment.append(f'{names[r1]} - {names[r2]}, borrow-in = 1')
            elif isn.name == b'prefix_xor':
                comment.append(f'clmul({names[r1]}, ~0), xor-in = 0')
            elif isn.name == b'prefix_xor1':
                comment.append(f'clmul({names[r1]}, ~0), xor-in = 1')
            else:
                raise ValueError(f'unknown instruction: {isn.name}')
        comments.append(''.join(comment))
    return comments


def _format_instruction_lines(mnemonics: list[str], comments: list[str]) -> list[str]:
    '''Merges a list of pseudo-assembly mnemonics and comments into a
    list of output lines, with the mnemonics and comments in separate
    columns.

    '''
    # The string length of the mnemonics matches the visual length since the
    # mnemonics contain only ASCII characters.
    padded_mnemonic_len = 3 + max(len(m) for m in mnemonics)
    lines: list[str] = []
    for mnemonic, comment in zip(mnemonics, comments):
        lines.append(mnemonic.ljust(padded_mnemonic_len))
        lines.append(comment)
        lines.append('\n')
    return lines


def format_instructions(program: Program) -> str:
    '''Formats a superoptimized program as a sequence of LLVM-style
    pseudo-instructions and comments.

    '''

    indices = _get_instruction_indices(program)
    mnemonics = _format_instruction_mnemonics(program, indices)
    comments = _format_instruction_comments(program, indices)
    lines = _format_instruction_lines(mnemonics, comments)
    return ''.join(lines)


def _get_expression_names(program: Program, prefix: str) -> list[Optional[str]]:
    '''Returns a mapping from instruction indices to temporary variable
    names to assign the output of the instruction to. If the instruction
    should not be assigned to a temporary, then the mapped name is `None`.

    :param program: program to generate the mapping for
    :param prefix: prefix for temporary variable names, e.g. if `prefix` is 'e'
        then the first variable name will be 'e1'
    :returns: a list containing a mix of temporary variable names and `None`
        values, where `None` means that the corresponding instruction
        does not have an associated temporary.

    '''

    # Assign names to every instruction that is used multiple times,
    # that is a constant or parameter, or that is output from the program.
    instructions = program.instructions
    names = [None] * len(instructions)
    count = 0
    for i, isn in enumerate(instructions):
        if isn.name == b'const':
            names[i] = f'0x{isn.arguments[0]:02x}'
        elif isn.name == b'param':
            names[i] = program.get_parameter(isn.arguments[0]).name
        elif isn.num_uses > 1 or i == len(instructions) - 1:
            count += 1
            names[i] = f'{prefix}{count}'

    return names


class _PythonFormatter:
    '''Formats a superoptimized program as a Python function.'''

    # The instruction types in DO_NOT_PARENTHESIZE are never wrapped
    # in parentheses when converting them to expressions, even when
    # they are nested.
    DO_NOT_PARENTHESIZE = {
        b'const',       # Avoid: (17)
        b'param',       # Avoid: (x)
        b'not',         # Avoid: ~(x) or ~((x + y))
        b'neg',         # Avoid: -(x) or -((x + y))
        b'prefix_xor',  # Avoid: bits.prefix_xor((x))
    }

    def __init__(self, program: Program):
        self.program = program
        self.bits_module_alias = _PythonFormatter.get_bits_module_alias(program)
        self.bit_count_name = next(iter(program.signature.parameters))
        prefix = _get_variable_prefix(program, PREFIXES)
        self.expression_names = _get_expression_names(program, prefix)
        self.fragments = []  # List used for constructing the formatted program.

    @staticmethod
    def get_bits_module_alias(program: Program) -> str:
        '''Returns a name for the 'pybitfsm.bits' module that will not
        collide with any other parameter or variable name in the generated
        code.

        '''
        for alias in ('bits', 'bits_', '_bits', '__bits', 'bits__'):
            if alias not in program.signature.parameters:
                return alias
        else:
            raise AssertionError('Could not find an import alias for pybitfsm.bits')

    def format(self) -> str:
        self.append_signature()
        self.append_imports()
        self.append_notes()
        instructions = self.program.instructions
        for pc, isn in enumerate(instructions):
            is_named = self.expression_names[pc] is not None
            is_predefined = isn.name in (b'const', b'param')
            if is_named and not is_predefined:
                self.append_statement(pc)
        self.append_result(pc)
        return ''.join(self.fragments)

    def append(self, s: str):
        self.fragments.append(s)

    def append_signature(self):
        signature = self.program.signature
        name = self.program.function.__name__
        if name == '<lambda>':
            name = 'function'
        self.append(f'def {name}(')
        for i, parameter in enumerate(signature.parameters.values()):
            if i > 0:
                self.append(', ')
            self.append(parameter.name)
            if parameter.annotation != inspect.Parameter.empty:
                self.append(': ')
                self.append(parameter.annotation.__name__)
        self.append(')')
        if signature.return_annotation != inspect.Signature.empty:
            self.append(f' -> {signature.return_annotation.__name__}')
        self.append(':\n')

    def append_imports(self):
        alias = self.bits_module_alias
        if alias == 'bits':
            self.append('    from pybitfsm import bits\n')
        else:
            self.append(f'    import pybitfsm.bits as {alias}\n')

    def append_notes(self):
        instruction_names = set(i.name for i in self.program.instructions)
        if b'prefix_xor' in instruction_names:
            self.append("    # Note: 'bits.prefix_xor(k, x)' is 'clmul(x, ~0)'\n")
        if b'prefix_xor1' in instruction_names:
            self.append("    # Note: '~bits.prefix_xor(k, x)' is 'clmul(x, ~0)' with the initial xor-in set to 1\n")
        if b'add1' in instruction_names:
            self.append("    # Note: 'x + y + 1' is 'x + y' with the initial carry-in set to 1\n")
        if b'sub1' in instruction_names:
            self.append("    # Note: 'x - y - 1' is 'x - y' with the initial borrow-in set to 1\n")
        if b'lsl1' in instruction_names:
            self.append("    # Note: '(x << 1) | 1' is 'x << 1' with the initial shift-in set to 1\n")

    def append_statement(self, pc: int):
        self.append(f'    {self.expression_names[pc]} = ')
        self.append_expression(pc, nested=False)
        self.append('\n')

    def append_expression(self, pc: int, nested: bool):
        isn = self.program.instructions[pc]
        parenthesize = nested and isn.name not in self.DO_NOT_PARENTHESIZE
        if parenthesize:
            self.append('(')
        if isn.name == b'const':
            self.append(f'0x{isn.arguments[0]:02x}')
        elif isn.name == b'param':
            self.append(parameter_names[isn.arguments[0]])
        elif isn.name == b'not':
            self.append('~')
            self.append_argument(isn.arguments[0])
        elif isn.name == b'and':
            self.append_binary_expression(' & ', isn)
        elif isn.name == b'or':
            self.append_binary_expression(' | ', isn)
        elif isn.name == b'xor':
            self.append_binary_expression(' ^ ', isn)
        elif isn.name == b'andn':
            self.append_binary_expression(' & ~', isn)
        elif isn.name == b'neg':
            self.append('-')
            self.append_argument(isn.arguments[0])
        elif isn.name == b'lsl':
            self.append_argument(isn.arguments[0])
            self.append(' << 1')
        elif isn.name == b'lsl1':
            self.append('(')
            self.append_argument(isn.arguments[0], nested=False)
            self.append(' << 1)')
            self.append(' | 1')
        elif isn.name == b'add':
            self.append_binary_expression(' + ', isn)
        elif isn.name == b'add1':
            self.append_binary_expression(' + ', isn)
            self.append(' + 1')
        elif isn.name == b'sub':
            self.append_binary_expression(' - ', isn)
        elif isn.name == b'sub1':
            self.append_binary_expression(' - ', isn)
            self.append(' - 1')
        elif isn.name.startswith(b'prefix_xor'):
            bits_alias = self.bits_module_alias
            k_name = self.bit_count_name
            if isn.name == b'prefix_xor1':
                self.append('~')
            else:
                assert isn.name == b'prefix_xor'
            self.append(f'{bits_alias}.prefix_xor({k_name}, ')
            self.append_argument(isn.arguments[0], nested=False)
            self.append(')')
        else:
            raise ValueError(f"unknown instruction: {isn.name}")
        if parenthesize:
            self.append(')')

    def append_binary_expression(self, op: str, isn: c_api.Instruction):
        self.append_argument(isn.arguments[0])
        self.append(op)
        self.append_argument(isn.arguments[1])

    def append_argument(self, pc: int, nested: bool = True):
        name = self.expression_names[pc]
        if name is not None:
            self.append(name)
        else:
            self.append_expression(pc, nested)

    def append_result(self, pc: int):
        bits_alias = self.bits_module_alias
        k_name = self.bit_count_name
        result_name = self.expression_names[pc]
        self.append(f'    return {bits_alias}.truncate({k_name}, {result_name})')


def format_python(program: Program) -> str:
    '''Formats a superoptimized program as a Python function.'''
    return _PythonFormatter(program).format()
