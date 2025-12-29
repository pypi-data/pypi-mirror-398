import datetime
import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from caerp.celery.exception import FileNameException


@dataclass
class UploadMetaData:
    filename: str
    date: datetime.date
    filetype: str


@dataclass
class OperationData:
    analytical_account: str
    general_account: str
    date: datetime.date
    label: str
    debit: float
    credit: float
    balance: float


class BaseParser(ABC):
    filename_re = re.compile(
        "(?:general_ledger_)*(?P<year>[0-9]{4,4})_(?P<month>[0-9]{1,2})_(?P<doctype>[^.]+)",
        re.IGNORECASE,
    )

    def __init__(self, file_path: Path):
        self.file_path = file_path
        match = self.filename_re.match(self.file_path.name)
        if match is None:
            raise FileNameException(
                f"{self.file_path.name} devrait être de la forme "
                f"2022_01_grandlivre.extension ou "
                f"general_ledger_2022_01_grandlivre.extension"
            )
        else:
            self.date = datetime.date(int(match["year"]), int(match["month"]), 1)

    def metadata(self) -> UploadMetaData:
        """return Upload metadata"""
        return UploadMetaData(
            filename=self.file_path.name,
            date=self.date,
            filetype="general_ledger",
        )

    @abstractmethod
    def stream(self) -> Iterable[list]:
        """stream lines as list in the format expected by the associated producer"""
        pass


class BaseProducer(ABC):
    def __init__(self, parser: BaseParser):
        self.parser = parser

    @abstractmethod
    def stream_operations(self) -> Iterable[OperationData]:
        """
        Stream operation data used to store the accounting operations in the
        database
        """
        pass


def get_md5sum(file_path, blocksize=65536):
    """
    Return a md5 sum of the given file_path informations
    """
    hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(blocksize), b""):
            hash.update(block)
    return hash.hexdigest()
