# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?= --color
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

prepare:
	mkdir -p packages
	for PKG in mammos-analysis mammos-dft mammos-entity mammos-mumag mammos-spindynamics mammos-units ; do \
		git clone --branch latest --depth 1 "https://github.com/mammos-project/$$PKG.git" packages/$$PKG || (cd packages/$$PKG && git pull --rebase) ;\
		rsync -a packages/$$PKG/examples/ source/examples/$$PKG ;\
	done
	rsync -a ../examples/ source/demonstrator/

prepare-local:
	for PKG in mammos-analysis mammos-dft mammos-entity mammos-mumag mammos-spindynamics mammos-units ; do \
		rsync -a ../../$$PKG/examples/ source/examples/$$PKG;\
	done
	rsync -a ../examples/ source/demonstrator/

clean:
	rm -rf build packages source/api/mammos* source/demonstrator source/examples/mammos*

.PHONY: help prepare clean Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
