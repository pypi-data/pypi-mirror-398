=========
Changelog
=========

The format follows `Keep a Changelog <https://keepachangelog.com/>`__. Versions
follow `semantic versioning <https://semver.org/>`__, the metapackage version is
updated according to the largest bump of any of the dependent packages.

..
   ADD NEW ENTRIES BELOW THIS COMMENT.


0.11.2 -- 2025-12-22
====================

Misc
----

``mammos``
  - Updated hard magnetic AI surrogate model notebook (`PR65 <https://github.com/MaMMoS-project/mammos/pull/65>`__), after upgrade of `mammos-analysis to version 0.4.0 <https://github.com/MaMMoS-project/mammos-analysis/tree/0.4.0>`__

Added
-----

``mammos-analysis``
  - ``extract_BHmax``: calculate BHmax based on M, H and demagnization_coefficient. This replaces ``extract_maximum_energy_product()`` which has the same purpose but a different user interface. (`PR53 <https://github.com/MaMMoS-project/mammos-analysis/pull/53>`__)

Removed
-------

``mammos-anylis``
  - ``extract_maximum_energy_product()``. Use ``extract_BHmax`` instead. (`PR53 <https://github.com/MaMMoS-project/mammos-analysis/pull/53>`__)


0.11.1 -- 2025-12-18
====================

Added
-----

``mammos``
  - Added micromagnetic simulation data to hard magnet AI example (and scripts to compute the data)
    (`PR62 <https://github.com/MaMMoS-project/mammos/pull/62>`__, `PR63 <https://github.com/MaMMoS-project/mammos/pull/63>`__)

Fixed
-----

``mammos``
  - Set the available number of ``OMP_NUM_THREADS`` to 1 in the spindynamics notebook. (`PR58 <https://github.com/MaMMoS-project/mammos/pull/58>`__)
  - Fixed binder links to AI spindynamics notebooks. (`PR59 <https://github.com/MaMMoS-project/mammos/pull/59>`__)

``mammos-spindynamics``
  - Indexing of ``TemperatureSweepData`` sub-runs. (`PR54 <https://github.com/MaMMoS-project/mammos-spindynamics/pull/54>`__)


   
0.11.0 -- 2025-12-17
====================

Added
-----

``mammos``
  - New demonstrator notebook: performing spindynamics simulations with UppASD
    to get temperature-dependent intrinsic properties.
    (`PR55 <https://github.com/MaMMoS-project/mammos/pull/55>`__)
``mammos-analysis``
  - Initial guesses for the Kuz'min fit are now allowed.
    (`PR50 <https://github.com/MaMMoS-project/mammos-analysis/pull/50>`__)
``mammos-spindynamics``
  - Python interface for UppASD.
    (`PR42 <https://github.com/MaMMoS-project/mammos-spindynamics/pull/42>`__,
    `PR43 <https://github.com/MaMMoS-project/mammos-spindynamics/pull/43>`__)

Changed
-------

``mammos``
  - Hard magnet demonstrator notebooks now use ``Fe2.33Ta0.67Y`` as default
    material. (`PR49 <https://github.com/MaMMoS-project/mammos/pull/49>`__)
``mammos-analysis``
  - Improved heuristics for the initial guess for the Kuz'min fit to make the
    fitting more robust. (`PR50 <https://github.com/MaMMoS-project/mammos-analysis/pull/50>`__)
``mammos-dft``
  - The values of posfiletype and maptype were added to the databases.
    (`PR43 <https://github.com/MaMMoS-project/mammos-dft/pull/43>`__)

0.10.0 -- 2025-12-15
====================

Added
-----

``mammos-dft``
  - A new function :py:func:`mammos_dft.db.get_uppasd_properties` to get inputs required for UppASD from the database. (`PR41 <https://github.com/MaMMoS-project/mammos-dft/pull/41>`__)


0.9.1 -- 2025-12-12
===================

Fixed
-----

``mammos-entity``
  - Fixed logic to establish ontology-preferred units. (`PR98 <https://github.com/MaMMoS-project/mammos-entity/pull/98>`__)
``mammos-spindynamics``
  - Fixed header of ``M.csv`` for Fe3Y and Fe2.33Ta0.67Y. (`PR45 <https://github.com/MaMMoS-project/mammos-spindynamics/pull/45>`__)


0.9.0 -- 2025-12-11
===================

New package ``mammos-ai`` added.

Added
-----

``mammos-ai``
  - A new AI model which can predict extrinsic magnetic properties (Hc, Mr, BHmax) from the
    intrinsic micromagnetic parameters Ms, A and K has been added. (`PR5 <https://github.com/MaMMoS-project/mammos-ai/pull/5>`__, `PR6 <https://github.com/MaMMoS-project/mammos-ai/pull/6>`__)


