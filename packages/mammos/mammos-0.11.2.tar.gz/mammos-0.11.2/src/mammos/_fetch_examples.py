"""Fetch examples (notebooks) for all mammos subpackages from github."""

import importlib
import re
from pathlib import Path

import requests


def url_from_template(repository: str, version: str, directory: str, file: str) -> str:
    """Create url to fetch single file."""
    return (
        f"https://raw.githubusercontent.com/MaMMoS-project/{repository}"
        f"/refs/tags/{version}/{directory}/{file}"
    )


def fetch_file(url: str) -> bytes:
    """Fetch from url and return content as bytes (encoded as utf-8)."""
    response = requests.get(url, timeout=5)
    if response.status_code != 200:
        msg = f"Fetching '{url}' failed:\n{response.text}"
        raise RuntimeError(msg)
    return response.content


# TODO should we replace this with docutils?
def parse_index_rst(content: str) -> list[str]:
    """Parse index.rst file and find content of first TOC (assuming they are notebooks).

    Expected file structure::

        Any amount of

        content::

           before the toc

        .. toc::
           :caption: Options will be ignored

           file1
           Custom titles are supported <file2>

        Anything after the first toc will be ignored.

    Args:
        content: Content of the index file. Split into lines at newline characters.

    Returns:
        List of notebook names in the form 'name.ipynb'.
    """
    notebooks = []
    toc_start = False
    for line in content.split("\n"):
        if not toc_start and not line.startswith(".. toctree::"):
            continue
        elif line.startswith(".. toctree::"):
            toc_start = True
            continue
        elif re.match(r"\s+:", line) or line == "":  # toctree option or empty line
            continue
        elif not re.match(r"\s+", line):
            # line does not start with whitespace -> end of toctree
            # TODO check for consistent indentation
            break

        # line contains a toc element, options:
        # - '   path/to/document'
        # - '   custom title <path/to/document>'

        # NOTEs:
        # - the special element 'self' is not treated correctly
        #   as we do not expect to find it in any of the files we will parse.
        # - absolute paths are not handled correctly
        if match := re.match(r"\s+.*<(.*)>", line):
            notebooks.append(f"{match.groups()[0]}.ipynb")
        else:
            notebooks.append(f"{line.strip()}.ipynb")

    return notebooks


def fetch_notebooks_for_repo(
    repository: str, version: str, repo_dir: str, base_dir: Path
) -> None:
    """Fetch all notebooks for a given repository and write them to output_dir.

    Notebooks are fetched based on the content of `index.rst` in `remode_dir` based
    on `URL_TEMPLATE`. Notebooks are written to a new sub directory `output_dir/repo`.
    An existing directory with the same name will lead to a failure.

    If no notebooks were found nothing is written to disk.
    """
    index_url = url_from_template(repository, version, repo_dir, "index.rst")
    index_file = fetch_file(index_url)

    notebooks = parse_index_rst(index_file.decode("utf-8"))

    if not notebooks:
        return

    output_dir = base_dir / repository
    output_dir.mkdir()

    for notebook in notebooks:
        notebook_url = url_from_template(repository, version, repo_dir, notebook)
        notebook_content = fetch_file(notebook_url)
        (output_dir / notebook).write_bytes(notebook_content)


def show_files(base_dir: Path) -> None:
    """Print a list of all notebooks in the base_dir subtree."""
    print("The following examples have been downloaded:")
    for notebook in sorted(base_dir.rglob("*.ipynb")):
        print(notebook)


def main():
    """Fetch examples for all repositories.

    At the time of writing this produces the following output::

        examples/
        ├── mammos
        │   ├── hard-magnet-material-exploration.ipynb
        │   ├── hard-magnet-tutorial.ipynb
        │   └── sensor.ipynb
        ├── mammos-analysis
        │   └── quickstart.ipynb
        ├── mammos-dft
        │   └── quickstart.ipynb
        ├── mammos-entity
        │   └── quickstart.ipynb
        ├── mammos-mumag
        │   └── quickstart.ipynb
        ├── mammos-spindynamics
        │   └── quickstart.ipynb
        └── mammos-units
            ├── example.ipynb
            └── quickstart.ipynb

    """
    base_dir = Path("examples")
    base_dir.mkdir()
    print("Downloading examples...")
    for package in [
        "mammos",
        "mammos-analysis",
        "mammos-dft",
        "mammos-entity",
        "mammos-mumag",
        "mammos-spindynamics",
        "mammos-units",
    ]:
        module = importlib.import_module(package.replace("-", "_"))
        fetch_notebooks_for_repo(package, module.__version__, "examples", base_dir)

    show_files(base_dir)
