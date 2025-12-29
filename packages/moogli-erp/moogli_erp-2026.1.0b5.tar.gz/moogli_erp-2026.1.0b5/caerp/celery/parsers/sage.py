import csv
import datetime
import logging
from pathlib import Path
from typing import Generator, Iterable, List, Optional

from pyramid.request import Request
from sylk_parser import SylkParser

from caerp.celery.interfaces import IAccountingFileParser
from caerp.celery.parsers import BaseParser, BaseProducer, OperationData
from caerp.compute.math_utils import str_to_float
from caerp.utils.datetimes import str_to_date

logger = logging.getLogger(__name__)


class SlkFileParser(BaseParser):
    def stream(self) -> Generator[list, None, None]:
        for line in SylkParser(str(self.file_path)):
            yield line


class CsvFileParser(BaseParser):
    encoding = "utf-8"

    def stream(self) -> Generator[list, None, None]:
        with open(self.file_path, encoding=self.encoding) as fbuf:
            dialect = csv.Sniffer().sniff(fbuf.read())
            fbuf.seek(0)
            for line in csv.reader(fbuf, dialect):
                yield line


class OperationProducer(BaseProducer):
    def _get_num_val(self, line: List[str], index: int) -> float:
        result = 0
        if len(line) > index:
            result = line[index].strip() or 0
        return str_to_float(result)

    def _get_label(self, line: List[str]) -> str:
        label = line[5].strip()
        label = label[:80]
        return label

    def _get_date(self, line) -> Optional[datetime.date]:
        date = None
        date_str = line[2].strip()
        if date_str:
            try:
                date = str_to_date(line[2].strip()).date()
            except Exception:
                logger.error("This line has incorrect datas : %s" % line)
                date = None
        return date

    def _stream_operation(self, line) -> Optional[OperationData]:
        """
        Analyticial/General/date/.../.../label/débit/crédit
        """
        result = None
        if len(line) >= 6:
            if line[0].strip() not in (
                "Compte analytique de l'entrepreneur",
                "Numéro analytique",
                " analytique",
                "",
            ):
                analytical_account = line[0].strip()
                general_account = line[1].strip()
                date = str_to_date(line[2].strip()).date()
                if not date:
                    return None

                label = self._get_label(line)
                debit = self._get_num_val(line, index=6)
                credit = self._get_num_val(line, index=7)
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
    if context.suffix == ".slk":
        return SlkFileParser(context)
    elif context.suffix == ".csv":
        return CsvFileParser(context)


def producer_factory(context: IAccountingFileParser, request: Request):
    return OperationProducer(context)
