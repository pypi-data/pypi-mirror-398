import datetime
import logging
from pathlib import Path
from typing import Generator, Iterable, Optional

from openpyxl import load_workbook
from pyramid.request import Request

from caerp.celery.interfaces import IAccountingFileParser
from caerp.celery.parsers import BaseParser, BaseProducer, OperationData
from caerp.compute.math_utils import str_to_float, str_to_int
from caerp.utils.datetimes import str_to_date

logger = logging.getLogger(__name__)


class QuadraFileParser(BaseParser):
    """
    Parse un fichier xlsx extrait de quadra
    """

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
    def _get_num_val(self, line: dict, key: str) -> float:
        result = 0
        val = line.get(key, 0)
        result = val or 0
        if not isinstance(result, (float, int)):
            result = str_to_float(result, default=0)
        return result

    def _get_label(self, line: dict) -> str:
        label = line.get("Libellé", "").strip()
        label = label[:80]
        return label

    def _get_date(self, line: dict) -> datetime.date:
        day = str_to_int(line.get("Jour", "0"), default=0)
        date = str_to_date(line.get("Période", "").strip()).date()
        return datetime.date(year=date.year, month=date.month, day=day)

    def _stream_operation(self, line) -> Optional[OperationData]:
        for key in ("CentreSimple", "Compte", "Débit", "Libellé", "Crédit", "Période"):
            if key not in line.keys():
                logger.error("This line has incorrect datas : %s" % line)
                return None
        analytical_account = line.get("CentreSimple", "").strip()
        general_account = line.get("Compte", "").strip()
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
    return QuadraFileParser(context)


def producer_factory(context: IAccountingFileParser, request: Request):
    return OperationProducer(context)
