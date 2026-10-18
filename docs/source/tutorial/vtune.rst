Intel VTune
===========

.. admonition:: Overview
   :class: Overview

   **Tutorial:** about one hour, after a 5–10 minute module/environment check.

   **Objectives:** establish a baseline, find expensive functions, interpret
   timing metrics, compare thread counts, and compare MPI with OpenMP on the
   same global mesh.

Intel VTune Profiler helps attribute application cost to functions, threads and
hardware behaviour. Use unprofiled elapsed time to measure improvement and a
profile to investigate its cause.

Workshop materials
------------------

The lesson follows the concept/exercise/checkpoint format of the MPI workshop:

* :download:`Jupyter notebook <../../../vtune/vtune_lab.ipynb>` and its companion
  :download:`lab.py <../../../vtune/lab.py>` (keep these in the repository's
  ``vtune/`` directory for the executable exercises).
* :download:`Slides (PDF) <../../slides/NCI_VTune_2026.pdf>`.
* :download:`LaTeX source <../../slides/NCI_VTune_2026.tex>` and
  :download:`NCI logo <../../slides/NCI_logo.png>` (keep these together to compile).

Launch the workshop JupyterLab session through ARE with **12 CPU cores on one
node**. Select the project/storage and workshop modules in the ARE launch form.
Use ``lulesh intel-vtune/2024.2.1`` in the ARE **Modules** field (with the
instructor-confirmed VTune version). Supply the private **Module directories**
setting if needed and mount its storage. The notebook checks the allocation and
profiles the supplied executable inside the existing job. See :doc:`intro` for
module setup and optional instructor build notes.

The notebook and slides explain both software and hardware sampling. **All
notebook profiling exercises use software Hotspots**, including the eight-rank
MPI exercise. Hardware examples below are for reference; the exercises do not
run hardware collections or require a counter-access check.

Prebuilt application and baseline
---------------------------------

Participants use the private ``lulesh`` module provided for ``vp91``:

.. code-block:: bash

   module load lulesh
   module load intel-vtune/2024.2.1
   command -v lulesh2.0 mpirun vtune

Configure these modules before ARE launches the notebook kernel. The notebook
finds ``lulesh2.0`` on ``PATH`` and uses the module's matching Open MPI runtime.
Participants do not compile the application. The module should set
``LULESH_SOURCE`` for source inspection; ask the instructor for that location
if it is absent.

The supplied build enables MPI and OpenMP and retains optimisation and debug
information (``-O3 -g -fno-omit-frame-pointer``). This supports realistic timing
and source attribution; VTune does not need ``-pg``. Keep the same binary for
comparisons and record its hash and loaded modules. Save results under your own
``/scratch/vp91/<username>/vtune-results/`` directory.

.. important::

   LULESH requires a perfect cube of MPI ranks: 1, 8, 27, and so on. Four ranks
   are invalid. ``-s N`` is the mesh side length **per rank**, so the total
   number of elements is ``ranks * N**3``. ``-i K`` caps iterations; record the
   actual count because the simulation can stop sooner.

The notebook uses one rank and compares 1, 2, 4, 6 and 12 OpenMP threads within
the same 12-core ARE allocation. Run each experiment after the previous one ends.
Start with a warm-up, calibrate the workload to several seconds of application
execution, and repeat unprofiled timings three times. Keep the input, build,
rank count and binding policy fixed. Check numerical diagnostics as well as the
exit status. The notebook saves each command, log, timing and environment in a
fresh directory.

Hotspots analysis
-----------------

Software Hotspots is a useful first collection mode. It samples the application
without hardware sampling drivers, although normal process-profiling permissions
are still required. Disable additional performance insights explicitly: they
otherwise collect hardware events even with software sampling selected and can
fail during PMU setup. The following example uses Open MPI mapping options:

.. code-block:: bash

   export OMP_NUM_THREADS=1 OMP_DYNAMIC=FALSE
   export OMP_PLACES=cores OMP_PROC_BIND=close
   mpirun -np 1 --map-by slot:PE=1 --bind-to core \
     vtune -collect hotspots -knob sampling-mode=sw \
     -knob enable-characterization-insights=false \
     -trace-mpi -result-dir /path/to/fresh/result \
     -- lulesh2.0 -s 30 -i 200

Launch VTune **inside** the MPI launcher so it profiles the application ranks.
For Open MPI, ``-trace-mpi`` enables MPI-aware results. The result directory may
have a hostname suffix. Use the exact generated path when reporting:

.. code-block:: bash

   vtune -report summary -result-dir /path/to/result.host
   vtune -report hotspots -group-by function -result-dir /path/to/result.host

A summary describes the collection; the function report identifies expensive
functions. The notebook discovers result paths and retains both reports. Inspect
warnings and confirm that the result contains your application and symbols.
Do not use the collector's complete launch-to-finalisation time as an unprofiled
application baseline.

Interpret the metrics
---------------------

* **Elapsed time:** wall time for the reported collection interval; it need not
  match the interval timed by the application.
* **CPU time:** on-CPU time summed across threads. It can exceed elapsed time.
* **Effective time:** CPU time excluding recognised spin and runtime overhead;
  it does not establish that all work is useful or that memory stalls are absent.
