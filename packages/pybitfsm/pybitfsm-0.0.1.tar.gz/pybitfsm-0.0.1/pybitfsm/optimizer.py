from collections.abc import Iterable
import ctypes
import dataclasses
import inspect
import io
import sys
import threading
import time
from typing import Callable, Optional

from . import c_api
from .c_api import LIMITS
from . import formatters
from .types import Program, TargetFunction


class _StopToken:
    '''Cancellation token for a superoptimization task. Use `request_stop`
    to gracefully stop a running task.

    Note that the lifetime of the token must exceed the lifetime of any
    tasks using the token. Freeing the token while a task is running --
    whether by calling `free`, allowing the last reference to go out of scope,
    or exiting the associated context manager -- will likely cause the
    process to crash, or result in undefined behavior.

    '''

    def __init__(self):
        self.token = c_api.new_stop_token()

    def request_stop(self):
        if self.token is not None:
            c_api.request_stop(self.token)

    def stop_requested(self):
        if self.token is None:
            return False
        return c_api.stop_requested(self.token)

    def free(self):
        '''Frees the native memory associated with this token.'''
        if self.token is not None:
            c_api.delete_stop_token(self.token)
        self.token = None

    def __del__(self):
        self.free()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        '''Frees the native memory associated with this token.'''
        self.free()


class Case:
    '''An element of the domain of the function being superoptimized.
    The element can be updated to restrict the domain of a function to
    eliminate cases that cannot occur, or to ignore certain bits of the
    result. The `restrict` parameter of `optimize` provides access to
    cases before the superoptimized function is invoked; refining them
    can help the superoptimizer to find a shorter instruction sequence.

    Each Case exposes the corresponding values of the function arguments
    as subscripts. Given the function

    .. code-block: python

       def func(k: int, x: int, y: int) -> int: ...

    the corresponding Cases will expose the function arguments with the
    subscripts `x` and `y`. (`k` is the bit count, and is not considered
    part of the function's domain.) The subscripted values can be modified
    order to change the function's domain.

    For example, if a function takes a pair of masks representing which
    characters in an input string are ``"`` characters, and which are
    ``\\`` characters, then no character can be both a quote and a
    backslash. This constraint on the domain can be represented using the
    following function:

    .. code-block: python

       def restrict_character_masks(c: Case):
           c['quote'] = c['quote'] & ~c['backslash']

    Other functions may only need certain parts of the output. For example,
    consider a function that calculates whether exactly one bit is set in
    the bit-vector `value` for each segment delimited by a trailing bit in
    `end`. In this case, only the last bit of each segment matters, and the
    others can be ignored. This is specified by setting `result_mask`:

    .. code-block: python

       def restrict_range(c: Case):
           c.result_mask = c['end']

    '''

    def __init__(self, parameter_names: list[str]):
        self._args = [0] * len(parameter_names)
        self._parameter_index = {n: i for i, n in enumerate(parameter_names)}
        self.result_mask = -1

    def __getitem__(self, key: str) -> int:
        '''Returns the value of the argument with the parameter name `key`.'''
        return self._args[self._parameter_index[key]]

    def __setitem__(self, key: str, value: int):
        '''Sets the value of the argument for the parameter `key` to `value`.'''
        self._args[self._parameter_index[key]] = value

    def arg(self, name: str) -> int:
        '''Returns the value of the argument with the parameter name `name`.'''
        return self._args[self._parameter_index[name]]

    def set_arg(self, name: str, value: int):
        '''Sets the value of the argument for the parameter `name` to `value`.

        ``c.set_arg(k, v)`` is equivalent to ``c[k] = v``, except that it can
        be used in a lambda expression.

        '''
        self._args[self._parameter_index[name]] = value

    def mask_arg(self, name: str, mask: int):
        '''Clears all bits of the argument for the parameter `name` that are
        not also set in `mask`.

        ``c.mask_arg(k, m)`` is equivalent to ``c[k] &= m``, except that it
        can be used in a lambda expression.

        '''
        self._args[self._parameter_index[name]] &= mask

    def set_result_mask(self, mask: int):
        '''Sets the result mask to `mask`.

        ``c.set_result_mask(m)`` is equivalent to ``c.result_mask = m``, except
        that it can be used in a lambda expression.

        '''
        self.result_mask = mask