0.8.2 -- 2025-12-10
===================

Misc
----

``mammos``
  - Refactored Demonstrator page with examples from the ``mammos`` metapackage. (`PR46 <https://github.com/MaMMoS-project/mammos/pull/46>`__)
``mammos-dft``
  - Materials Fe3Y and Fe2.33Ta0.67Y were added to the database. (`PR39 <https://github.com/MaMMoS-project/mammos-dft/pull/39>`__)
``mammos-spindynamics``
  - Materials Fe3Y and Fe2.33Ta0.67Y were added to the database. (`PR41 <https://github.com/MaMMoS-project/mammos-spindynamics/pull/41>`__)


0.8.1 -- 2025-12-03
===================

Misc
----

``mammos-mumag``
  - Fixed dependencies: added `matplotlib`, `pandas`, and `urllib3`. (`PR93 <https://github.com/MaMMoS-project/mammos-mumag/pull/93>`__)
``mammos-spindynamics``
  - Fixed dependencies: added `numpy`. (`PR38 <https://github.com/MaMMoS-project/mammos-spindynamics/pull/38>`__)


0.8.0 -- 2025-11-27
===================

Added
-----

``mammos-analysis``
  - Added `celsius=True` option in the `plot` methods for the :py:mod:`mammos_analysis.kuzmin` module to generate plots in degree Celsius. (`PR40 <https://github.com/MaMMoS-project/mammos-analysis/pull/40>`__)
``mammos-mumag``
  - Added `tesla=True` option in the `plot` method of :py:class:`mammos_mumag.hysteresis.Result` to generate the hysteresis loop in Tesla units. (`PR87 <https://github.com/MaMMoS-project/mammos-mumag/pull/87>`__)


Changed
-------

``mammos_entity``
  - Improved :doc:`/examples/mammos-entity/io>` notebook. Use cases for working with :py:class:`~mammos_entity.io.EntityCollection` objects are added. (`PR83 <https://github.com/MaMMoS-project/mammos-entity/pull/83>`__)


Misc
----

``mammos-entity``
  - Fix dependencies: remove upper limit for `emmontopy` and add `pandas>2`. (`PR93 <https://github.com/MaMMoS-project/mammos-entity/pull/93>`__)


0.7.0 -- 2025-11-05
===================

Added
-----

``mammos-mumag``
  - Two new notebooks :doc:`/examples/mammos-mumag/hysteresis` and
    :doc:`/examples/mammos-mumag/additional-functionality` documenting
    additional functionality of ``mammos-mumag``. (`PR42
    <https://github.com/MaMMoS-project/mammos-mumag/pull/42>`__)
  - Create cli command ``unv2fly`` to convert unv mesh to fly format. (`PR61 <https://github.com/MaMMoS-project/mammos-mumag/pull/61>`__)
  - Added notebook :doc:`/examples/mammos-mumag/using_tesla` for information on how to set up a workflow in Tesla. (`PR68 <https://github.com/MaMMoS-project/mammos-mumag/pull/68>`__)
  - Added possibility to install GPU support (both CUDA and ROCm) with ``pip`` via the extra dependencies. (`PR81 <https://github.com/MaMMoS-project/mammos-mumag/pull/81>`__)

Fixed
-----

``mammos-analysis``
  - The function :py:func:`mammos_analysis.kuzmin_properties` will not assume the magnetization input is in ``A/m``. If the input is in a unit not convertible to ``A/m`` (e.g., Tesla), an error is raised. (`PR31 <https://github.com/MaMMoS-project/mammos-analysis/pull/31>`__)
``mammos-mumag``
  - Fixed default ``outdir`` input in two functions in :py:mod:`mammos_mumag.simulation`. (`PR69 <https://github.com/MaMMoS-project/mammos-mumag/pull/69>`__)


Changed
-------

``mammos-mumag``
  - Now :py:func:`mammos_mumag.hysteresis.run` can be used to execute simulations with multigrain materials. (`PR46 <https://github.com/MaMMoS-project/mammos-mumag/pull/46>`__)
  - Implement automatic retries to download meshes if the requests fail. The requests will try three times in total, with a backoff factor of 0.1. (`PR70 <https://github.com/MaMMoS-project/mammos-mumag/pull/70>`__)
  - Documentation is updated. Parameters have been formatted to snake case when possible. The names ``h_start``, ``h_final``, ``h_step``,  ``n_h_steps``, ``m_step``, ``m_final``, and ``tol_h_mag_factor`` take the place of ``hstart``, ``hfinal``, ``hstep``, ``nhsteps``, ``mstep``, ``mfinal``, and ``tol_hmag_factor``. Whenever possible, reasonable entities have been defined. The unused variables ``iter_max``, ``tol_u``, and ``verbose`` have been removed. **Warning**: this PR causes failure in previously defined workflows if the variables  were defined by the user. (`PR71 <https://github.com/MaMMoS-project/mammos-mumag/pull/71>`__)

