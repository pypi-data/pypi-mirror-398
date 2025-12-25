add_library(xxhash INTERFACE)
target_include_directories(xxhash INTERFACE .)
target_compile_definitions(xxhash INTERFACE XXH_INLINE_ALL)

# xxhash relies on optimizations to inline indirect calls via a function pointer
# to functions annotated with always_inline. This may fail if the code is built
# in debug mode; we need to use XXH_NO_INLINE_HINTS=1 to work around the issue.
target_compile_definitions(xxhash INTERFACE "$<$<CONFIG:Debug>:XXH_NO_INLINE_HINTS=1>")