# Mapping from user-facing instruction set names to enum values supported by
# the optimizer. See `enum bitfsm_opt_instruction_set` for more information.
_INSTRUCTION_SET_IDS = {
    'full': 0,    # BITFSM_OPT_ALL_ISNS
    'reduced': 1, # BITFSM_OPT_REDUCED_ISNS
}


class _Optimizer:
    # The function being superoptimzed. See `optimize` for more information.
    function: TargetFunction

    # The signature of the function being superoptimized.
    signature: inspect.Signature

    # The number of parameters to the function, excluding the initial parameter
    # containing the number of bits (which isn't passed to the superoptimizer.)
    num_parameters: int

    # The following fields are all copies of the optimizer parameters. See the
    # documentation for `optimize` for more information.
    restrict: Optional[Callable[[Case], None]]
    formatter: Optional[Callable[[Program], str]]
    status_file: Optional[io.TextIOBase]
    instruction_set_id: int  # Name has been translated to the enum value.
    constants: Iterable[int]
    max_carries: int
    max_operations: int  # Internal alias for the `max_instructions` parameter

    # Function that returns a monotonic nanosecond clock. Outside of unit tests,
    # this is always set to `time.monotonic_ns`.
    monotonic_ns: Callable[[], int]

    # Cancellation token for the running superoptimization task. If no such task
    # is running, then `stop_token` is None.
    stop_token: Optional[_StopToken]

    # Exception thrown while running `function`, `restrict`, or rendering the
    # progress bar. If no exception has been thrown, then `thrown` is None.
    thrown: Optional[BaseException]

    def __init__(
            self,
            function: TargetFunction,
            restrict: Optional[Callable[[Case], None]] = None,
            formatter: Optional[Callable[[Program], str]] = formatters.format_python,
            status_file: Optional[io.TextIOBase] = sys.stderr,
            instruction_set: str = 'full',
            constants: Iterable[int] = (0,),
            max_carries: int = 3,
            max_instructions: int = 7,
            monotonic_ns: Callable[[], int] = time.monotonic_ns,
        ):
        if not inspect.isroutine(function):
            raise TypeError('`function` is not a function or bound method')
        signature = inspect.signature(function)
        positional_kinds = (inspect.Parameter.POSITIONAL_ONLY,
                            inspect.Parameter.POSITIONAL_OR_KEYWORD)
        for parameter in signature.parameters.values():
            if parameter.kind not in positional_kinds:
                raise ValueError(
                    '`function` has one or more *args, **kwargs, or keyword-only '
                    f'parameters (hint: check `{parameter.name}`)')
        num_parameters = len(signature.parameters) - 1  # 1st parameter is bit count
        if num_parameters < 1:
            raise ValueError('`function` must have at least two parameters, '
                             'including the bit count')
        if num_parameters > LIMITS.max_parameters:
            raise ValueError(f'`function` has more than {LIMITS.max_parameters + 1} '
                             'parameters, including the bit count')
        self.function = function
        self.signature = signature
        self.num_parameters = num_parameters

        self.restrict = restrict
        self.formatter = formatter

        if status_file is not None:
            if not (isinstance(status_file, io.TextIOBase)
                    and status_file.writable()):
                raise TypeError('`status_file` is not a writable file or stream')
        self.status_file = status_file

        instruction_set_id = _INSTRUCTION_SET_IDS.get(instruction_set)
        if instruction_set_id is None:
            names = ', '.join(f'"{name}"' for name in _INSTRUCTION_SET_IDS)
            raise ValueError(f'`instruction_set` "{instruction_set}" is unknown. '
                             f'Expected one of {names}.')
        self.instruction_set_id = instruction_set_id

        if not isinstance(constants, Iterable):
            raise TypeError('`constants` is not iterable')
        for index, constant in enumerate(constants):
            if not isinstance(constant, int):
                raise TypeError(f'`constants[{index}] = {constant!r}` is not an integer')
        if len(constants) > LIMITS.max_constants:
            raise ValueError(f'length of `constants` exceeds {LIMITS.max_constants}')
        self.constants = constants

        if not isinstance(max_carries, int):
            raise TypeError('`max_carries` must be an integer, not '
                            f'{type(max_carries).__name__}')
        if max_carries < 0:
            raise ValueError('`max_carries` is negative')
        if max_carries > LIMITS.max_carries:
            raise ValueError(f'`max_carries` exceeds {LIMITS.max_carries}')
        self.max_carries = max_carries

        max_operations = max_instructions  # Alias to internal name
        if not isinstance(max_operations, int):
            raise TypeError('`max_instructions` is not an integer')
        if max_operations < 0:
            raise ValueError('`max_instructions` is negative')
        if max_operations > LIMITS.max_operations:
            raise ValueError(f'`max_instructions` exceeds {LIMITS.max_operations}')
        self.max_operations = max_operations

        self.monotonic_ns = monotonic_ns
        self.stop_token = None  # Only set while running
        self.thrown = None

    def assert_running(self):
        if self.stop_token is None:
            raise AssertionError('Optimizer is not running!')

    def handle_exception(self, exc: BaseException):
        self.assert_running()
        if self.thrown is None:
            self.thrown = exc
            self.stop_token.request_stop()

    def wrap_function(self) -> Callable[[c_api.UINT8_POINTER, c_api.UINT8_POINTER], ctypes.c_uint8]:
        '''Combines `self.function` and `self.restrict` into a function that
        is compatible with the superoptimizer's C API.

        '''
        self.assert_running()
        num_bits = 8
        case_ = Case(list(self.signature.parameters)[1:])
        function = self.function
        num_parameters = self.num_parameters
        restrict = self.restrict
        def wrapper(c_args: c_api.UINT8_POINTER, c_mask: c_api.UINT8_POINTER) -> ctypes.c_uint8:
            try:
                args = [c_args[i] for i in range(num_parameters)]
                if restrict is not None:
                    case_._args = args
                    case_.result_mask = -1
                    restrict(case_)
                    args = case_._args
                    for i in range(num_parameters):
                        c_args[i] = args[i]
                    c_mask[0] = case_.result_mask
                return function(num_bits, *args)
            except BaseException as exc:
                self.handle_exception(exc)
                return 0
        return wrapper

    @dataclasses.dataclass
    class ProgressState:
        '''Persistent state maintained between calls to `show_progress`.'''
        operations: int = 0
        fraction: float = 0.0
        start_ns: int = 0
        version: int = 0

    def show_progress(
            self,
            state: ProgressState,
            operations: int,
            fraction: float,
            asm: c_api.AssemblyProgram,
            version: int
        ):
        '''Writes progress information to `self.status_file`.

        :param state: persistent state maintained across progress updates
        :param operations: total number of operations (non-const,
            non-param instructions) in the programs that are currently being
            generated
        :param fraction: fraction of possible programs that have already been
            generated for the current number of operations
        :param asm: best matching program found so far, as pseudo-assembly
            instructions
        :param version: version number of the program in `asm`. The version
            number is incremented whenever a new best match is found.

        '''
        if self.thrown is not None:
            # Avoid printing nonsense programs if the target function
            # throws an exception, leaving the target output all zeros.
            return
        now = self.monotonic_ns()
        if state.version != version:
            state.version = version
            if self.formatter is not None:
                program = Program(self.function, self.signature, asm)
                formatted = self.formatter(program)
                if state.operations > 0:
                    print(file=self.status_file)  # newline after progress bar
                print(f'\n{formatted.strip()}\n', file=self.status_file)
        if state.operations != operations:
            assert operations <= self.max_operations
            state.operations = operations
            state.fraction = fraction
            state.start_ns = now
        bar_width = 25
        bar = ('#' * round(fraction * bar_width)).ljust(bar_width, '.')
        elapsed_ns = now - state.start_ns
        if fraction == 1.0:
            # Avoid showing 'Pending' for the final progress update.
            remaining = 'ETA: 00:00:00'
        elif fraction == state.fraction or fraction == 0 or elapsed_ns == 0:
            remaining = 'ETA: Pending'  # Cannot interpolate
        else:
            remaining_ns = (1 - fraction) * elapsed_ns / (fraction - state.fraction)
            ns_per_second = 1_000_000_000
            hours, seconds = divmod(remaining_ns // ns_per_second, 3600)
            minutes, seconds = divmod(seconds, 60)
            remaining = f'ETA: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}'
        status_width = 74
        status = (f'\rInstructions: {operations}/{self.max_operations}'
                  f'  [{bar}] {100.0 * fraction:5.1f}%'
                  f'  {remaining}')
        if len(status) > status_width:  # Length logic is OK, all chars are ASCII
            status = f'{status[:status_width-3]}...'
        status = status.ljust(status_width)
        print(status, end='', file=self.status_file)

    def progress_callback(
            self,
            state: ProgressState,
            operations: int,
            fraction: float,
            asm: ctypes.POINTER(c_api.AssemblyProgram),
            version: int
        ):
        '''Callback invoked periodically by the superoptimizer to update the
        status and progress information displayed to the user.

        '''
        try:
            self.show_progress(state, operations, fraction, asm.contents, version)
        except BaseException as exc:
            self.handle_exception(exc)

    def make_options(self) -> c_api.Options:
        options = c_api.Options(
            func=c_api.TARGET_FUNCTION(self.wrap_function()),
            progress=ctypes.cast(None, c_api.PROGRESS_CALLBACK),
            progress_data=None,
            instruction_set=self.instruction_set_id,
            constants=(ctypes.c_uint8 * len(self.constants))(*self.constants),
            num_constants=ctypes.c_uint(len(self.constants)),
            num_parameters=self.num_parameters,
            max_carries=self.max_carries,
            max_operations=self.max_operations,
            max_sequential_size=0,
        )
        if self.status_file is not None:
            options.progress = c_api.PROGRESS_CALLBACK(self.progress_callback)
            options.progress_data = ctypes.py_object(self.ProgressState())
        return options

    def run(self) -> Optional[Program]:
        with _StopToken() as stop_token:
            self.stop_token = stop_token
            self.thrown = None
            options = self.make_options()
            asm = c_api.AssemblyProgram()
            result = [None]
            def run_optimizer():
                result[0] = c_api.optimize(ctypes.byref(options),
                                           stop_token.token,
                                           ctypes.byref(asm))
            thread = threading.Thread(target=run_optimizer, name='pybitfsm optimizer')
            try:
                thread.start()
                thread.join()
            except KeyboardInterrupt:
                stop_token.request_stop()
                while True:
                    try:
                        thread.join()
                        break
                    except KeyboardInterrupt:
                        pass
        self.stop_token = None
        if self.status_file is not None:
            print('\n', file=self.status_file)  # New line after progress bar
        if self.thrown is not None:
            raise self.thrown
        if result[0] == c_api.Result.INVALID:
            raise AssertionError("Invalid options passed to c_api.optimize()")
        elif result[0] == c_api.Result.NOT_FOUND or result[0] is None:
            return None
        elif result[0] == c_api.Result.FOUND:
            program = Program(self.function, self.signature, asm)
            return program
        else:
            raise AssertionError(f"Unknown result code: {result[0]}")


def optimize(
        function: TargetFunction,
        restrict: Optional[Callable[[Case], None]] = None,
        formatter: Optional[Callable[[Program], str]] = formatters.format_python,
        status_file: Optional[io.TextIOBase] = sys.stderr,
        instruction_set: str = 'full',
        constants: Iterable[int] = (0,),
        max_carries: int = 3,
        max_instructions: int = 7
    ) -> Optional[Program]:
    '''Searches for a branchless integer program that computes that same
    function as `function`, and returns it. If no such program is found,
    then `None` is returned instead.

    `function` must meet the following preconditions:
    - It must be a Python function that takes a positive bit count `k`
      and between 1 and 3 `k`-bit integers, and returns a `k`-bit result.
    - The `k`-bit result must be computed one bit position at a time,
      proceeding from the low bits of the inputs to the high bits.
    - It must be possible to exhaustively test the function by enumerating
      all combinations of 7-bit integer inputs.

    The resulting program may compute a different function if any of these
    preconditions are violated.

    :param function: function to optimize. It must meet the preconditions
         documented above.
    :param restrict: function that constrains parts of the domain and range
         of the function that need to match. See the documentation for
         :class:`Case` for more information.
    :param formatter: function used to print matching programs to `status_file`
         as they are discovered. Programs are only printed if they
         are considered "better" (e.g. faster) than any program
         printed previously. If `formatter` is `None`, then
         programs are not printed.
    :param status_file: file or stream to use to display matching programs and
         progress information
    :param instruction_set: name of the instruction set to use to generate the
         program. Supported instruction sets are "full" and "reduced"; "full"
         includes all possible instructions, while "reduced" omits instruction
         variants with initial carry-in (e.g. 'x + y + 1') to speed up
         optimization for larger programs.
    :param constants: iterable of potential integer constants to use in the
         program
    :param max_carries: maximum number of stateful instructions (like addition
         or prefix-XOR) to generate in each program
    :param max_instructions: the maximum number of instructions to generate in
         each program

    The example below finds a well-known expression to isolate the
    least-significant set bit:

    >>> from pybitfsm import optimize
    >>> from pybitfsm.formatters import format_python
    >>> def isolate_low_bit(k: int, x: int) -> int:
    ...     for i in range(k):
    ...         mask = 1 << i
    ...         if x & mask:
    ...             return mask
    ...     return 0
    >>> program = optimize(isolate_low_bit, status_file=None)
    >>> print(format_python(program))
    def isolate_low_bit(k: int, x: int) -> int:
        from pybitfsm import bits
        e1 = -x & x
        return bits.truncate(k, e1)
    >>>

    As a more complex example, the code fragment below finds an expression
    that produces 1 bits for all characters in a quoted string, ignoring
    quote characters preceded by an unescaped backslash:

    >>> from pybitfsm import Case, optimize
    >>> def string_mask(k: int, quote: int, backslash: int) -> int:
    ...     escaped = False
    ...     quoted = False
    ...     result = 0
    ...     for i in range(k):
    ...         if escaped:
    ...             escaped = False
    ...         elif (backslash >> i) & 1:
    ...             escaped = True
    ...         elif (quote >> i) & 1:
    ...             quoted = not quoted
    ...         result |= int(quoted) << i
    ...     return result
    >>> def restrict_string_mask(c: Case):
    ...     # A character cannot be both " and \\ at the same time.
    ...     c['quote'] &= ~c['backslash']
    >>> program = optimize(string_mask, restrict=restrict_string_mask,
    ...                    constants=(0x55,), max_instructions=5,
    ...                    status_file=None)
    >>> # (max_instructions=5 avoids slowing down the doctests)
    >>> from pybitfsm.formatters import format_python
    >>> print(format_python(program))
    def string_mask(k: int, quote: int, backslash: int) -> int:
        from pybitfsm import bits
        # Note: 'bits.prefix_xor(k, x)' is 'clmul(x, ~0)'
        e1 = bits.prefix_xor(k, (((backslash ^ 0x55) + 0x55) ^ 0x55) & quote)
        return bits.truncate(k, e1)
    >>>

    In a real implementation, the constant 0x55 must be expanded to an
    appropriate bit width; for example, to process 64 bits at a time it
    would need to be 0x5555555555555555.

    '''

    optimizer = _Optimizer(
        function,
        restrict=restrict,
        formatter=formatter,
        status_file=status_file,
        instruction_set=instruction_set,
        constants=constants,
        max_carries=max_carries,
        max_instructions=max_instructions,
    )
    return optimizer.run()