Misc
----

``mammos-mumag``
  - Added :doc:`examples/mammos-mumag/hysteresis` to document full functionality of :py:mod:`mammos-mumag` when running a hysteresis loop simulation. Additionally, show the functionality of the package irrelevant to an average user in :doc:`examples/mammos-mumag/additional-functionality`. (`PR42 <https://github.com/MaMMoS-project/mammos-mumag/pull/42>`__)

0.6.0 -- 2025-08-13
===================

Added
-----

``mammos-entity``
  - CSV files written with :py:mod:`mammos_entity.io` can now optionally contain
    a description. (`PR52
    <https://github.com/MaMMoS-project/mammos-entity/pull/52>`__)
  - Support for YAML as additional file format in :py:mod:`mammos_entity.io`.
    (`PR59 <https://github.com/MaMMoS-project/mammos-entity/pull/59>`__, `PR69
    <https://github.com/MaMMoS-project/mammos-entity/pull/69>`__, `PR70
    <https://github.com/MaMMoS-project/mammos-entity/pull/70>`__)
  - Two new functions :py:func:`mammos_entity.io.entities_to_file` and
    :py:func:`mammos_entity.io.entities_from_file` to write and read entity
    files. The file type is inferred from the file extension. (`PR57
    <https://github.com/MaMMoS-project/mammos-entity/pull/57>`__)
  - A function :py:func:`mammos_entity.concat_flat` to concatenate compatible
    entities, quantities and array-likes into a single entity. (`PR56
    <https://github.com/MaMMoS-project/mammos-entity/pull/56>`__)
``mammos-mumag``
  - Add function :py:func:`mammos_mumag.hysteresis.read_result` to read the
    result of a hysteresis loop from a folder (without running the hysteresis
    calculation again). (`PR48
    <https://github.com/MaMMoS-project/mammos-mumag/pull/48>`__)
  - Implement :py:class:`mammos_mumag.mesh.Mesh` class that can read and display
    information of local meshes, meshes on Zenodo and meshes given by the user.
    (`PR53 <https://github.com/MaMMoS-project/mammos-mumag/pull/53>`__)

Changed
-------

``mammos-analysis``
  - The Kuz'min formula to evaluate micromagnetic properties can now accept
    Curie Temperature Tc and spontaneous magnetisation at zero temperature Ms_0
    as optional inputs. If given, they are not optimised by fitting the
    magnetisation curve. (`PR12
    <https://github.com/MaMMoS-project/mammos-analysis/pull/12>`__)
  - The initial guess for the optimization of the Curie Temperature in Kuz'min
    formula is set to a much lower temperature (depending on the data). (`PR18
    <https://github.com/MaMMoS-project/mammos-analysis/pull/18>`__)
``mammos-entity``
  - When reading files with :py:mod:`mammos_entity.io` IRIs are now checked in
    addition to ontology labels and file reading fails if there is a mismatch
    between IRI and ontology label. (`PR68
    <https://github.com/MaMMoS-project/mammos-entity/pull/68>`__)
``mammos-mumag``
  - Changed the output of the hysteresis loop in compliance with
    :py:mod:`mammos_entity.io` v2. (`PR54
    <https://github.com/MaMMoS-project/mammos-mumag/pull/54>`__)

Deprecated
----------

``mammos-entity``
  - The functions ``mammos.entity.io.entities_to_csv`` and
    ``mammos_entity.io.entities_from_csv`` have been deprecated. Use
    :py:func:`mammos_entity.io.entities_to_file` and
    :py:func:`mammos_entity.io.entities_from_file` instead. (`PR58
    <https://github.com/MaMMoS-project/mammos-entity/pull/58>`__)

Fixed
-----

``mammos-entity``
  - On Windows, CSV files written with mammos-entity had blank lines between all
    data lines. (`PR66
    <https://github.com/MaMMoS-project/mammos-entity/pull/66>`__)
  - Writing CSV files with entities of different shapes 0 and 1, where elements
    with shape 0 were broadcasted is no longer supported as it is not round-trip
    safe. (`PR67 <https://github.com/MaMMoS-project/mammos-entity/pull/67>`__)
``mammos-dft``
  - Update attribute name of uniaxial anisotropy constant to `Ku_0` from `K1_0`
    for the returned `MicromagneticProperties` object during a database lookup.
    (`PR19 <https://github.com/MaMMoS-project/mammos-dft/pull/19>`__)
