# Don't build benchmarks when installing pybitfsm.
if(NOT DEFINED SKBUILD_PROJECT_NAME)
  set(BENCHMARK_ENABLE_INSTALL OFF)
  set(BENCHMARK_ENABLE_TESTING OFF)
  add_subdirectory(benchmark)
endif()

add_subdirectory(doctest)
add_subdirectory(taskflow)
add_subdirectory(wyhash)
add_subdirectory(xoshiro256pp)
add_subdirectory(xxhash)
