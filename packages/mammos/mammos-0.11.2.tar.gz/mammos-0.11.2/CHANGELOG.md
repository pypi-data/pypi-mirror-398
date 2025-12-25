# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This project uses [towncrier](https://towncrier.readthedocs.io/) and the changes for the upcoming release can be found in [changes](changes).

<!-- towncrier release notes start -->

## [mammos 0.11.2](https://github.com/MaMMoS-project/mammos/tree/0.11.2) – 2025-12-22

### Misc

- Updated hard magnetic AI surrogate model notebook ([#65](https://github.com/MaMMoS-project/mammos/pull/65))


## [mammos 0.11.1](https://github.com/MaMMoS-project/mammos/tree/0.11.1) – 2025-12-19

### Added

- Added micromagnetic simulation data to hard magnet AI example (and scripts to compute the data) ([#63](https://github.com/MaMMoS-project/mammos/pull/63))

### Fixed

- Set the available number of `OMP_NUM_THREADS` to 1 in the spindynamics notebook. ([#58](https://github.com/MaMMoS-project/mammos/pull/58))
- Fixed binder links to AI an spindynamics notebooks. ([#59](https://github.com/MaMMoS-project/mammos/pull/59))

### Misc

- Reviewed hard magnet AI surrogate model example. ([#62](https://github.com/MaMMoS-project/mammos/pull/62))


## [mammos 0.11.0](https://github.com/MaMMoS-project/mammos/tree/0.11.0) – 2025-12-17

### Added

- New demonstrator notebook: performing spindynamics simulations with UppASD to get temperature-dependent intrinsic properties. ([#55](https://github.com/MaMMoS-project/mammos/pull/55))

### Changed

- Hard magnet demonstrator notebooks now use `Fe2.33Ta0.67Y` as default material. ([#49](https://github.com/MaMMoS-project/mammos/pull/49))


## [mammos 0.10.0](https://github.com/MaMMoS-project/mammos/tree/0.10.0) – 2025-12-15

No significant changes.


## [mammos 0.9.1](https://github.com/MaMMoS-project/mammos/tree/0.9.1) – 2025-12-12

No significant changes.


## [mammos 0.9.0](https://github.com/MaMMoS-project/mammos/tree/0.9.0) – 2025-12-11

### Added

- Included demonstrator notebook for AI surrogate model for hard magnets. ([#47](https://github.com/MaMMoS-project/mammos/pull/47))


## [mammos 0.8.2](https://github.com/MaMMoS-project/mammos/tree/0.8.2) – 2025-12-10

### Misc

- Refactored Demonstrator page with examples from the `mammos` metapackage. ([#46](https://github.com/MaMMoS-project/mammos/pull/46))


## [mammos 0.8.1](https://github.com/MaMMoS-project/mammos/tree/0.8.1) – 2025-12-03

No significant changes.


## [mammos 0.8.0](https://github.com/MaMMoS-project/mammos/tree/0.8.0) – 2025-11-27

### Fixed

- Typos fixed in Hard magnet tutorial notebook. ([#45](https://github.com/MaMMoS-project/mammos/pull/45))


## [mammos 0.7.0](https://github.com/MaMMoS-project/mammos/tree/0.7.0) – 2025-11-05

No significant changes.


## [mammos 0.6.0](https://github.com/MaMMoS-project/mammos/tree/0.6.0) – 2025-08-13

### Misc

- Use [towncrier](https://towncrier.readthedocs.io) to generate changelog from fragments. Each new PR must include a changelog fragment. ([#33](https://github.com/MaMMoS-project/mammos/pull/33))
