MaMMoS documentation
====================

.. toctree::
   :maxdepth: 1
   :hidden:

   Demonstrator <demonstrator/index>
   examples/index
   api/index
   design
   changelog


Framework
---------

The MaMMoS framework provides software components for magnetic multiscale
modeling. The following table provides a short overview and contains links to
example and API reference for the individual components. The binder badges allow
running the examples for the individual packages interactively in the cloud.

.. list-table::
   :header-rows: 1

   * - Package repository
     - Examples
     - API
     - Interactive examples
   * - `mammos <https://github.com/mammos-project/mammos>`__
     - :doc:`Demonstrator <demonstrator/index>`
     - –
     - |binder-mammos-1| |binder-mammos-2|
   * - `mammos-analysis <https://github.com/mammos-project/mammos-analysis>`__
     - :doc:`examples/mammos-analysis/index`
     - :doc:`api/mammos_analysis`
     - |binder-analysis-1| |binder-analysis-2|
   * - `mammos-dft <https://github.com/mammos-project/mammos-dft>`__
     - :doc:`examples/mammos-dft/index`
     - :doc:`api/mammos_dft`
     - |binder-dft-1| |binder-dft-2|
   * - `mammos-entity <https://github.com/mammos-project/mammos-entity>`__
     - :doc:`examples/mammos-entity/index`
     - :doc:`api/mammos_entity`
     - |binder-entity-1| |binder-entity-2|
   * - `mammos-mumag <https://github.com/mammos-project/mammos-mumag>`__
     - :doc:`examples/mammos-mumag/index`
     - :doc:`api/mammos_mumag`
     - |binder-mumag-1| |binder-mumag-2|
   * - `mammos-spindynamics <https://github.com/mammos-project/mammos-spindynamics>`__
     - :doc:`examples/mammos-spindynamics/index`
     - :doc:`api/mammos_spindynamics`
     - |binder-spindynamics-1| |binder-spindynamics-2|
   * - `mammos-units <https://github.com/mammos-project/mammos-units>`__
     - :doc:`examples/mammos-units/index`
     - :doc:`api/mammos_units`
     - |binder-units-1| |binder-units-2|

.. |binder-mammos-1| image:: /_static/badge-launch-binder.svg
          :target: https://mybinder.org/v2/gh/mammos-project/mammos/latest?urlpath=lab%2Ftree%2Fexamples
.. |binder-mammos-2| image:: /_static/badge-launch-binder2.svg
          :target: https://notebooks.mpcdf.mpg.de/binder/v2/gl/mammos-project%2Fmammos/latest?urlpath=lab%2Ftree%2Fexamples
.. |binder-analysis-1| image:: /_static/badge-launch-binder.svg
          :target: https://mybinder.org/v2/gh/mammos-project/mammos-analysis/latest?urlpath=lab%2Ftree%2Fexamples
.. |binder-analysis-2| image:: /_static/badge-launch-binder2.svg
          :target: https://notebooks.mpcdf.mpg.de/binder/v2/gl/mammos-project%2Fmammos-analysis/latest?urlpath=lab%2Ftree%2Fexamples
.. |binder-dft-1| image:: /_static/badge-launch-binder.svg
          :target: https://mybinder.org/v2/gh/mammos-project/mammos-dft/latest?urlpath=lab%2Ftree%2Fexamples
.. |binder-dft-2| image:: /_static/badge-launch-binder2.svg
          :target: https://notebooks.mpcdf.mpg.de/binder/v2/gl/mammos-project%2Fmammos-dft/latest?urlpath=lab%2Ftree%2Fexamples
.. |binder-entity-1| image:: /_static/badge-launch-binder.svg
          :target: https://mybinder.org/v2/gh/mammos-project/mammos-entity/latest?urlpath=lab%2Ftree%2Fexamples
.. |binder-entity-2| image:: /_static/badge-launch-binder2.svg
          :target: https://notebooks.mpcdf.mpg.de/binder/v2/gl/mammos-project%2Fmammos-entity/latest?urlpath=lab%2Ftree%2Fexamples
.. |binder-mumag-1| image:: /_static/badge-launch-binder.svg
          :target: https://mybinder.org/v2/gh/mammos-project/mammos-mumag/latest?urlpath=lab%2Ftree%2Fexamples
.. |binder-mumag-2| image:: /_static/badge-launch-binder2.svg
          :target: https://notebooks.mpcdf.mpg.de/binder/v2/gl/mammos-project%2Fmammos-mumag/latest?urlpath=lab%2Ftree%2Fexamples
.. |binder-spindynamics-1| image:: /_static/badge-launch-binder.svg
          :target: https://mybinder.org/v2/gh/mammos-project/mammos-spindynamics/latest?urlpath=lab%2Ftree%2Fexamples
