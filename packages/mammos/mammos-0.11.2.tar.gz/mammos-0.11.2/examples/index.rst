MaMMoS Demonstrator
===================

This demonstrator contains end-to-end workflows combining functionality of
multiple of the MaMMoS framework components. The individual workflows have been
prepared in the form of Jupyter notebooks and you can either browse a static
version on this webpage or execute them interactively (see below). All notebooks
are independent and can be executed in arbitrary order, or you can pick the ones
you are interested in.

You can execute the workflows in the cloud by clicking on one of the Binder
buttons in the following table. Note that binder sessions time out after a
certain period of inactivity and that you only get access to limited computing
resources (e.g., no GPU). To run the notebooks locally, you should first follow
the :ref:`installation instructions <installation>` and can afterwards download
all notebooks as explained at the end of this page (once downloaded, all
demonstrator notebooks will be under ``examples/mammos``).

Some of the workflows require additional software, see `Requirements` at the top
of the individual notebooks.

.. toctree::
   :maxdepth: 1
   :hidden:

   hard-magnet-tutorial
   hard-magnet-material-exploration
   hard-magnet-ai-surrogate-model
   sensor
   spindynamics-temperature-dependent-parameters

.. list-table::
   :header-rows: 1

   * - Workflow (static page)
     - Interactive execution in the cloud
   * - :doc:`hard-magnet-tutorial`
     - |1-mybinder| |1-mpcdf|
   * - :doc:`hard-magnet-material-exploration`
     - |2-mybinder| |2-mpcdf|
   * - :doc:`hard-magnet-ai-surrogate-model`
     - |4-mybinder| |4-mpcdf|
   * - :doc:`sensor`
     - |3-mybinder| |3-mpcdf|
   * - :doc:`spindynamics-temperature-dependent-parameters`
     - |5-mybinder| |5-mpcdf|

.. note::

   In some of the notebooks the setup has been simplified in order to keep the
   runtimes reasonably short (in particular when executed in the cloud), e.g. by
   simulating a system of a smaller size than is realistic in actual
   application. You can scale the problem back up by modifying the notebook, if
   you have enough hardware resources to run simulations at a realistic scale.


Additional notebooks showing more (low-level) details for the individual framework components are available in :doc:`/examples/index`.

.. include:: /downloading-examples.rst


.. |1-mybinder| image:: /_static/badge-launch-binder.svg
   :target: https://mybinder.org/v2/gh/mammos-project/mammos/latest?urlpath=lab%2Ftree%2Fexamples%2Fhard-magnet-tutorial.ipynb
.. |1-mpcdf| image:: /_static/badge-launch-binder2.svg
   :target: https://notebooks.mpcdf.mpg.de/binder/v2/gl/mammos-project%2Fmammos/latest?urlpath=lab%2Ftree%2Fexamples%2Fhard-magnet-tutorial.ipynb
.. |2-mybinder| image:: /_static/badge-launch-binder.svg
   :target: https://mybinder.org/v2/gh/mammos-project/mammos/latest?urlpath=lab%2Ftree%2Fexamples%2Fhard-magnet-material-exploration.ipynb
.. |2-mpcdf| image:: /_static/badge-launch-binder2.svg
   :target: https://notebooks.mpcdf.mpg.de/binder/v2/gl/mammos-project%2Fmammos/latest?urlpath=lab%2Ftree%2Fexamples%2Fhard-magnet-material-exploration.ipynb
.. |3-mybinder| image:: /_static/badge-launch-binder.svg
   :target: https://mybinder.org/v2/gh/mammos-project/mammos/latest?urlpath=lab%2Ftree%2Fexamples%2Fsensor.ipynb
.. |3-mpcdf| image:: /_static/badge-launch-binder2.svg
   :target: https://notebooks.mpcdf.mpg.de/binder/v2/gl/mammos-project%2Fmammos/latest?urlpath=lab%2Ftree%2Fexamples%2Fsensor.ipynb
.. |4-mybinder| image:: /_static/badge-launch-binder.svg
   :target: https://mybinder.org/v2/gh/mammos-project/mammos/latest?urlpath=lab%2Ftree%2Fexamples%2Fhard-magnet-ai-surrogate-model.ipynb
.. |4-mpcdf| image:: /_static/badge-launch-binder2.svg
   :target: https://notebooks.mpcdf.mpg.de/binder/v2/gl/mammos-project%2Fmammos/latest?urlpath=lab%2Ftree%2Fexamples%2Fhard-magnet-ai-surrogate-model.ipynb
.. |5-mybinder| image:: /_static/badge-launch-binder.svg
   :target: https://mybinder.org/v2/gh/mammos-project/mammos/latest?urlpath=lab%2Ftree%2Fexamples%2Fspindynamics-temperature-dependent-parameters.ipynb
.. |5-mpcdf| image:: /_static/badge-launch-binder2.svg
   :target: https://notebooks.mpcdf.mpg.de/binder/v2/gl/mammos-project%2Fmammos/latest?urlpath=lab%2Ftree%2Fexamples%2Fspindynamics-temperature-dependent-parameters.ipynb
