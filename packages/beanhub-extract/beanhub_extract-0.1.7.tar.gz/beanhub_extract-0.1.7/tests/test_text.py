import pathlib

import pytest

from beanhub_extract.text import as_text


@pytest.mark.parametrize("encoding", ["utf8", "utf16", "cp950"])
def test_as_text_with_binary_file(tmp_path: pathlib.Path, encoding: str):
    bin_file = tmp_path / "bin.txt"
    text = "hello there, 你好"
    bin_file.write_text(text, encoding=encoding)

    with bin_file.open("rb") as fo:
        with as_text(fo, encoding=encoding) as text_file:
            assert text_file.read() == text
        # ensure that the file is not closed
        fo.seek(0)
        assert fo.read() == text.encode(encoding)


@pytest.mark.parametrize("encoding", ["utf8", "utf16", "cp950"])
def test_as_text_with_text_file(tmp_path: pathlib.Path, encoding: str):
    bin_file = tmp_path / "bin.txt"
    text = "hello there, 你好"
    bin_file.write_text(text, encoding=encoding)

    with bin_file.open("rt", encoding=encoding) as fo:
        with as_text(fo) as text_file:
            assert text_file.read() == text
        # ensure that the file is not closed
        fo.seek(0)
        assert fo.read() == text
