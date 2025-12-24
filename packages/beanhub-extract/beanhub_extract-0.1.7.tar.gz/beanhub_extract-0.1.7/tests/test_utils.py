import datetime
import pathlib

import pytest

from beanhub_extract.data_types import Transaction
from beanhub_extract.utils import parse_date
from beanhub_extract.utils import strip_base_path
from beanhub_extract.utils import strip_txn_base_path


@pytest.mark.parametrize(
    "base_path, input_path, expected",
    [
        ("/path/to/", "/path/to/nested/my-file.csv", "nested/my-file.csv"),
    ],
)
def test_strip_base_path(base_path: str, input_path: str, expected: str):
    assert (
        strip_base_path(
            pathlib.PurePosixPath(base_path), pathlib.PurePosixPath(input_path)
        )
        == expected
    )


@pytest.mark.parametrize(
    "base_path, txn, expected",
    [
        (
            "/path/to/",
            Transaction(extractor="", file="/path/to/nested/my-file.csv"),
            Transaction(extractor="", file="nested/my-file.csv"),
        ),
    ],
)
def test_strip_txn_base_path(base_path: str, txn: Transaction, expected: Transaction):
    assert (
        strip_txn_base_path(pathlib.PurePosixPath(base_path), txn, pure_posix=True)
        == expected
    )


@pytest.mark.parametrize(
    "date_str, expected",
    [
        ("2024-05-04", datetime.date(2024, 5, 4)),
    ],
)
def test_parse_date(date_str: str, expected: datetime.date):
    assert parse_date(date_str) == expected
