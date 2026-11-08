GNU gprof
=========

.. admonition:: Overview
   :class: Overview

   **Tutorial:** 45 minutes, after a 5–10 minute ARE/module check.

   **Objectives:** collect a profile, distinguish call counts from sampled and
   inferred times, interpret flat profiles and call graphs, measure profiling
   overhead, and assess repeatability.

Workshop materials
------------------

* :download:`Jupyter notebook <../../../gprof/gprof_lab.ipynb>` and companion
  :download:`gprof_lab.py <../../../gprof/gprof_lab.py>` and
  :download:`rank_run.py <../../../gprof/rank_run.py>` (keep together).
* :download:`Slides (PDF) <../../../gprof/slides/NCI_Gprof_2026.pdf>` and
  :download:`LaTeX source <../../../gprof/slides/NCI_Gprof_2026.tex>` with the
  :download:`NCI logo <../../../gprof/slides/NCI_logo.png>`.
* :download:`Instructor setup <../../../gprof/README.md>` and
  :download:`private module template <../../../gprof/modulefiles/lulesh-gprof>`.

The lesson uses classic GNU gprof, which is distinct from gprofng. Participants
use prebuilt LULESH and follow the MPI workshop's concept, prediction, exercise
and checkpoint format. All numerical illustrations are examples, not captured
Gadi measurements.

ARE and the private module
--------------------------

Submit ARE JupyterLab with **12 CPU cores on one node**, project ``vp91``, and
storage ``gdata/vp91+scratch/vp91``. Under advanced options, set **Module
directories** to ``/g/data/vp91/privatemodules`` and **Modules** to
``lulesh-gprof``. The instructor must prepare and verify this proposed module
before the workshop. Use the instructor's path if the module directory differs.

The terminal equivalent is:

.. code-block:: bash

   module use /g/data/vp91/privatemodules
   module load lulesh-gprof
   command -v lulesh2.0-gprof-baseline lulesh2.0-gprof mpirun gprof

Configure modules before the kernel starts. A module loaded in another terminal
cannot update the existing Python process. Run within the ARE allocation; no
additional batch or interactive job is submitted by the notebook. Save profiles
under ``/scratch/vp91/<username>/gprof-results/``.

A matched build pair
--------------------

The instructor helper ``build_scripts/build_lulesh_gprof.sh`` creates two
optimised builds from the same source and GCC/Open MPI environment:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Executable
     - Purpose
   * - ``lulesh2.0-gprof-baseline``
     - Uninstrumented timing with ``-O3 -g -DNDEBUG -fno-omit-frame-pointer``.
   * - ``lulesh2.0-gprof``
     - Same flags, plus ``-pg`` during compilation and linking.

Both enable MPI and disable OpenMP. The core lesson uses one rank; the optional
extension uses eight single-threaded application ranks. LULESH requires cubic
rank counts, so twelve ranks are invalid. The 12-core allocation is a resource
limit, not a requirement to occupy all cores.

The GNU manual warns that glibc's ``mcount`` routine is not thread-safe. Keeping
application work single-threaded avoids an OpenMP comparison that this tool
cannot reliably support; runtime libraries may still have helper threads or
uninstrumented work. Use the VTune lesson for OpenMP profiling. Its existing
MPI/OpenMP executable is not the matched timing baseline for this lesson.

Instructor preparation, within a suitable allocation and with GCC, Open MPI,
CMake, Ninja and GNU gprof available:

.. code-block:: bash

   BUILD_JOBS=12 bash build_scripts/build_lulesh_gprof.sh /g/data/vp91/LULESH

Outputs are under ``build/gprof-baseline/bin/`` and ``build/gprof/bin/``.
Each build retains a manifest and compile commands. The module template uses
the known source root ``/g/data/vp91/LULESH``; edit its dependency versions to
match those used for compilation, then install it in the private module
directory. Keep source, debug information and executable identity fixed during
the class. Check permissions and runtime dependencies from a participant ARE
session.

What gprof counts, samples and estimates
---------------------------------------

``-pg`` adds function-entry hooks that record caller–callee arcs and call counts.
Periodic program-counter observations separately estimate self time. The entry
hooks do not measure every invocation's start-to-finish duration. Optimisation
can remove or transform call boundaries through inlining and other changes.

A call graph combines those inputs to estimate descendant cost. It assumes
comparable average callee cost for each caller. A routine that quickly returns
for one caller but does substantial work for another can violate that assumption.

The profile is not a complete record of elapsed time, sleeping, blocked I/O,
kernel work or shared-library activity. Interpret it within its scope.

Exercise 1: establish a baseline
--------------------------------

Warm up ``lulesh2.0-gprof-baseline`` and repeat the same uninstrumented run three
times. Start at ``-s 30 -i 200`` and calibrate to several seconds of calculation.
Check actual iterations, origin energy and symmetry diagnostics. The iteration
cap may not determine the actual iteration count.

Record median and range. The notebook saves both LULESH's calculation time and
launcher-to-exit time. These cover different intervals; use the same interval
for comparisons. The latter includes startup and, for instrumented runs,
profile-file writing.

Exercise 2: collect and inspect a flat profile
---------------------------------------------

In a fresh writable result directory inside the existing allocation:

.. code-block:: bash

   export OMP_NUM_THREADS=1 OMP_DYNAMIC=FALSE
   export GMON_OUT_PREFIX="$PWD/gmon"
   mpirun -np 1 --map-by slot:PE=1 --bind-to core \
     lulesh2.0-gprof -s 30 -i 200

The glibc profiling runtime writes ``prefix.PID`` on normal exit. Without a
prefix, the default ``gmon.out`` may overwrite an earlier result. Abnormal
termination can prevent output. The notebook wrapper also records the rank/PID
mapping and checks that every expected profile exists.

