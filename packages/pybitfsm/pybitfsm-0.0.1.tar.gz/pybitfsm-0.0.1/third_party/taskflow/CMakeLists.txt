add_library(taskflow INTERFACE)
target_include_directories(taskflow INTERFACE .)
target_compile_features(taskflow INTERFACE cxx_std_20)