* **Spin time:** recognised active waiting, which consumes CPU time.
* **Overhead time:** recognised parallel-runtime management, not a measurement
  of all profiler overhead.
* **Total thread count:** observed threads, potentially including runtime helpers;
  it is not necessarily simultaneous concurrency or exactly ranks times threads.
* **Paused time:** intervals when collection was paused, not a general measure
  of sleeping or descheduled threads.

Availability depends on analysis type, processor and runtime. An unavailable
metric is not zero. In particular, GCC OpenMP builds may not provide Intel
runtime-specific region and efficiency metrics.

For an illustrative calculation, 24 CPU-seconds over 8 elapsed-seconds means
an average on-CPU concurrency of 3; it does not prove three cores of useful work.
Likewise, 1.63 effectively used physical cores out of 48 detected cores gives
about 3.4% node utilisation. Check the job's allocation before interpreting this
as poor parallelism. Node utilisation and fixed-work speedup/parallel efficiency
are different quantities.

HPC Performance
---------------

Use this analysis to investigate available CPU, memory, floating-point and
parallel-behaviour metrics. It needs supported hardware counters and access
permissions. This is a reference example, outside the notebook exercises.
Preserve the workload and binding when comparing with Hotspots:

.. code-block:: bash

   export OMP_NUM_THREADS=12 OMP_DYNAMIC=FALSE
   export OMP_PLACES=cores OMP_PROC_BIND=close
   mpirun -np 1 --map-by slot:PE=12 --bind-to core \
     vtune -collect hpc-performance -trace-mpi \
     -result-dir /path/to/fresh/hpc \
     -- lulesh2.0 -s 30 -i 200

Report the actual generated directory with ``vtune -report summary``. Relate a
flagged metric to a costly region and a testable hypothesis. Do not assume that
every processor/runtime supports the same metrics.

Memory Access
-------------

This reference example shows a separate Memory Access collection for questions
about data access, with the same OpenMP environment. It is outside the notebook
exercises:

.. code-block:: bash

   mpirun -np 1 --map-by slot:PE=12 --bind-to core \
     vtune -collect memory-access -trace-mpi \
     -result-dir /path/to/fresh/memory \
     -- lulesh2.0 -s 30 -i 200

Examine available cache, bandwidth, memory-stall and NUMA metrics in expensive
regions. Bandwidth measures data transferred per second; latency describes the
wait for an access. Low bandwidth can coexist with significant memory stalls.
A large cache-miss count alone does not prove an end-to-end bottleneck.

The notebook uses software Hotspots throughout, including the eight-rank MPI
collection in Exercise 5. Hardware analyses can be proposed as future
measurements; hardware metrics remain uncollected in the exercises.

GUI analysis
------------

The core ARE JupyterLab exercise uses saved text reports and source inspection.
For optional GUI exploration in a configured desktop/VNC environment, open the
actual result directory:

.. code-block:: bash

   vtune-gui /path/to/result.host

Follow Summary, Bottom-up, Caller/Callee, Source/Assembly and Timeline. Add the
matching source search path when needed. Without GUI access, use the saved text
reports and inspect the source function directly. Results can also be copied
with the matching binary/source to a compatible local VTune installation.

Exercises and key points
------------------------

The notebook supplies five stops: baseline, Hotspots, interpretation, a
thread-count experiment, and an MPI/OpenMP comparison. Exercise 5 first profiles
eight MPI ranks with one thread each, then compares that configuration with
one rank using eight OpenMP threads. The default sizes are ``-s 30`` per MPI
rank and ``-s 60`` for the single rank, giving 216,000 elements and eight
application cores in both cases.

Warm up both configurations, alternate three unprofiled timing repetitions,
and compare median launcher elapsed times and their ranges. Check actual
iteration counts, numerical diagnostics and binding. Compare the two software
Hotspots profiles to investigate the difference. The ratio of MPI to OpenMP
median time compares two eight-core configurations; it is not parallel
efficiency relative to one core. Decomposition changes boundaries, memory
layout and rank-dependent region work, so the difference does not isolate
communication overhead.

.. admonition:: Key Points
   :class: hint

   #. Time a correct, representative optimised application before profiling.
   #. Record workload, ranks, threads, binding, environment and result paths.
   #. Start with Hotspots and follow function cost back to its callers/source.
   #. Read metric units, denominators and collection scope before interpreting.
   #. Use hardware analyses to test a specific explanation when supported.
   #. Validate numerical behaviour and repeat unprofiled timings after a change.

References
----------

* `LLNL LULESH <https://github.com/LLNL/LULESH>`_.
* `Intel VTune User Guide (2024.2)
  <https://cdrdv2-public.intel.com/824400/vtune-profiler_user-guide_2024.2-766319-824400.pdf>`_.
* `Intel MPI profiling cookbook
  <https://www.intel.com/content/www/us/en/docs/vtune-profiler/cookbook/2024-0/profiling-mpi-applications.html>`_.
* `Intel CPU metric definitions
  <https://www.intel.com/content/www/us/en/docs/vtune-profiler/user-guide/2023-1/cpu-metrics-reference.html>`_.
* `Intel collection pauses
  <https://www.intel.com/content/www/us/en/docs/vtune-profiler/user-guide/2024-0/problem-unexpected-paused-time.html>`_.
