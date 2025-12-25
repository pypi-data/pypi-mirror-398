Source code to create overview diagram.

We use plantuml.

The source is in [diagram.puml](overview.puml).

To compile it to a bitmap, we have [Makefile](Makefile).

Requirements:

- plantuml
  - on MacOS: install via brew works fine (PlantUML version 1.2025.3)
  
  - install via pixi (i.e. conda-forge) also works sometimes for exporting png
    (but not for exporting eps). Seems a bit random.

- `make` if MAkefile is to be used.
- `epstopdf` if conversion to pdf is needed.