``mammos-mumag``
  - Fixed the default values of the
    :py:class:`~mammos_mumag.materials.MaterialDomain` class. (`PR41
    <https://github.com/MaMMoS-project/mammos-mumag/pull/41>`__)

0.5.0 -- 2025-07-11
===================

Added
-----

``mammos-entity``
  - A new submodule :py:mod:`mammos_entity.io` that provides two functions to
    write and read CSV files with additional ontology metadata. For more details
    refer to the new :doc:`io documentation </examples/mammos-entity/io>`.
    (`PR29 <https://github.com/MaMMoS-project/mammos-entity/pull/29>`__, `PR46
    <https://github.com/MaMMoS-project/mammos-entity/pull/46>`__, `PR47
    <https://github.com/MaMMoS-project/mammos-entity/pull/47>`__ )

Fixed
-----

``mammos-entity``
  - Fix bug when defining unitless entities. (`PR37
    <https://github.com/MaMMoS-project/mammos-entity/pull/37>`__ and `PR45
    <https://github.com/MaMMoS-project/mammos-entity/pull/45>`__)

0.4.0 -- 2025-06-27
===================

Changed
-------

``mammos-entity``
  - The ``Entity`` class is no longer a subclass of ``mammos_units.Quantity``.
    As a consequence it does no longer support mathematical operations. Use the
    attribute ``.quantity`` (or the short-hand ``.q``) to access the underlying
    quantity and to perform (mathematical) operations. (`PR28
    <https://github.com/MaMMoS-project/mammos-entity/pull/28>`__)
  - The package now comes with a bundled ontology consisting of `EMMO
    <https://github.com/emmo-repo/EMMO>`__ (version 1.0.0-rc3) and `Magnetic
    Material <https://github.com/MaMMoS-project/MagneticMaterialsOntology>`__
    (version 0.0.3). Internet access is no longer required. (`PR33
    <https://github.com/MaMMoS-project/mammos-entity/pull/33>`__)
``mammos``
  - Use Fe16N2 instead of Nd2Fe14B in hard magnet workflow. (`PR17
    <https://github.com/MaMMoS-project/mammos/pull/17>`__)

0.3.0 -- 2025-06-11
===================

Added
-----

``mammos-entity``
  - New predefined entity ``mammos_entity.J``
  - New predefined entity ``mammos_entity.Js``
``mammos-mumag``
  - Optional argument ``plotter`` in ``plot_configuration`` to add a vector plot
    of a magnetization configuration to a :py:class:`pyvista.Plotter` provided
    by the caller.

Changed
-------

``mammos-entity``
  - Return a ``mammos_units.UnitConversionError`` (inherited from
    ``astropy.units``) when trying initialize an entity with incompatible units.

0.2.0 -- 2025-06-06
===================

Added
-----

``mammos``
  - Command-line script ``mammos-fetch-examples`` to download all example
    notebooks.
``mammos-entity``
  - Entity objects have ``ontology_label_with_iri`` attribute.

Changed
-------

``mammos-entity``
  - When trying to initialize an entity with a wrong unit the error message does
    now show the required unit defined in the ontology.

Fixed
-----

``mammos-entity``
  - ``Entity.to`` did not return a new entity in the requested units and instead
    used the default entity units.
  - ``Entity.axis_label``: unit inside parentheses instead of brackets.

0.1.0 -- 2025-06-05
===================

Added
-----

``mammos`` -- 0.1.0
  - Workflows for hard magnets and sensor shape optimization.
  - Ensures compatible software components are installed.
``mammos-analysis`` -- 0.1.0
  - Calculation of macroscopic properties (Mr, Hc, BHmax) from a hysteresis
    loop.
  - Fitting of the linear segment of a hysteresis loop.
  - Calculation of temperature-dependent micromagnetic properties from atomistic
    spin dynamics simulations using Kuz’min equations.
``mammos-dft`` -- 0.3.0
  - Database lookup functionality for a selection of pre-computed materials.
``mammos-entity`` -- 0.5.0
  - Provides entities: quantities with links to the MaMMoS ontology (based on
    EMMO) by combining ``mammos-units`` and `EMMOntoPy
    <https://github.com/emmo-repo/EMMOntoPy>`__.
  - Helper functions to simplify creation of commonly required magnetic entities.
``mammos-mumag`` -- 0.6.0
  - Finite-element hysteresis loop calculations.
  - Requires a separate installation of `esys-escript
    <https://github.com/LutzGross/esys-escript.github.io/>`__.
``mammos-spindynamics`` -- 0.2.0
  - Database lookup functionality for a selection of pre-computed materials.
``mammos-units`` -- 0.3.1
  - Extension of astropy.units that allows working with quantities (units with
    values) containing additional units relevant for magnetism.
