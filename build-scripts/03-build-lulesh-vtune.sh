#!/bin/bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <path-to-LULESH>"
  exit 1
fi

# -------------------------------
# 0. Input arguments
# -------------------------------
SRCDIR=$(realpath "$1")
BUILDDIR=$SRCDIR/build/vtune
INSTALLDIR=$BUILDDIR/install

# -------------------------------
# 1. Load required modules
# -------------------------------
module purge
module load gcc/10.3.0
module load openmpi/4.1.7
module load cuda/12.9.0
module load papi/7.1.0
module load intel-mkl/2024.2.1
module load intel-vtune/2024.2.1
module load cmake/3.8.2

# -------------------------------
# 2. Set compilers to MPI wrappers
# -------------------------------
export CC=mpicc
export CXX=mpicxx
export FC=mpif90

# -------------------------------
# 3. Set library prefixes
# -------------------------------
export CUDA_TOOLKIT_ROOT_DIR=/apps/cuda/12.9.0
export CUPTI_PREFIX=/apps/cuda/12.9.0/extras/CUPTI
export MKLROOT=/apps/intel-tools/intel-mkl/2024.2.1
export PAPI_PREFIX=/apps/papi/7.1.0
export ITT_PREFIX=/apps/intel-tools/intel-vtune/2024.2.1

# -------------------------------
# 4. Adjust library paths
# -------------------------------
export PATH=$CUDA_TOOLKIT_ROOT_DIR/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_TOOLKIT_ROOT_DIR/lib64:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=$PAPI_PREFIX/lib:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=$MKLROOT/lib/intel64:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=$CUPTI_PREFIX/lib64:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=$ITT_PREFIX/lib64:$LD_LIBRARY_PATH

# -------------------------------
# 5. Create build directory
# -------------------------------
mkdir -p "$BUILDDIR"
cd "$BUILDDIR"

# -------------------------------
# 6. Run CMake configure
# -------------------------------
cmake -G Ninja \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DMPI_CXX_COMPILER="$(which mpicxx)" \
  -DWITH_MPI=On \
  -DWITH_OPENMP=On \
  -DCMAKE_INSTALL_PREFIX="$INSTALLDIR" \
  -DCMAKE_CXX_FLAGS="-g -O3 -fno-omit-frame-pointer" \
  "$SRCDIR"

# -------------------------------
# 7. Build & install
# -------------------------------
ninja -j "$(nproc)"
#ninja install
