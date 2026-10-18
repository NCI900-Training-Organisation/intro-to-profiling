Setup the Application
=====================

.. admonition:: Overview
   :class: Overview

   **Participant setup:** 5–10 minutes after the ARE session starts.

   **Objective:** load the prebuilt LULESH application and verify a baseline run.

LULESH (Livermore Unstructured Lagrangian Explicit Shock Hydrodynamics) is a C++
hydrodynamics proxy application with MPI and OpenMP support. For the Intel VTune
workshop, the instructor provides an optimised executable through the private
``lulesh`` module for participants in project ``vp91``.

Participant setup: load the module
----------------------------------

Launch JupyterLab through ARE with **12 CPU cores on one node** and project
``vp91``. In **Advanced options → Modules**, enter:

.. code-block:: text

   lulesh intel-vtune/2024.2.1

Use the VTune version confirmed by the instructor. The ``lulesh`` module should
provide its compatible compiler/Open MPI runtime automatically. If the private
module is not already discoverable, enter the instructor's modulefile directory
in **Module directories**. In **Storage**, include ``scratch/vp91`` and any
additional storage containing the module, executable and source.

The terminal equivalent, before launching a kernel, is:

.. code-block:: bash

   module load lulesh
   module load intel-vtune/2024.2.1
   command -v lulesh2.0 mpirun vtune

Module settings must reach the Python kernel through the ARE launch environment.
Loading a module later in a separate terminal does not update an existing kernel.
Participants do not need to clone or compile LULESH.

The notebook finds ``lulesh2.0`` on ``PATH``. The module should also set
``LULESH_SOURCE`` to the matching, readable source directory. If that variable
is unavailable, function-level profiling can proceed; obtain the source location
from the instructor before source inspection.

Check the supplied application
------------------------------

Use the notebook's environment check and baseline cells. The following terminal
example runs inside the existing ARE allocation:

.. code-block:: bash

   export OMP_NUM_THREADS=1 OMP_DYNAMIC=FALSE
   export OMP_PLACES=cores OMP_PROC_BIND=close
   cd /scratch/vp91/$USER
   mpirun -np 1 --map-by slot:PE=1 --bind-to core \
     lulesh2.0 -s 30 -i 200

Check the program's rank/thread counts, actual iterations, energy/symmetry
output and successful completion. Calibrate the workload and repeat timings as
explained in :doc:`vtune`. LULESH requires a cubic MPI rank count: the core
thread comparison uses one rank with up to twelve OpenMP threads. Exercise 5
compares eight MPI ranks with one thread each at ``-s 30`` against one rank
with eight threads at ``-s 60``. Both configurations have 216,000 elements and
use eight application cores; compare actual iterations and numerical diagnostics.

Each participant writes logs and results to their own
``/scratch/vp91/<username>/vtune-results/`` directory. The shared executable and
matching source are used for reading and execution.

Optional instructor notes: prepare the private module
-----------------------------------------------------

Complete this preparation before the workshop. It is not a participant exercise.
The final installation/modulefile directories are chosen by the instructor.

#. Build with the compiler and Open MPI runtime that the module will load.
   Enable MPI and OpenMP, retain debug symbols, and keep the source revision,
   compile commands and binary hash. Load the chosen compiler, Open MPI, CMake
   and Ninja modules first, then run the optimised build helper:

   .. code-block:: bash

      BUILD_JOBS=12 bash build_scripts/build_lulesh_vtune.sh /path/to/LULESH

   Run it within an appropriate allocation; ``BUILD_JOBS`` must fit that
   allocation. CMake and Ninja are instructor build dependencies.

#. The helper builds ``LULESH/build/vtune/lulesh2.0`` with
   ``-O3 -g -DNDEBUG -fno-omit-frame-pointer`` in the
   ``RelWithDebInfo`` configuration, with MPI and OpenMP enabled. Keep the
   executable unstripped and retain matching readable source. Preserve source
   locations embedded in the debug information where possible, or supply the
   matching source search path to VTune.

#. Optionally build an unoptimised executable for an instructor demonstration
   of how optimisation changes the profile. Use the same source checkout and
   loaded modules:

   .. code-block:: bash

      BUILD_JOBS=12 bash build_scripts/build_lulesh_vtune_o0.sh /path/to/LULESH

   This uses a separate ``LULESH/build/vtune-O0/`` directory and produces
   ``lulesh2.0-O0`` there, alongside CMake's original ``lulesh2.0`` target.
   Its flags are ``-O0 -g -DNDEBUG -fno-omit-frame-pointer``. Both helpers
   explicitly set the compiler flags, enable MPI/OpenMP, disable optional Silo
   output, and use ``RelWithDebInfo`` with the stated optimisation level.
   Assertions remain disabled in both builds, so only optimisation changes.
   Keep ``lulesh2.0`` from the optimised build as the participant default.

#. Publish the executable/source in a location that ``vp91`` participants can
   read, with executable permissions on the binary and directory traversal
   permissions on its parent directories. Participants need no write access to
   the installation. Keep the selected build fixed during the workshop.

#. Make ``module load lulesh`` expose ``lulesh2.0`` on ``PATH``, load the matching
   compiler/MPI runtime dependencies, and set ``LULESH_SOURCE``. For example,
   adapt this Tcl modulefile to the actual paths and dependency versions:

   .. code-block:: tcl

      #%Module1.0
      module-whatis "Prebuilt MPI/OpenMP LULESH for the vp91 VTune workshop"
      module load gcc/10.3.0 openmpi/4.1.7
      set root /path/to/prebuilt/lulesh
      prepend-path PATH [file join $root bin]
      setenv LULESH_SOURCE [file join $root src]

   This example assumes the binary is installed as ``bin/lulesh2.0`` and the
   matching C++ sources are directly under ``src``. Adapt both to the chosen
   layout. If supplying both builds, install the comparison executable as
   ``bin/lulesh2.0-O0``; it uses the same matching source and runtime. A private
   module directory must be on the module search path; it can
   be supplied through ARE's **Module directories** field. Publish the directory
   and storage requirements with the workshop launch settings. See the
   `Environment Modules modulefile reference
   <https://modules.readthedocs.io/en/stable/modulefile.html>`_.

#. Test as a participant in a fresh **12-core, single-node ARE JupyterLab
   session**: module discovery, runtime dependencies, personal result-directory
   creation, the one-thread baseline, twelve-thread Hotspots, and both the
   eight-rank and eight-thread runs in Exercise 5. All profiling exercises use
   software sampling. Verify source attribution and source readability from
   the participant session.

Other profiler builds
---------------------

The repository retains ``build_lulesh_gprof.sh`` and
``build_lulesh_hpctoolkit.sh`` for the corresponding tutorials. They have their
own build requirements. The supplied VTune module is the application for this
workshop; it is not assumed to contain gprof instrumentation.

.. admonition:: Key Points
   :class: hint

   #. Participants use ``module load lulesh`` and profile the supplied executable.
   #. Configure the module in ARE before the kernel starts.
   #. Retain the matching source and record the loaded module/binary identity.
   #. Save each participant's results in their own scratch directory.
