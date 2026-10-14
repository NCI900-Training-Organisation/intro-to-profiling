#!/bin/bash
# Build the optional unoptimised comparison executable, with debug information.
# Load the same compiler, Open MPI, CMake and Ninja modules as for the O3 build.
# Run within a compute allocation; BUILD_JOBS must fit that allocation.
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <path-to-LULESH>" >&2
  exit 1
fi

SRCDIR=$(realpath "$1")
BUILDDIR=$SRCDIR/build/vtune-O0
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
# Keep the configuration and all other flags identical to the O3 build.
# RelWithDebInfo is explicitly overridden below to use -O0. NDEBUG stays set
# so the comparison changes optimisation without adding assertion checks.
cmake -G Ninja \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DCMAKE_CXX_COMPILER="$(command -v mpicxx)" \
  -DMPI_CXX_COMPILER="$(command -v mpicxx)" \
  -DWITH_MPI=On \
  -DWITH_OPENMP=On \
  -DWITH_SILO=Off \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=On \
  -DCMAKE_CXX_FLAGS="" \
  -DCMAKE_CXX_FLAGS_RELWITHDEBINFO="-O0 -g -DNDEBUG -fno-omit-frame-pointer" \
  "$SRCDIR"
cmake --build . --target lulesh2.0 -- -j "$BUILD_JOBS"
test -x "$BUILDDIR/lulesh2.0"
# CMake's target is named lulesh2.0. Retain it for rebuilds and give the
# deployable copy a distinct name so both variants can share a module's bin/.
cp -- "$BUILDDIR/lulesh2.0" "$BUILDDIR/lulesh2.0-O0"
echo "Built $BUILDDIR/lulesh2.0-O0"
