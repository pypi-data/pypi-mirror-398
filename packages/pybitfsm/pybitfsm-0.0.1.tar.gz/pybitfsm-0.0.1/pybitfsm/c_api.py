'''Python bindings for libbitfsmopt, the bit-FSM superoptimizer.

See bitfsm/opt/c_api.h for details on the structures and functions
bound in this module.

'''

import ctypes
import os
import pathlib


# PYBITFSM_LIBRARY_PATH is exported when running under cmake
_LIBRARY_PATH = os.environ.get('PYBITFSM_LIBRARY_PATH')
if _LIBRARY_PATH is None:
    from . import libname
    _LIBRARY_PATH = pathlib.Path(__file__).parent / libname.NAME

_libbitfsmopt = ctypes.cdll.LoadLibrary(_LIBRARY_PATH)


class Limits(ctypes.Structure):
    '''struct bitfsm_opt_limits'''
    _fields_ = [
        ('max_carries', ctypes.c_uint),
        ('max_constants', ctypes.c_uint),
        ('max_parameters', ctypes.c_uint),
        ('max_operations', ctypes.c_uint),
        ('max_instructions', ctypes.c_uint),
    ]


# We need to access get_limits() early to access `max_instructions`.
#
# Otherwise, we would need to hardcode the size of the instructions
# array in the bitfsm_opt_program struct.
get_limits = _libbitfsmopt.bitfsm_opt_get_limits
get_limits.argtypes = [ctypes.POINTER(Limits)]
get_limits.restype = None

LIMITS = Limits()
get_limits(ctypes.byref(LIMITS))



class Instruction(ctypes.Structure):
    '''struct bitfsm_opt_instruction'''
    ARG_ARRAY = ctypes.c_ubyte * 2
    _fields_ = [
        ('name', ctypes.c_char_p),
        ('args', ARG_ARRAY),
        ('num_args', ctypes.c_ubyte),
        ('num_uses', ctypes.c_ubyte),
    ]


class AssemblyProgram(ctypes.Structure):
    '''struct bitfsm_opt_program'''
    INSTRUCTION_ARRAY = Instruction * LIMITS.max_instructions
    _fields_ = [
        ('size', ctypes.c_uint),
        ('instructions', INSTRUCTION_ARRAY)
    ]


UINT8_POINTER = ctypes.POINTER(ctypes.c_uint8)
TARGET_FUNCTION = ctypes.CFUNCTYPE(ctypes.c_uint8, UINT8_POINTER, UINT8_POINTER)
PROGRESS_CALLBACK = ctypes.CFUNCTYPE(
    None,
    ctypes.py_object,
    ctypes.c_uint,
    ctypes.c_float,
    ctypes.POINTER(AssemblyProgram),
    ctypes.c_uint64,
)


class Options(ctypes.Structure):
    '''struct bitfsm_opt_options'''
    _fields_ = [
        ('func', TARGET_FUNCTION),
        ('progress', PROGRESS_CALLBACK),
        ('progress_data', ctypes.py_object),
        ('instruction_set', ctypes.c_uint),
        ('constants', UINT8_POINTER),
        ('num_constants', ctypes.c_uint),
        ('num_parameters', ctypes.c_uint),
        ('max_carries', ctypes.c_uint),
        ('max_operations', ctypes.c_uint),
        ('max_sequential_size', ctypes.c_uint),
    ]


class Result:
    '''Return values from bitfsm_opt_optimize()'''
    FOUND = 0
    NOT_FOUND = 1
    INVALID = 2


new_stop_token = _libbitfsmopt.bitfsm_opt_new_stop_token
new_stop_token.argtypes = []
new_stop_token.restype = ctypes.c_void_p

delete_stop_token = _libbitfsmopt.bitfsm_opt_delete_stop_token
delete_stop_token.argtypes = [ctypes.c_void_p]
delete_stop_token.restype = None

request_stop = _libbitfsmopt.bitfsm_opt_request_stop
request_stop.argtypes = [ctypes.c_void_p]
request_stop.restype = None

stop_requested = _libbitfsmopt.bitfsm_opt_stop_requested
stop_requested.argtypes = [ctypes.c_void_p]
stop_requested.restype = ctypes.c_int

optimize = _libbitfsmopt.bitfsm_opt_optimize
optimize.argtypes = [
    ctypes.POINTER(Options),
    ctypes.c_void_p,
    ctypes.POINTER(AssemblyProgram),
]
optimize.restype = ctypes.c_int
