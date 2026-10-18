Modules
=======

Intel VTune workshop
--------------------

For the ``vp91`` training, use the private ``lulesh`` module containing the
prebuilt MPI/OpenMP application:

.. code-block:: bash

   module load lulesh
   module load intel-vtune/2024.2.1
   command -v lulesh2.0 mpirun vtune

Use the instructor-confirmed VTune version. The ``lulesh`` module supplies the
matching runtime dependencies. Participants do not need CMake or Ninja.

In ARE, enter ``lulesh intel-vtune/2024.2.1`` in **Advanced options → Modules**
before launching the 12-core, single-node JupyterLab session. If necessary,
enter the instructor's private modulefile directory in **Module directories**.
Mount ``scratch/vp91`` and any storage containing the module and application.
The module should set ``LULESH_SOURCE`` to its matching source directory.

Other tutorial modules
----------------------

The following versions are examples used across the broader profiling
materials. They are not a list of modules participants must load for VTune.

.. note::
    
    #. gcc/10.3.0
    #. openmpi/4.1.7
    #. cuda/12.9.0
    #. papi/7.1.0
    #. intel-mkl/2024.2.1
    #. intel-vtune/2024.2.1
    #. hpctoolkit/2021.05.15
    #. hpcviewer/2021.05.15
    #. cmake/3.8.2

Modules are how we manage software in most HPC machines. We can see all the available modules using the command

.. code-block:: console
    :linenos:
    
    module avail

If we want load a module *python3/3.11.0* we can use the command

.. code-block:: console
    :linenos:

    module load python3/3.11.0

If we want to unload the same module use the command

.. code-block:: console
    :linenos:
    
    module unload python3/3.11.0

We can unload all the modules using the command

.. code-block:: console
    :linenos:
    
    module purge