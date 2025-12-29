import csv
import logging
from itertools import zip_longest
from pathlib import Path
from typing import Generator, Iterable, List

from pyramid.request import Request

from caerp.celery.interfaces import IAccountingFileParser
from caerp.celery.parsers import BaseParser, BaseProducer, OperationData
from caerp.compute.math_utils import str_to_float
from caerp.utils.datetimes import str_to_date

logger = logging.getLogger(__name__)


def split_list(lst, n=3):
    return zip_longest(*[iter(lst)] * n, fillvalue="")


class TxtFileParser(BaseParser):
    """
    Parse un fichier texte
    La partie contenant les écritures

    ECRITURES

        15/11/2021 BQ 512000 "1" "Apport capital social" D 6000,00 E  ( axe1 COOP00 )
        15/11/2021 BQ 101000 "2" "Apport capital social" C 6000,00 E  ( axe1 COOP00 )
        15/11/2021 BQ 101000 "2" "Apport capital social" C 6000,00 E  A ( axe1 COOP00 )
        ....

    """

    encoding = "iso8859-15"
    key_line = "ECRITURES"

    def _stream_operation_lines_from_file(self) -> Generator[str, None, None]:
        stream = False
        with open(self.file_path, "r", encoding=self.encoding) as fbuf:
            for line in fbuf.readlines():
                line = line.strip()
                if line.startswith("ECRITURES"):
                    stream = True
                elif stream and len(line) > 5:
                    yield line

    def stream(self) -> Generator[list, None, None]:
        for line in csv.reader(
            self._stream_operation_lines_from_file(),
            quotechar='"',
            delimiter=" ",
            skipinitialspace=True,
        ):
            yield line


class OperationProducer(BaseProducer):
    def _get_num_val(self, line: List[str], index: int) -> float:
        """
        Return the value of the given index in the given line in float format

        """
        result = 0
        if len(line) > index:
            result = line[index].strip() or 0

        return str_to_float(result, default=0.0)

    def _get_label(self, line: List[str]) -> str:
        label = line[4].strip()
        label = label[:80]
        return label

    def _get_analytical_accounts(self, line) -> List[dict]:
        """
        Collect analytical accounts from the given line

        Cas 1 :
        15/11/2021 BQ 101000 "2" "Apport capital social" C 6000,00 E  ( axe1 COOP00 )

        Cas 2 (cf le A en plus):
        15/11/2021 BQ 101000 "2" "Apport capital social" C 6000,00 E  A ( axe1 COOP00 )

        Cas 3
        15/11/2021 BQ 101000 "2" "TVA" C 6000,00 E  A ( axe1 COOP00 1000.0 axe1 COOP01 5000.0 )
        """
        # Join analytical related lines
        end_columns = " ".join(line[8:])
        if "(" in end_columns and ")" in end_columns:
            analytical_columns = [
                column
                for column in end_columns.split("(")[1].split(")")[0].split(" ")
                if column
            ]
        else:
            analytical_columns = []

        if analytical_columns.count("axe1") == 1:
            analytical_accounts = [{"account": analytical_columns[1].strip()}]
        elif analytical_columns.count("axe1") > 1:
            analytical_accounts = []
            for libelle, account, value in split_list(analytical_columns, 3):
                if account and value:
                    analytical_accounts.append(
                        {
                            "account": account.strip(),
                            "value": str_to_float(value.strip()),
                        }
                    )
        else:
            # Should not happen
            analytical_accounts = []
        return analytical_accounts

    def _stream_operation(self, line) -> Generator[OperationData, None, None]:
        print("Handling new line : %s" % line)
        if len(line) >= 12:
            analytical_accounts = self._get_analytical_accounts(line)

            general_account = line[2].strip()
            date = str_to_date(line[0].strip())
            if not date:
                logger.error("This line has incorrect datas : %s" % line)
                return None
            else:
                date = date.date()

            label = self._get_label(line)
            type_ = line[5]
            if type_ == "C":
                debit = 0
                credit = self._get_num_val(line, index=6)
            else:
                credit = 0
                debit = self._get_num_val(line, index=6)

            # Dans le cas où on a plusieurs axe sur la même ligne, on
            # splitte la ligne en plusieurs écritures analytiques
            for analytical_account_data in analytical_accounts:
                if "value" in analytical_account_data:
                    if credit == 0:
                        debit = analytical_account_data["value"]
                    else:
                        credit = analytical_account_data["value"]
                analytical_account = analytical_account_data["account"]
                balance = 0
                yield OperationData(
                    analytical_account=analytical_account,
                    general_account=general_account,
                    date=date,
                    label=label,
                    debit=debit,
                    credit=credit,
                    balance=balance,
                )

    def stream_operations(self) -> Iterable[OperationData]:
        for line in self.parser.stream():
            yield from self._stream_operation(line)


def parser_factory(context: Path, request: Request):
    return TxtFileParser(context)


def producer_factory(context: IAccountingFileParser, request: Request):
    return OperationProducer(context)
