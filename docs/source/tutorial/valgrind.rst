Valgrind
==========================

.. admonition:: Overview
   :class: Overview

    * **Tutorial:** 60 min

        **Objectives:**
            #. Use Memcheck to find invalid memory operations, uninitialized values, and memory leaks.
            #. Use Callgrind, Cachegrind, and Massif to inspect program execution and memory use.



Valgrind is a suite of tools for debugging and profiling programs. This tutorial uses Memcheck to find memory
errors and leaks, then introduces Callgrind, Cachegrind, and Massif for profiling function costs, cache behavior,
and heap usage. The examples are small C programs so that each report is easy to interpret.

First, start an interactive job on the cluster 



..  code-block:: bash

    qsub -I -q normal -P vp91 -l walltime=02:00:00 -l ncpus=48 -l mem=192GB -l wd


and load the necessary modules.

..  code-block:: bash

    module load gcc/15.1.0


Run Valgrind to detect memory leaks
---------------------------------


Compile the code with debugging information

..  code-block:: bash

    cd /scratch/vp91/$USER/intro-to-profiling/code/valgrind
    gcc -g -O0 01-leak.c -o 01-leak

* `-g` enables debugging information.
* `-O0` disables optimizations to make debugging easier.

Now run the program with Valgrind to check for memory leaks

..  code-block:: bash

    valgrind ./01-leak

This will produce output indicating any memory leaks detected in the program. Look for lines that mention 
"definitely lost" to identify memory that was allocated but not freed.

Sample output will be similar to:

..  code-block:: bash

    ==384063== HEAP SUMMARY:
    ==384063==     in use at exit: 40 bytes in 1 blocks
    ==384063==   total heap usage: 1 allocs, 0 frees, 40 bytes allocated
    ==384063==
    ==384063== LEAK SUMMARY:
    ==384063==    definitely lost: 40 bytes in 1 blocks
    ==384063==    indirectly lost: 0 bytes in 0 blocks
    ==384063==      possibly lost: 0 bytes in 0 blocks
    ==384063==    still reachable: 0 bytes in 0 blocks
    ==384063==         suppressed: 0 bytes in 0 blocks
    ==384063== Rerun with --leak-check=full to see details of leaked memory
    ==384063==
    ==384063== For lists of detected and suppressed errors, rerun with: -s
    ==384063== ERROR SUMMARY: 0 errors from 0 contexts (suppressed: 0 from 0)


* **Definitely lost**: No pointer to the allocated memory exists at program exit. This a real memory leak that must be fixed.

* **Indirectly lost**: Memory is only reachable through another leaked block. Fixing the *definitely lost* allocation will fix this too.

* **Possibly lost**: A pointer exists but does not point to the start of the allocation → **ambiguous**, often caused by pointer arithmetic and usually a bug.

* **Still reachable**: Memory is still referenced at exit and could be freed → **not a true leak**, typically safe to ignore.

Indirect leak example
----------------------

Compile the code with debugging information

..  code-block:: bash

    cd /scratch/vp91/$USER/intro-to-profiling/code/valgrind

    gcc -g -O0 02-indirect.c -o 02-indirect

and run Valgrind

..  code-block:: bash

    valgrind ./02-indirect

Sample output will be similar to:

..  code-block:: bash

    ==384410== HEAP SUMMARY:
    ==384410==     in use at exit: 48 bytes in 2 blocks
    ==384410==   total heap usage: 2 allocs, 0 frees, 48 bytes allocated
    ==384410==
    ==384410== LEAK SUMMARY:
    ==384410==    definitely lost: 8 bytes in 1 blocks
    ==384410==    indirectly lost: 40 bytes in 1 blocks
    ==384410==      possibly lost: 0 bytes in 0 blocks
    ==384410==    still reachable: 0 bytes in 0 blocks
    ==384410==         suppressed: 0 bytes in 0 blocks


Possibly lost example
----------------------

Compile the code with debugging information

..  code-block:: bash

    cd /scratch/vp91/$USER/intro-to-profiling/code/valgrind

    gcc -g -O0 03-possible.c -o 03-possible


run Valgrind

..  code-block:: bash

    valgrind ./03-possible


Sample output will be similar to:

