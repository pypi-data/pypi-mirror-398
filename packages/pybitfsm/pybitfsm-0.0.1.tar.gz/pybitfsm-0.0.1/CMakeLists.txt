cmake_minimum_required(VERSION 3.26)

project(bitfsm VERSION 0.0.1 LANGUAGES C CXX)

set(CMAKE_C_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(CTest)
enable_testing()

add_subdirectory(opt)
add_subdirectory(pybitfsm)
add_subdirectory(third_party)

# Don't build examples for pybitfsm.
if(NOT DEFINED SKBUILD_PROJECT_NAME)
  add_subdirectory(lib)
  add_subdirectory(examples)
endif()
