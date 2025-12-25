import os
import textwrap
from pathlib import Path

import pytest

from mammos import _fetch_examples as fetch_examples


def test_fetch_file():
    url = fetch_examples.url_from_template(
        repository="mammos", version="0.1.0", directory="examples", file="index.rst"
    )
    index_file = fetch_examples.fetch_file(url)
    assert index_file.startswith(b"mammos\n======")


def test_fetch_file_wrong():
    url = fetch_examples.url_from_template(
        repository="mammos",
        version="0.1.0",
        directory="not-examples",
        file="non-existent",
    )
    with pytest.raises(RuntimeError):
        fetch_examples.fetch_file(url)


def test_parse_index_rst():
    content = textwrap.dedent(
        """\
        Our content
        ===========

        .. toctree::
           :caption: Example

           notebook1
           Advanced usage <notebook2>
           notebook3

        That's all, the next toc will NOT be read.

        .. toctree::
           :caption: Other examples

           This will not be read <other_notebook>
        """
    )
    notebooks = fetch_examples.parse_index_rst(content)
    assert notebooks == ["notebook1.ipynb", "notebook2.ipynb", "notebook3.ipynb"]


def test_parse_index_rst_no_toc():
    content = ""
    assert fetch_examples.parse_index_rst(content) == []

    content = textwrap.dedent(
        """\
        Some file
        =========

        This file does not contain a .. toctree:: directive which we can::

           parse.
        """
    )
    assert fetch_examples.parse_index_rst(content) == []


def test_fech_notebooks_for_mammos(tmp_path):
    fetch_examples.fetch_notebooks_for_repo("mammos", "0.1.0", "examples", tmp_path)
    for notebook in [
        "hard-magnet-material-exploration.ipynb",
        "hard-magnet-tutorial.ipynb",
        "sensor.ipynb",
    ]:
        assert (tmp_path / "mammos" / notebook).exists()


def test_main(tmp_path, capsys):
    os.chdir(tmp_path)
    fetch_examples.main()

    assert (tmp_path / "examples" / "mammos").exists()
    assert (tmp_path / "examples" / "mammos-analysis").exists()

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out.startswith("Downloading examples...")
    assert str(Path("examples/mammos-analysis/quickstart.ipynb")) in captured.out
