import datetime
import decimal
import functools
import pathlib

import pytest

from beanhub_extract.data_types import Fingerprint
from beanhub_extract.data_types import Transaction
from beanhub_extract.extractors.citi import CitiCreditCardExtractor
from beanhub_extract.extractors.citi import parse_date
from beanhub_extract.utils import strip_txn_base_path as strip_txn


@pytest.mark.parametrize(
    "date_str, expected",
    [
        ("11/22/2025", datetime.date(2025, 11, 22)),
    ],
)
def test_parse_date(date_str: str, expected: datetime.date):
    assert parse_date(date_str) == expected


@pytest.mark.parametrize(
    "input_file, expected",
    [
        (
            "citi.csv",
            [
                Transaction(
                    extractor="citi_credit_card",
                    file="citi.csv",
                    lineno=1,
                    reversed_lineno=-8,
                    date=datetime.date(2025, 11, 23),
                    post_date=datetime.date(2025, 11, 23),
                    desc="LAKE ARROWHEAD RESORT FB 999-2223311 CA (PERSON NAME)",
                    amount=decimal.Decimal("115.00"),
                    status="Cleared",
                ),
                Transaction(
                    extractor="citi_credit_card",
                    file="citi.csv",
                    lineno=2,
                    reversed_lineno=-7,
                    date=datetime.date(2025, 11, 23),
                    post_date=datetime.date(2025, 11, 23),
                    desc="TST*ITS A GRIND MURRIETA MURRIETA CA (ANOTHER PERSON)",
                    amount=decimal.Decimal("7.70"),
                    status="Cleared",
                ),
                Transaction(
                    extractor="citi_credit_card",
                    file="citi.csv",
                    lineno=3,
                    reversed_lineno=-6,
                    date=datetime.date(2025, 11, 23),
                    post_date=datetime.date(2025, 11, 23),
                    desc="STARBUCKS STORE 2450A (PERSON NAME)",
                    amount=decimal.Decimal("37.30"),
                    status="Cleared",
                ),
                Transaction(
                    extractor="citi_credit_card",
                    file="citi.csv",
                    lineno=4,
                    reversed_lineno=-5,
                    date=datetime.date(2025, 11, 23),
                    post_date=datetime.date(2025, 11, 23),
                    desc="TESLA SUPERCHARGER US 877-123456 CA (ANOTHER PERSON)",
                    amount=decimal.Decimal("18.44"),
                    status="Cleared",
                ),
                Transaction(
                    extractor="citi_credit_card",
                    file="citi.csv",
                    lineno=5,
                    reversed_lineno=-4,
                    date=datetime.date(2025, 11, 23),
                    post_date=datetime.date(2025, 11, 23),
                    desc="TESLA SUPERCHARGER US 877-123456 CA (PERSON NAME)",
                    amount=decimal.Decimal("18.67"),
                    status="Cleared",
                ),
                Transaction(
                    extractor="citi_credit_card",
                    file="citi.csv",
                    lineno=6,
                    reversed_lineno=-3,
                    date=datetime.date(2025, 11, 22),
                    post_date=datetime.date(2025, 11, 22),
                    desc="ONLINE PAYMENT, THANK YOU (PERSON NAME)",
                    amount=decimal.Decimal("-3748.66"),
                    status="Cleared",
                ),
                Transaction(
                    extractor="citi_credit_card",
                    file="citi.csv",
                    lineno=7,
                    reversed_lineno=-2,
                    date=datetime.date(2025, 11, 22),
                    post_date=datetime.date(2025, 11, 22),
                    desc="TRADER JOE S #223 SAN DIEGO CA (PERSON NAME)",
                    amount=decimal.Decimal("5.98"),
                    status="Cleared",
                ),
                Transaction(
                    extractor="citi_credit_card",
                    file="citi.csv",
                    lineno=8,
                    reversed_lineno=-1,
                    date=datetime.date(2025, 11, 22),
                    post_date=datetime.date(2025, 11, 22),
                    desc="PETCO 0928 CA (PERSON NAME)",
                    amount=decimal.Decimal("39.85"),
                    status="Cleared",
                ),
            ],
        ),
    ],
)
def test_citi_extractor(
    fixtures_folder: pathlib.Path, input_file: str, expected: list[Transaction]
):
    with open(fixtures_folder / input_file, "rt") as fo:
        extractor = CitiCreditCardExtractor(fo)
        assert (
            list(map(functools.partial(strip_txn, fixtures_folder), extractor()))
            == expected
        )


@pytest.mark.parametrize(
    "input_file, expected",
    [
        ("citi.csv", True),
        ("mercury.csv", False),
        ("empty.csv", False),
        ("other.csv", False),
        (pytest.lazy_fixture("zip_file"), False),
    ],
)
def test_citi_detect(fixtures_folder: pathlib.Path, input_file: str, expected: bool):
    with open(fixtures_folder / input_file, "rt") as fo:
        extractor = CitiCreditCardExtractor(fo)
        assert extractor.detect() == expected


def test_citi_fingerprint(fixtures_folder: pathlib.Path):
    with open(fixtures_folder / "citi.csv", "rt") as fo:
        extractor = CitiCreditCardExtractor(fo)
        assert extractor.fingerprint() == Fingerprint(
            starting_date=datetime.date(2025, 11, 23),
            first_row_hash="f99f0003cdc10ce36058c12212d7739ae5b035cf8b9d72c685da9cb8e40fef96",
        )
