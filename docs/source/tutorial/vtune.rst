Intel VTune
==========================

.. admonition:: Overview
   :class: Overview

    * **Tutorial:** 45 min

        **Objectives:**
            #. Understand the basics of Intel Vtune and how to use it for profiling applications.


Intel VTune Profiler is a performance analysis tool that helps developers identify performance bottlenecks in their applications.
It provides insights into CPU usage, threading performance, memory access patterns, and more.   

First compile the code with the appropriate flags to enable profiling.
The cmake command used is:

..  code-block:: bash
    :linenos:

    cmake -G Ninja \
        -DCMAKE_BUILD_TYPE=RelWithDebInfo \
        -DMPI_CXX_COMPILER="$(which mpicxx)" \
        -DWITH_MPI=On \
        -DWITH_OPENMP=On \
        -DCMAKE_INSTALL_PREFIX="$INSTALLDIR" \
        -DCMAKE_CXX_FLAGS="-g -O3 -fno-omit-frame-pointer" \
        "$SRCDIR"

where ``-DCMAKE_CXX_FLAGS="-g -O3 -fno-omit-frame-pointer" `` is used to enable profiling with gprof. 


HotsPot Analysis
-------------------

HotsPot analysis helps identify the most time-consuming functions in your application.



..  code-block:: bash
    :linenos:

    ./vtune -collect hotspots -result-dir vtune_hotspots mpirun -np 4 ./lulesh2.0 -s 20

This will generate a directory named ``vtune_hotspots`` in the current directory after the program completes.
To analyze the profiling data, use the following command:   

..  code-block:: bash
    :linenos:

    vtune -report summary -result-dir vtune_hotspots

This will display a summary of the profiling results, including the most time-consuming functions and 
their respective CPU usage.


1. **CPU Time**:

    * Total time all threads spent on-CPU (executing instructions, even if just spinning).
    
    * This is not wall-clock runtime, it’s aggregated across threads.

2. **Effective Time**:

    * Time actually doing useful work (retired instructions, arithmetic, etc.).

    * The closer this is to CPU Time, the better.

3. **Spin Time:**

    * Time threads spent actively waiting (busy-waiting) rather than progressing.

    * Common causes in HPC apps like LULESH:
        - OpenMP threads waiting at barriers

        - MPI processes spinning in synchronization calls

        - Locks/spinlocks in runtime libraries

    * VTune is hinting that ~11% of CPU time was wasted in spin-wait.



4. **Overhead Time:**

    * Time in the runtime system itself (thread scheduling, task bookkeeping, OpenMP runtime).

    * Zero here means runtime overhead was negligible.

5. **Total Thread Count:**

    * Number of software threads seen during execution.

    * On an MPI + OpenMP run, this equals:

        - MPI ranks × OpenMP threads per rank
        - Or possibly extra threads from the runtime.


6. **Paused Time:** 

    * Time threads were deliberately suspended or descheduled (not runnable).

    * None here → all waiting was spin-based, not due to OS sleeping.


7. **Top Hotspots Function:**

    * The function consuming the most CPU time.

8. **Effective Physical Core Utilization:** 

    * 48 = the number of physical cores on your node (VTune detected this from the hardware).

    * 1.630 = the average number of physical cores doing useful work at any given time.

    * 3.4% = (1.630 ÷ 48) × 100 → basically says:
        - Out of 48 cores available, on average only ~3.4% were actually contributing useful computation.
        - This is a sign of poor parallel efficiency, likely due to load imbalance, excessive synchronization, or insufficient parallelism.

9. **Effective Logical Core Utilization:** 

    * 96 = total number of logical cores on your system.
    * Your machine has 48 physical cores with Hyper-Threading (SMT) → 2 logical per physical = 96.
    * 1.651 = the average number of logical cores that were effectively doing useful work.
    * 1.7% = (1.651 ÷ 96) × 100.
    * So on average, only ~1.6 logical cores were active out of 96 possible.


HPC Performance
--------------------

``hpc-performance`` gives a much more detailed view of parallel performance, especially for MPI + OpenMP codes like LULESH.

To run the HPC performance analysis, use the following command:

..  code-block:: bash
    :linenos:

    vtune -collect hpc-performance -result-dir vtune_hpc mpirun -np 4 ./lulesh2.0 -s 20

After the program completes, analyze the profiling data with:

..  code-block:: bash
    :linenos:

    vtune -report summary -result-dir vtune_hpc


Memory Aceess
-------------------

..  code-block:: bash
    :linenos:

    vtune -collect memory-access -result-dir vtune_mem mpirun -np 4 ./lulesh2.0 -s 20



GUI Analysis
-------------------

To see the analysis in a GUI, you can launch the VTune GUI with the following command:

..  code-block:: bash
    :linenos:

    vtune-gui vtune_hotspots



.. admonition:: Key Points
   :class: hint
   
    #. GProf is a performance analysis tool for Unix-like operating systems.
    #. It helps identify performance bottlenecks in code by analyzing function calls and execution times
    #. To use GProf with a C++ application, compile the code with the `-pg` flag.
    #. Run the application to generate a `gmon.out` file.
    #. Analyze the data using the `gprof` command.
    #. Flat Profile section summarizes time spent in each function.
    #. Call Graph section provides a detailed view of function calls and their relationships.
    



