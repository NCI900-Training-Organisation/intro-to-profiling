Setup the Application
==========================

.. admonition:: Overview
   :class: Overview

    * **Tutorial:** 30 min

        **Objectives:**
            #. Setup the application to be profiled.


The application we are going to use LULESH (Livermore Unstructured Lagrangian Explicit Shock 
Hydrodynamics). It is a proxy application that implements a Lagrangian hydrodynamics model for 
simulating shock wave propagation in materials. The code is written in C++ and is parallelized 
using MPI (Message Passing Interface) for distributed memory systems.

Build the LULESH application
----------------------------

..  code-block:: bash
    :linenos:

    cd /scratch/vp91/$USER
    git clone https://github.com/LLNL/LULESH.git

    cd /scratch/vp91/$USER/intro-to-profiling/build_scripts

The run the following command to build the LULESH application with gprof enabled:

..  code-block:: bash
    :linenos:

    ./build_lulesh_gprof.sh /scratch/vp91/$USER/LULESH

For Intel Vtune use


..  code-block:: bash
    :linenos:

    ./build_lulesh_vtune.sh /scratch/vp91/$USER/LULESH


For HCPToolkit use


..  code-block:: bash
    :linenos:

    ./build_lulesh_hpctoolkit.sh /scratch/vp91/$USER/LULESH





Test the LULESH application
----------------------------

..  code-block:: bash
    :linenos:

    qsub -I -q normal -P vp91 -l walltime=02:00:00 -l ncpus=48 -l mem=192GB -l wd

..  code-block:: bash
    :linenos:

    cd /scratch/vp91/$USER/LULESH/build
    ./lulesh2.0 -s 20





.. admonition:: Key Points
   :class: hint
   
    #. LULESH is a proxy application for simulating shock wave propagation in materials.
    #. It is written in C++ and parallelized using MPI.
    #. The application can be built and tested on a high-performance computing cluster.
    