.. |binder-spindynamics-2| image:: /_static/badge-launch-binder2.svg
          :target: https://notebooks.mpcdf.mpg.de/binder/v2/gl/mammos-project%2Fmammos-spindynamics/latest?urlpath=lab%2Ftree%2Fexamples
.. |binder-units-1| image:: /_static/badge-launch-binder.svg
          :target: https://mybinder.org/v2/gh/mammos-project/mammos-units/latest?urlpath=lab%2Ftree%2Fexamples
.. |binder-units-2| image:: /_static/badge-launch-binder2.svg
          :target: https://notebooks.mpcdf.mpg.de/binder/v2/gl/mammos-project%2Fmammos-units/latest?urlpath=lab%2Ftree%2Fexamples


Additional tools
----------------

An overview of other tools created through or supported by the MaMMoS project is
available at https://mammos-project.github.io/#additional-tools.

.. _installation:

Framework installation
----------------------

The MaMMoS framework consists of a collection of packages (see :doc:`design
<design>` for more details). The metapackage ``mammos`` can be used to install a
consistent set of these packages.

The package ``mammos-mumag`` depends on ``jax``. To get jax with GPU support you
will need to manually install ``jax`` with the required optional dependencies
matching your GPU hardware/software, e.g. for an NVIDIA GPU you may need to
install ``jax[cuda12]``. For details please refer to the `jax installation
instructions <https://docs.jax.dev/en/latest/installation.html>`__.

.. tab-set::

   .. tab-item:: pixi

      Requirements: ``pixi`` (https://pixi.sh/)

      Pixi will install Python and mammos.

      To conveniently work with the notebook tutorials we install
      ``jupyterlab``. (``packaging`` needs to be pinned due to a limitation of
      pixi/PyPI.):

      Some examples also require `esys-escript
      <https://github.com/LutzGross/esys-escript.github.io>`__. On linux we can
      install it from conda-forge. On Mac or Windows refer to the esys-escript
      installation instructions:

      - Linux:

        .. code:: shell

           pixi init
           pixi add python=3.11 jupyterlab esys-escript uppasd
           pixi add mammos --pypi
           pixi add --pypi "jax[cuda12]"  # assuming an NVIDIA GPU with CUDA 12, see comment above

      - Mac/Windows:

        .. code:: shell

           pixi init
           pixi add python=3.11 jupyterlab uppasd
           pixi add mammos --pypi
           pixi add --pypi "jax[cuda12]"  # assuming an NVIDIA GPU with CUDA 12, see comment above

      Finally start a shell where the installed packages are available:

      .. code:: shell

         pixi shell

   .. tab-item:: conda

      Requirements: ``conda`` (https://conda-forge.org/download/)

      Use ``conda`` in combination with ``pip`` to get packages from
      conda-forge and PyPI.

      To conveniently work with the notebook tutorials we install
      ``jupyterlab``. (``packaging`` needs to be pinned due to a dependency
      issue in ``mammos-entity``.)

      Some examples also require `esys-escript
      <https://github.com/LutzGross/esys-escript.github.io>`__. On linux we can
      install it from conda-forge. On Mac or Windows refer to the esys-escript
      installation instructions.

      .. code:: shell

         conda create -n mammos-environment python=3.11 pip jupyterlab esys-escript uppasd
         conda activate mammos-environment
         pip install mammos
         pip install "jax[cuda12]"  # assuming an NVIDIA GPU with CUDA 12, see comment above

   .. tab-item:: pip

      Requirements: ``python=3.11`` and ``pip``

      When using ``pip`` we recommend creating a virtual environment to isolate the MaMMoS installation.

      First, create a new virtual environment. Here, we choose the name
      ``mammos-venv``.

      .. code:: shell

         python3 -m venv mammos-venv

      To activate it, run

      - on MacOS/Linux

        .. code:: shell

          . mammos-venv/bin/activate

      - on Windows

        .. code:: shell

           mammos-venv/bin/activate.sh

      Finally install ``mammos`` from PyPI:

      .. code:: shell

        pip install mammos
        pip install "jax[cuda12]"  # assuming an NVIDIA GPU with CUDA 12, see comment above

      Some examples also require `esys-escript
      <https://github.com/LutzGross/esys-escript.github.io>`__, which must be
      installed separately. Please refer to the documentation of esys-escript
      for installation instructions.

.. include:: /downloading-examples.rst

Acknowledgements
----------------

This software has been supported by the European Union’s Horizon Europe research and innovation programme under grant agreement No 101135546 `MaMMoS <https://mammos-project.github.io/>`__.
