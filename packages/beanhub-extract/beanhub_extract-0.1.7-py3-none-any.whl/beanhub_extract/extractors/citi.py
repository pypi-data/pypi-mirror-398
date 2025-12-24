import csv
import datetime
import decimal
import hashlib
import typing

from ..data_types import Fingerprint
from ..data_types import Transaction
from ..text import as_text
from .base import ExtractorBase


def parse_date(date_str: str) -> datetime.date:
    parts = date_str.split("/")
    return datetime.date(int(parts[-1]), *(map(int, parts[:-1])))


def parse_to_decimal(number_str: str) -> decimal.Decimal:
    try:
        return decimal.Decimal(number_str)
    except (ValueError, decimal.InvalidOperation):
        pass

    return decimal.Decimal("0.0")


class CitiCreditCardExtractor(ExtractorBase):
    EXTRACTOR_NAME = "citi_credit_card"
    DEFAULT_IMPORT_ID = "{{ file | as_posix_path }}:{{ reversed_lineno }}"
    ALL_FIELDS = ["Status", "Date", "Description", "Debit", "Credit", "Member Name"]

    def detect(self) -> bool:
        with as_text(self.input_file) as text_file:
            reader = csv.DictReader(text_file)
            try:
                return reader.fieldnames == self.ALL_FIELDS
            except Exception:
                return False

    def fingerprint(self) -> Fingerprint | None:
        with as_text(self.input_file) as text_file:
            reader = csv.DictReader(text_file)
            try:
                row = next(reader)
            except StopIteration:
                return

            hash = hashlib.sha256()
            for field in reader.fieldnames:
                hash.update(row[field].encode("utf8"))

            date_value = parse_date(row["Date"])
            if not date_value:
                date_value = datetime.date(1970, 1, 1)
            return Fingerprint(
                starting_date=date_value,
                first_row_hash=hash.hexdigest(),
            )

    def __call__(self) -> typing.Generator[Transaction, None, None]:
        filename = None
        if hasattr(self.input_file, "name"):
            filename = self.input_file.name
        with as_text(self.input_file) as text_file:
            row_count_reader = csv.DictReader(text_file)
            row_count = 0
            for _ in row_count_reader:
                row_count += 1
            text_file.seek(0)
            reader = csv.DictReader(text_file)
            for i, row in enumerate(reader):
                # amount
                credit = parse_to_decimal(row.pop("Credit").strip())
                debit = parse_to_decimal(row.pop("Debit").strip())
                amount = debit + credit

                # desc
                member = row.pop("Member Name").strip()
                desc = row.pop("Description").strip()
                if member:
                    desc = f"{desc} ({member})"

                # date
                date = row.pop("Date")

                kwargs = dict(
                    status=row.pop("Status"),
                    date=parse_date(date),
                    post_date=parse_date(date),
                    desc=desc,
                    amount=amount,
                )
                if row:
                    kwargs["extra"] = row

                yield Transaction(
                    extractor=self.EXTRACTOR_NAME,
                    file=filename,
                    lineno=i + 1,
                    reversed_lineno=i - row_count,
                    **kwargs,
                )
