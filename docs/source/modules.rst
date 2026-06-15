Modules
=======

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