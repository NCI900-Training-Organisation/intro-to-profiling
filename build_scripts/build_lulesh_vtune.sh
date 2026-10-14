#!/bin/bash
# Build the optimised workshop executable, with debug information.
# Load the workshop compiler, MPI, CMake and Ninja modules before running.
# Keep that same compiler/MPI environment in the Jupyter kernel and batch jobs.
# Run within a compute allocation; BUILD_JOBS must fit that allocation.
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <path-to-LULESH>" >&2
  exit 1
fi

SRCDIR=$(realpath "$1")
BUILDDIR=$SRCDIR/build/vtune
BUILD_JOBS=${BUILD_JOBS:-4}
if ! [[ "$BUILD_JOBS" =~ ^[1-9][0-9]*$ ]]; then
  echo "BUILD_JOBS must be a positive integer within your allocation." >&2
  exit 1
fi
if [ ! -f "$SRCDIR/CMakeLists.txt" ]; then
  echo "No CMakeLists.txt in $SRCDIR" >&2
  exit 1
fi
for tool in cmake ninja mpicxx; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Missing $tool: load the workshop build modules first." >&2
    exit 1
  fi
done

mkdir -p "$BUILDDIR"
cd "$BUILDDIR"
cmake -G Ninja \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DCMAKE_CXX_COMPILER="$(command -v mpicxx)" \
  -DMPI_CXX_COMPILER="$(command -v mpicxx)" \
  -DWITH_MPI=On \
  -DWITH_OPENMP=On \
  -DWITH_SILO=Off \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=On \
  -DCMAKE_CXX_FLAGS="" \
  -DCMAKE_CXX_FLAGS_RELWITHDEBINFO="-O3 -g -DNDEBUG -fno-omit-frame-pointer" \
  "$SRCDIR"
cmake --build . --target lulesh2.0 -- -j "$BUILD_JOBS"
test -x "$BUILDDIR/lulesh2.0"
echo "Built $BUILDDIR/lulesh2.0"
