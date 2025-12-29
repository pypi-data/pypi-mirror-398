"""
Exemple de fichier xlsx

.. code-block::

    Section analytique	Général	Auxiliaire	Date	Type	Journal	Libellé	Débit	Crédit	Solde
    006000	421000	421100	31/01/2022	A	512	juvenon	2090,43	0	2090,43
"""
import datetime
import logging
from pathlib import Path
from typing import Generator, Iterable, Optional

from openpyxl import load_workbook
from pyramid.request import Request

from caerp.celery.interfaces import IAccountingFileParser
from caerp.celery.parsers import BaseParser, BaseProducer, OperationData
from caerp.compute.math_utils import str_to_float
from caerp.utils import datetimes as date_utils

logger = logging.getLogger(__name__)


class CegidFileParser(BaseParser):
    def _stream_operation_lines_from_file(self) -> Generator[dict, None, None]:
        wb = load_workbook(self.file_path)
        ws = wb.active
        rows: Generator = ws.rows
        headers = [cell.value for cell in next(rows)]
        for row in rows:
            row_data = {}
            for num_col, header in enumerate(headers):
                row_data[header] = row[num_col].value
            yield row_data

    def stream(self) -> Generator[dict, None, None]:
        for line in self._stream_operation_lines_from_file():
            yield line


class OperationProducer(BaseProducer):
    _required_keys = (
        "Section analytique",
        "Général",
        "Date",
        "Libellé",
        "Débit",
        "Crédit",
        "Solde",
    )

    def _get_date(self, line):
        date = line.get("Date", "")
        if isinstance(date, datetime.datetime):
            return date.date()
        else:
            date = date.strip()
        date_and_time = date_utils.str_to_date(date)
        if date_and_time is not None:
            return date_and_time.date()
        return None

    def _get_label(self, line) -> str:
        return line.get("Libellé", "").strip()

    def _get_num_val(self, line: dict, key: str) -> float:
        val = line.get(key, 0)
        if isinstance(val, (int, float)):
            return val
        else:
            val = val.strip()
            return str_to_float(val, default=0)

    def _stream_operation(self, line) -> Optional[OperationData]:
        for key in self._required_keys:
            if key not in line.keys():
                logger.error("This line has incorrect datas : %s" % line)
                return None
        analytical_account = line.get("Section analytique", "")
        general_account = line.get("Général", "")
        date = self._get_date(line)
        if not date:
            logger.error("This line has incorrect date data : %s" % line)
            return None
        label = self._get_label(line)
        credit = self._get_num_val(line, key="Crédit")
        debit = self._get_num_val(line, key="Débit")
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
    return CegidFileParser(context)


def producer_factory(context: IAccountingFileParser, request: Request):
    return OperationProducer(context)