..  code-block:: bash
    
    ==384772== HEAP SUMMARY:
    ==384772==     in use at exit: 100 bytes in 1 blocks
    ==384772==   total heap usage: 1 allocs, 0 frees, 100 bytes allocated
    ==384772==
    ==384772== LEAK SUMMARY:
    ==384772==    definitely lost: 0 bytes in 0 blocks
    ==384772==    indirectly lost: 0 bytes in 0 blocks
    ==384772==      possibly lost: 100 bytes in 1 blocks
    ==384772==    still reachable: 0 bytes in 0 blocks
    ==384772==         suppressed: 0 bytes in 0 blocks


.. admonition:: Note
   :class: note

    Valgrind classifies leaks by what pointers remain reachable at program exit, not simply by whether free was called.

    Here, the global `g` still points into the allocated block, at `base + 10`. Since that's an interior pointer rather than the start of 
    the block, Memcheck reports the allocation as possibly lost. It can't establish whether the pointer is intentionally pointing into the block 
    or whether the original pointer was lost.


.. admonition:: Todo
   :class: note

    What happens if you set `g = NULL;` before returning? Try it and see how the report changes.



Still reachable example
----------------------

Comnpile the code with debugging information

..  code-block:: bash

    cd /scratch/vp91/$USER/intro-to-profiling/code/valgrind

    gcc -g -O0 04-still_reachable.c -o 04-still_reachable

Run Valgrind

..  code-block:: bash

    valgrind ./04-still_reachable

Sample output will be similar to:

..  code-block:: bash


    ==384651== HEAP SUMMARY:
    ==384651==     in use at exit: 100 bytes in 1 blocks
    ==384651==   total heap usage: 1 allocs, 0 frees, 100 bytes allocated
    ==384651==
    ==384651== LEAK SUMMARY:
    ==384651==    definitely lost: 0 bytes in 0 blocks
    ==384651==    indirectly lost: 0 bytes in 0 blocks
    ==384651==      possibly lost: 0 bytes in 0 blocks
    ==384651==    still reachable: 100 bytes in 1 blocks
    ==384651==         suppressed: 0 bytes in 0 blocks


Detailed leak report
----------------------

To see more details about the leaks, rerun Valgrind with the `--leak-check=full` option:

..  code-block:: bash

    cd /scratch/vp91/$USER/intro-to-profiling/code/valgrind
    gcc -g -O0 05-leaks_all.c -o 05-leaks_all


Run Valgrind

..  code-block:: bash

    valgrind --leak-check=full --show-leak-kinds=all ./05-leaks_all


* **--leak-check=full**: provides detailed information about each memory leak.

* **--show-leak-kinds=all**: shows all types of leaks: definitely lost, indirectly lost, possibly lost, and still reachable.

Sample output will be similar to:

..  code-block:: bash

    ==384913== HEAP SUMMARY:
    ==384913==     in use at exit: 428 bytes in 5 blocks
    ==384913==   total heap usage: 5 allocs, 0 frees, 428 bytes allocated
    ==384913==
    ==384913== 40 bytes in 1 blocks are definitely lost in loss record 1 of 5
    ==384913==    at 0x4C39185: malloc (vg_replace_malloc.c:442)
    ==384913==    by 0x400617: main (05-leaks_all.c:16)
    ==384913==
    ==384913== 80 bytes in 1 blocks are indirectly lost in loss record 2 of 5
    ==384913==    at 0x4C39185: malloc (vg_replace_malloc.c:442)
    ==384913==    by 0x400633: main (05-leaks_all.c:21)
    ==384913==
    ==384913== 88 (8 direct, 80 indirect) bytes in 1 blocks are definitely lost in loss record 3 of 5
    ==384913==    at 0x4C39185: malloc (vg_replace_malloc.c:442)
    ==384913==    by 0x400625: main (05-leaks_all.c:20)
    ==384913==
    ==384913== 100 bytes in 1 blocks are possibly lost in loss record 4 of 5
    ==384913==    at 0x4C39185: malloc (vg_replace_malloc.c:442)
    ==384913==    by 0x400647: main (05-leaks_all.c:25)
    ==384913==
    ==384913== 200 bytes in 1 blocks are still reachable in loss record 5 of 5
    ==384913==    at 0x4C39185: malloc (vg_replace_malloc.c:442)
    ==384913==    by 0x400664: main (05-leaks_all.c:30)
    ==384913==
    ==384913== LEAK SUMMARY:
    ==384913==    definitely lost: 48 bytes in 2 blocks
    ==384913==    indirectly lost: 80 bytes in 1 blocks
    ==384913==      possibly lost: 100 bytes in 1 blocks
    ==384913==    still reachable: 200 bytes in 1 blocks
    ==384913==         suppressed: 0 bytes in 0 blocks

