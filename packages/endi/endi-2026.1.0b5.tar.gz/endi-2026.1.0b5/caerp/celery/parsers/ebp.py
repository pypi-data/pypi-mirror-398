import csv
import datetime
import logging
from pathlib import Path
from typing import Generator, Iterable, List, Optional

from pyramid.request import Request

from caerp.celery.interfaces import IAccountingFileParser
from caerp.celery.parsers import BaseParser, BaseProducer, OperationData
from caerp.compute.math_utils import str_to_float
from caerp.utils import datetimes as date_utils

logger = logging.getLogger(__name__)


class CsvFileParser(BaseParser):
    encoding = "iso-8859-15"

    def stream(self) -> Generator[list, None, None]:
        with open(self.file_path, encoding=self.encoding) as fbuf:
            for line in csv.reader(fbuf, quotechar='"', delimiter=","):
                yield line


class OperationProducer(BaseProducer):
    """
    Exemple de contenu :

    Poste analytique,N° de compte,Date,Libellé,Débit,Crédit
    "PP0000","44566100","13/01/2023","TELECOM","5,62000000","0"
    """

    def _get_num_val(self, line: List[str], index: int) -> float:
        result = 0
        if len(line) > index:
            result = line[index].strip() or 0
        return str_to_float(result, 0)

    def _get_label(self, line: List[str]) -> str:
        label = line[3].strip()
        label = label[:80]
        return label

    def _get_date(self, line) -> Optional[datetime.date]:
        date = None
        date_str = line[2].strip()
        if date_str:
            try:
                date = date_utils.str_to_date(line[2].strip()).date()
            except Exception:
                logger.error("This line has incorrect datas : %s" % line)
                date = None
        return date

    def _stream_operation(self, line) -> Optional[OperationData]:
        """
        Analyticial/General/date/.../.../label/débit/crédit
        """
        result = None
        if len(line) >= 4:
            first_cell = line[0].strip()
            if first_cell and "analytique" not in first_cell.lower():
                analytical_account = first_cell
                general_account = line[1].strip()
                date = date_utils.str_to_date(line[2].strip()).date()
                if not date:
                    return None

                label = self._get_label(line)
                debit = self._get_num_val(line, index=4)
                credit = self._get_num_val(line, index=5)
                balance = 0
                result = OperationData(
                    analytical_account=analytical_account,
                    general_account=general_account,
                    date=date,
                    label=label,
                    debit=debit,
                    credit=credit,
                    balance=balance,
                )
        return result

    def stream_operations(self) -> Iterable[OperationData]:
        for line in self.parser.stream():
            data = self._stream_operation(line)
            if data is not None:
                yield data


def parser_factory(context: Path, request: Request):
    return CsvFileParser(context)


def producer_factory(context: IAccountingFileParser, request: Request):
    return OperationProducer(context)