Use the exact executable used for collection and the actual raw filename:

.. code-block:: bash

   gprof -i /path/to/lulesh2.0-gprof /path/to/gmon.PID
   gprof -b --demangle -p /path/to/lulesh2.0-gprof /path/to/gmon.PID

``-i`` describes raw profile records, ``-b`` suppresses explanatory prose,
``-p`` selects the flat profile and ``--demangle`` prints readable C++ names.
**GNU gprof's ``-C`` requests execution counts; it is not a demangling flag.**

.. list-table:: Flat-profile fields
   :header-rows: 1
   :widths: 30 70

   * - Field
     - Meaning
   * - ``% time``
     - Share of attributed sampled time in this function itself.
   * - ``self seconds``
     - Sampled time attributed to the function's own code.
   * - ``cumulative seconds``
     - Running sum of self times down the table, not descendants.
   * - ``calls``
     - Observed instrumented calls where available; blank is not zero.
   * - ``self .../call``
     - Self time divided by calls; read the printed units.
   * - ``total .../call``
     - Self plus estimated descendant cost per call.

Inspect the stated sampling period. Very small or zero sampled times need
careful interpretation; a frequently called function may be cheap or poorly
resolved by sampling. Record observed hotspots instead of assuming a fixed
LULESH ranking.

Exercise 3: follow the call graph
---------------------------------

.. code-block:: bash

   gprof -b --demangle -q /path/to/lulesh2.0-gprof /path/to/gmon.PID

The primary row begins with ``[index]``; callers appear above and children
below. Its ``% time`` includes **self and estimated descendants**. Parent and
child costs overlap, so adding percentages is meaningless. The ``children``
field is inferred from call counts and sampled costs, not an independently
measured duration for each call path.

Choose a function present in the report, identify a caller and child, and
inspect the matching source at ``LULESH_SOURCE``. A source-text match does not
provide per-line timing. The notebook's core exercise is function-level analysis.

Exercise 4: measure profiling overhead
--------------------------------------

Warm up both builds, then alternate the order of three matched baseline/profile
pairs. Keep input, placement and timing region unchanged. Check all numerical
logs. Calculate the observed relative median difference:

.. math::

   100\left(\frac{\operatorname{median}(T_{pg})}
   {\operatorname{median}(T_{base})}-1\right)\%.

The result describes this instrumented build, workload and interval. Report
spread and measurement variability, including a noisy or negative result.
Do not interpret it as a universal profiler overhead percentage. Later code
optimisations must be checked using repeated uninstrumented timings.

Exercise 5: assess repeatability and sum profiles
-------------------------------------------------

Compare the three instrumented reports using absolute self times, calls and
rankings. Confirm the same executable, input, process/thread configuration,
actual iterations and numerical behaviour before merging. In a fresh directory:

.. code-block:: bash

   gprof -s /path/to/lulesh2.0-gprof \
     /path/to/run1/gmon.PID /path/to/run2/gmon.PID
   gprof -b --demangle -p /path/to/lulesh2.0-gprof gmon.sum

The result sums time and calls; it is not an average run. Aggregation can help
sampling resolution but does not remove instrumentation bias or call-graph
assumptions. The notebook rejects incompatible or duplicate input profiles and
retains the raw files.

State an observation, a source-based hypothesis, one proposed change and a
correctness/timing validation plan. If the explanation needs memory counters,
OpenMP worker behaviour or blocked time, identify the missing measurement.

Optional extension: eight MPI ranks
-----------------------------------

The notebook's ``RUN_MPI_EXTENSION`` switch enables eight ranks with one
application thread each. It sets a rank-specific prefix before executing each
application process, preserving PID through ``exec``. Expect eight nonempty
``gmon.rank-NNN.PID`` files and eight rank manifests.

Inspect individual rank profiles before summing them. Aggregation combines CPU
costs and calls, not MPI elapsed time or communication time. Less sampled compute
work can coexist with more waiting. At fixed ``-s``, the global mesh grows with
rank count, so this extension demonstrates profile coverage rather than
fixed-work speedup.

.. admonition:: Key Points
   :class: hint

   #. Compile and link the profiling build with ``-pg``; keep a matched baseline.
   #. Separate counted calls, sampled self time and inferred descendant cost.
   #. Read units, denominators, sampling resolution and call-graph assumptions.
   #. Preserve raw files and the exact matching executable identity.
   #. Measure overhead and validate hypotheses with uninstrumented timings.
   #. Use one application thread per rank and unique files for MPI collection.

References
----------

* `GNU gprof manual <https://sourceware.org/binutils/docs/gprof/>`_.
* `Compilation <https://sourceware.org/binutils/docs/gprof/Compiling.html>`_,
  `execution <https://sourceware.org/binutils/docs/gprof/Executing.html>`_, and
  `output options <https://sourceware.org/binutils/docs/gprof/Output-Options.html>`_.
* `Flat profiles <https://sourceware.org/binutils/docs/gprof/Flat-Profile.html>`_,
  `call-graph primary rows <https://sourceware.org/binutils/docs/gprof/Primary.html>`_,
  `sampling error <https://sourceware.org/binutils/docs/gprof/Sampling-Error.html>`_
  and `child-time assumptions <https://sourceware.org/binutils/docs/gprof/Assumptions.html>`_.
* `LLNL gprof guide <https://hpc.llnl.gov/software/development-environment-software/gprof>`_.
* `LLNL LULESH <https://github.com/LLNL/LULESH>`_.
* `NCI ARE training <https://nci900-training-organisation.github.io/learning-resources/Getting-Started/use-jupyterlab.html>`_.