Invalid accesses 
----------------------------------------------------

Memcheck also detects invalid reads and writes.

..  code-block:: bash

    gcc -g -O0 06-invalid_access.c -o 06-invalid_access
    valgrind ./06-invalid_access

Sample output will be similar to:

..  code-block:: bash

    ==1872382== Memcheck, a memory error detector
    ==1872382== Copyright (C) 2002-2022, and GNU GPL'd, by Julian Seward et al.
    ==1872382== Using Valgrind-3.22.0 and LibVEX; rerun with -h for copyright info
    ==1872382== Command: ./06-invalid_access
    ==1872382== 
    ==1872382== Invalid write of size 4
    ==1872382==    at 0x400674: main (06-invalid_access.c:7)
    ==1872382==  Address 0x5222048 is 0 bytes after a block of size 8 alloc'd
    ==1872382==    at 0x4C39185: malloc (vg_replace_malloc.c:442)
    ==1872382==    by 0x400667: main (06-invalid_access.c:5)
    ==1872382== 
    ==1872382== Invalid read of size 4
    ==1872382==    at 0x40067E: main (06-invalid_access.c:8)
    ==1872382==  Address 0x5222048 is 0 bytes after a block of size 8 alloc'd
    ==1872382==    at 0x4C39185: malloc (vg_replace_malloc.c:442)
    ==1872382==    by 0x400667: main (06-invalid_access.c:5)
    ==1872382== 
    ==1872382== 
    ==1872382== HEAP SUMMARY:
    ==1872382==     in use at exit: 0 bytes in 0 blocks
    ==1872382==   total heap usage: 1 allocs, 1 frees, 8 bytes allocated
    ==1872382== 
    ==1872382== All heap blocks were freed -- no leaks are possible
    ==1872382== 
    ==1872382== For lists of detected and suppressed errors, rerun with: -s
    ==1872382== ERROR SUMMARY: 2 errors from 2 contexts (suppressed: 0 from 0)


Uninitialized values
----------------------------------------------------

Memcheck also detects uses of uninitialized values, which can lead to unpredictable behavior. 
An uninitialized value is reported when the program uses it, for example in a conditional branch. Ask Memcheck
to track where the value originated:


..  code-block:: bash

    gcc -g -O0 07-uninitialized.c -o 07-uninitialized
    valgrind ./07-uninitialized

Sample output will be similar to:

..  code-block:: bash

    ==1872478== Memcheck, a memory error detector
    ==1872478== Copyright (C) 2002-2022, and GNU GPL'd, by Julian Seward et al.
    ==1872478== Using Valgrind-3.22.0 and LibVEX; rerun with -h for copyright info
    ==1872478== Command: ./07-uninitialized
    ==1872478== 
    ==1872478== Conditional jump or move depends on uninitialised value(s)
    ==1872478==    at 0x400675: main (07-uninitialized.c:7)
    ==1872478== 
    ==1872478== 
    ==1872478== HEAP SUMMARY:
    ==1872478==     in use at exit: 0 bytes in 0 blocks
    ==1872478==   total heap usage: 1 allocs, 1 frees, 4 bytes allocated
    ==1872478== 
    ==1872478== All heap blocks were freed -- no leaks are possible
    ==1872478== 
    ==1872478== Use --track-origins=yes to see where uninitialised values come from
    ==1872478== For lists of detected and suppressed errors, rerun with: -s
    ==1872478== ERROR SUMMARY: 1 errors from 1 contexts (suppressed: 0 from 0)


``--track-origins=yes`` adds origin information to undefined-value reports and can make the run slower. Follow
the first relevant application stack frame back to the source, initialize or otherwise correct the value, and
rerun Memcheck to verify the report is gone.

..  code-block:: bash

    valgrind --track-origins=yes ./07-uninitialized


Invalid operations
--------------------


Memcheck detects invalid memory operations, such as writing past the end of an allocation, reading freed storage, 
freeing the same allocation twice, or passing a stack address to ``free``. 

