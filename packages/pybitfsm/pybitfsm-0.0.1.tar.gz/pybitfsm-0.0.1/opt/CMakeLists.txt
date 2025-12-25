include(CheckCXXCompilerFlag)
include(CheckCXXSourceCompiles)

set(BITFSM_VECTOR "" CACHE STRING
   "Vector implementation, e.g. 'AVX2' or 'SWAR'")

set(BITFSM_ENABLE_EXCEPTIONS ON CACHE BOOL
    "Enable/disable C++ exceptions. The standard library must be compiled to match.")

if(NOT BITFSM_VECTOR STREQUAL "")
  add_compile_definitions("BITFSM_OPT_USE_${BITFSM_VECTOR}")
endif()

set(CMAKE_CXX_VISIBILITY_PRESET hidden)

check_cxx_source_compiles("#include <stop_token>\nstd::stop_token s;\nint main() {return 0;}\n"
                          HAVE_STD_STOP_TOKEN)
if(NOT HAVE_STD_STOP_TOKEN)
  # libc++ < 20 hides std::stop_token by default
  check_cxx_compiler_flag(-fexperimental-library COMPILER_SUPPORTS_EXPERIMENTAL_LIBRARY)
  if (COMPILER_SUPPORTS_EXPERIMENTAL_LIBRARY)
    add_compile_options(-fexperimental-library)
  endif()
endif()

if(CMAKE_CXX_COMPILER_FRONTEND_VARIANT STREQUAL "GNU")
  add_compile_options(-Wall -Wextra -pedantic)
  add_compile_options("$<$<CONFIG:Debug>:-Og;-fno-omit-frame-pointer;-fsanitize=undefined>")
  add_link_options("$<$<CONFIG:Debug>:-fsanitize=undefined>")
elseif(MSVC)
  set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
  add_compile_options(/W3)
endif()

if(NOT BITFSM_ENABLE_EXCEPTIONS)
  add_compile_definitions("TF_DISABLE_EXCEPTION_HANDLING")
  if(CMAKE_CXX_COMPILER_FRONTEND_VARIANT STREQUAL "GNU")
    add_compile_options(-fno-exceptions -fno-rtti)
  elseif(MSVC)
    add_compile_options(/EHs-c- /D_HAS_EXCEPTIONS=0 /GR-)
  else()
    message(FATAL_ERROR "Target does not support disabling exceptions.")
  endif()
endif()

link_libraries(
  doctest
  taskflow
  wyhash
  xxhash
  xoshiro256pp
)

add_library(bitfsmopt SHARED c_api.cc)
target_compile_definitions(bitfsmopt PRIVATE BITFSM_DLL)

if(NOT DEFINED SKBUILD_PROJECT_NAME)
  add_executable(bits_test test_main.cc bits_test.cc)
  add_test(NAME opt.bits_test COMMAND $<TARGET_FILE:bits_test> --no-colors)

  add_executable(optimize_test test_main.cc optimize_test.cc)
  add_test(NAME opt.optimize_test COMMAND $<TARGET_FILE:optimize_test> --no-colors)
endif()
