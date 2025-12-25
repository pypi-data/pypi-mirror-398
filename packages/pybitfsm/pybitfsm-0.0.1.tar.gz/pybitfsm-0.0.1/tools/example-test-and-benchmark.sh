#!/bin/sh

# Builds and runs tests and benchmarks for the specified example.
# Usage: './tools/example-test-and-benchmark.sh or_scan'

set -eu

toolchain="$1"
example="$2"

if [ "${toolchain}" = "clang" ]; then
  export CC=clang
  export CXX=clang++
elif [ "${toolchain}" = "gcc" ]; then
  export CC=gcc
  export CXX=g++
else
  echo "Unsupported toolchain: \"${toolchain}\"" >&2
  exit 1
fi

build_dir="./build_${toolchain}_release"
cmake -B "${build_dir}" -DCMAKE_BUILD_TYPE=Release -DBENCHMARK_ENABLE_LIBPFM=ON .
CLICOLOR=0 cmake --build "${build_dir}" -j
ctest --test-dir "${build_dir}" -j --output-on-failure
"${build_dir}/examples/${example}/${example}_bench" \
    --benchmark_counters_tabular \
    --benchmark_perf_counters=CYCLES