..  code-block:: bash

    gcc -g -O0 08-invalid_operations.c -o 08-invalid_operations

The scenarios read freed storage, free the same allocation twice, or pass a stack address to ``free``. 

..  code-block:: bash

    valgrind ./08-invalid_operations use-after-free
    valgrind ./08-invalid_operations double-free
    valgrind ./08-invalid_operations invalid-free




Diagnose, fix, and verify
-------------------------

Use a full leak report to locate the allocation site in the intentionally leaking example:

..  code-block:: bash

    valgrind --leak-check=full ./01-leak

The report's ``by`` frames show the application call path and source line when debug information is available.
Compare it with the corrected version, which releases the allocation:

..  code-block:: bash

    gcc -g -O0 09-leak_fixed.c -o 09-leak_fixed
    valgrind --leak-check=full --error-exitcode=1 ./09-leak_fixed

The corrected program should finish without Memcheck errors. ``--error-exitcode=1`` makes Valgrind return a
nonzero status when it reports an error, which is useful in scripts and CI. To make leak kinds count as errors,
specify them explicitly:

..  code-block:: bash

    valgrind --leak-check=full --errors-for-leak-kinds=definite,possible \
        --error-exitcode=1 ./01-leak

Suppressions
------------

Suppression files can silence known reports from external libraries when those reports are understood and
unavoidable. First ask Valgrind to print candidate suppression blocks:

..  code-block:: bash

    valgrind --gen-suppressions=all ./your_program

Review a candidate carefully, copy the relevant block into a text file such as ``project.supp``, then pass it
back to Valgrind:

..  code-block:: bash

    valgrind --suppressions=project.supp ./your_program

Do not suppress reports from your own code just to make the output clean. Fix those errors instead, and keep
suppression files small and documented.

Callgrind: function costs and call relationships
------------------------------------------------

Callgrind records function call relationships and instruction costs. Compile the sample workload and collect a
profile:

..  code-block:: bash

    gcc -g -O0 10-profile_workload.c -o 10-profile_workload
    valgrind --tool=callgrind ./10-profile_workload

Callgrind writes a file named ``callgrind.out.<pid>``. Replace ``<pid>`` with the number in the generated
filename, then inspect the profile in the terminal or open it in KCachegrind if that viewer is installed:

..  code-block:: bash

    callgrind_annotate --auto=yes callgrind.out.<pid>

Use the annotated output or call graph to find functions with high instruction costs and understand which
callers contribute to them. Callgrind's instruction counts are useful for comparing work, but are not wall-clock
timings.

Cachegrind: instruction and cache behavior
------------------------------------------

Cachegrind records instruction counts and simulated cache events. Run the same workload and annotate the
result:

..  code-block:: bash

    valgrind --tool=cachegrind --cachegrind-out-file=cachegrind.out ./10-profile_workload
    cg_annotate --auto=yes cachegrind.out

Inspect instruction counts and cache read/write misses, then use source annotations to find where they occur.
Cachegrind's cache behavior is simulated; it is not a direct measurement of the machine's live hardware counters.

Massif: heap usage over time
----------------------------

Massif samples heap allocation over the program's execution. Collect and print a report:

..  code-block:: bash

    valgrind --tool=massif --massif-out-file=massif.out ./10-profile_workload
    ms_print massif.out

Read the graph and snapshots to find when heap use peaks, then inspect the allocation tree around that point.
Massif profiles heap allocations; it does not replace Memcheck for finding invalid accesses or leaks.

Running Valgrind effectively
---------------------------

Valgrind adds substantial runtime and memory overhead. Use a small, representative input while learning, and do
not treat Valgrind timings as native performance measurements. The available tools and supported CPU
architectures depend on the installed Valgrind build; on a cluster, run within an allocated job and follow the
site's software and resource policies.

.. admonition:: Key Points
   :class: hint

    #. Memcheck detects invalid memory operations, uninitialized values, and memory leaks.
    #. Compile with ``-g`` and use ``--track-origins=yes`` when tracking the source of an uninitialized value.
    #. Use ``--leak-check=full`` and interpret the stack trace to locate allocation sites.
    #. Callgrind profiles function call costs, Cachegrind reports instruction and simulated cache events, and Massif tracks heap use.
    #. Valgrind runs have significant overhead; use representative inputs and do not use them for native timing comparisons.