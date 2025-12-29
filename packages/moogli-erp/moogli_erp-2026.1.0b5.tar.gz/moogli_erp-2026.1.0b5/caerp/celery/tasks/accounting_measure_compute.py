"""
Tasks used to compile treasury measures
"""
import datetime
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import List, Optional, Tuple, Type

import transaction
from dateutil.relativedelta import relativedelta
from pyramid_celery import celery_app
from sqlalchemy import desc, extract, func, or_

from caerp.celery.conf import get_recipients_addresses, get_request
from caerp.celery.locks import acquire_lock, is_locked, release_lock
from caerp.celery.tasks import utils
from caerp.models.accounting.accounting_closures import AccountingClosure
from caerp.models.accounting.balance_sheet_measures import (
    ActiveBalanceSheetMeasureType,
    BalanceSheetMeasure,
    BalanceSheetMeasureGrid,
    BalanceSheetMeasureType,
    PassiveBalanceSheetMeasureType,
)
from caerp.models.accounting.base import (
    BaseAccountingMeasure,
    BaseAccountingMeasureGrid,
    BaseAccountingMeasureType,
    BaseAccountingMeasureTypeCategory,
)
from caerp.models.accounting.income_statement_measures import (
    IncomeStatementMeasure,
    IncomeStatementMeasureGrid,
    IncomeStatementMeasureType,
    IncomeStatementMeasureTypeCategory,
)
from caerp.models.accounting.operations import (
    AccountingOperation,
    AccountingOperationUpload,
)
from caerp.models.accounting.treasury_measures import (
    TreasuryMeasure,
    TreasuryMeasureGrid,
    TreasuryMeasureType,
    TreasuryMeasureTypeCategory,
)
from caerp.models.base import DBSESSION
from caerp.models.config import Config
from caerp.utils.mail import send_mail

logger = utils.get_logger(__name__)


class GridCacheItem:
    """
    Wraps a grid in cache and provide storages for

    measures
    total value by measure_type
    total value by measure type category
    """

    def __init__(self, grid):
        self.grid = grid
        self._category_totals = {}
        self._type_totals = {}
        self._measures = {}

    def clean_old_measures(self, type_ids):
        """
        Clean old measures

        Set them to  or remove them if theire type is not in the type list

        :param list type_ids: List of ids (int)
        :returns: The list of measures to remove
        """
        old_measures = [
            measure
            for measure in self.grid.measures
            if measure.measure_type_id not in type_ids
        ]
        self.grid.measures = [
            measure
            for measure in self.grid.measures
            if measure.measure_type_id in type_ids
        ]

        for measure in self.grid.measures:
            measure.value = 0
            self._measures[measure.measure_type_id] = measure
        return old_measures

    def get_measures(self):
        """
        Collect all existing measures (newly created or already existing)
        """
        return self._measures

    def store_measure(self, measure):
        """
        Store a measure in the measure cache

        :param obj measure: A child of BaseTreasuryMeasure
        """
        self._measures[measure.measure_type_id] = measure
        if measure not in self.grid.measures:
            self.grid.measures.append(measure)

    def set_total_type(self, measure):
        """
        Store the total value for a given measure type in the grid's cache

        :param obj measure: A child of BaseTreasuryMeasure
        """
        self._type_totals[measure.measure_type_id] = measure.value

    def update_category_total(self, measure):
        """
        Update the category total value for a given measure type in the grid's
        cache

        :param obj measure: A child of BaseTreasuryMeasure
        """
        measure_type = measure.measure_type
        if not measure_type.is_computed_total:
            if measure_type.category_id not in self._category_totals:
                self._category_totals[measure_type.category_id] = 0
            self._category_totals[measure_type.category_id] += measure.value

    def get_type_total(self, typ_id):
        """
        Get the total type for a given measure type

        :param int typ_id: The id of the measure type
        """
        return self._type_totals.get(typ_id, 0)

    def get_category_total(self, category_id):
        """
        Get the category total for a given measure type category

        :param int category_id: The id of the category
        """
        return self._category_totals.get(category_id, 0)


class GridCache:
    """
    A grid cache used to temporarly store all datas related to the current
    computation

    Eache item is an Accounting Measure Grid wraped with the GridCacheItem
    object
    """

    def __init__(self):
        self._datas = {}

    def store_grid(self, key, grid):
        self._datas[key] = GridCacheItem(grid)
        return self._datas[key]

    def get(self, key):
        return self._datas.get(key)


class BaseMeasureCompiler(ABC):
    """
    Base measure compiler

    Uses a cache to store grids currently edited

    For each grid, the cache contains :

        - Measures already created
        - totals by category
        - totals by type

    Totals are used in a second time to compute "total" measures
    (not related to account numbers)
    """

    measure_type_class: BaseAccountingMeasureType
    measure_type_category_class: Optional[BaseAccountingMeasureTypeCategory]
    measure_grid_class: BaseAccountingMeasureGrid
    measure_class: BaseAccountingMeasure
    label: str

    def __init__(self, upload, operations):
        self.upload = upload
        self.filetype = upload.filetype
        self.operations = operations
        self.session = DBSESSION()
        self.cache = GridCache()

        # Collect all types
        self.common_measure_types = self._collect_common_measure_types()
        self.categories = self._collect_categories()
        self.computed_measure_types = self._collect_computed_measure_types()

        self.all_type_ids = [t.id for t in self.common_measure_types]
        for types in self.computed_measure_types.values():
            self.all_type_ids.extend([t.id for t in types])

        self.processed_grids = []

    def _get_active_type_query(self):
        """
        Build a query to list active measure types
        :returns: An sqlalchemy query object
        """
        if self.measure_type_category_class:
            return (
                self.measure_type_class.query()
                .join(self.measure_type_category_class)
                .filter(self.measure_type_class.active == True)  # noqa: E712
                .filter(self.measure_type_category_class.active == True)  # noqa: E712
            )
        else:
            return self.measure_type_class.query().filter(
                self.measure_type_class.active == True
            )  # noqa: E712

    def _collect_common_measure_types(self):
        """
        Retrieve measure types that are not computed from other measures
        :returns: The list of measure types
        """
        return (
            self._get_active_type_query()
            .filter(
                or_(
                    self.measure_type_class.is_total == False,  # noqa: E712
                    self.measure_type_class.total_type == "account_prefix",
                )
            )
            .all()
        )

    def _collect_categories(self) -> Optional[List[BaseAccountingMeasureTypeCategory]]:
        """
        Retrieve all measure type categories
        """
        if self.measure_type_category_class:
            return self.measure_type_category_class.get_categories()
        else:
            return None

    def _collect_computed_measure_types(self):
        """
        Collect computed measure types and store them by category id

        :returns: a dict {category_id: [list of MeasureType]}
        """
        result = OrderedDict()
        query = self._get_active_type_query()

        if self.measure_type_category_class:
            query = (
                query.filter(
                    self.measure_type_class.is_total == True,  # noqa: E712
                )
                .filter(
                    self.measure_type_class.total_type != "account_prefix",
                )
                .order_by(self.measure_type_category_class.order)
                .order_by(self.measure_type_class.order)
            )
        else:
            query = (
                query.filter(
                    self.measure_type_class.is_total == True,  # noqa: E712
                )
                .filter(
                    self.measure_type_class.total_type != "account_prefix",
                )
                .order_by(self.measure_type_class.order)
            )

        for typ in query:
            result.setdefault(typ.category_id, []).append(typ)

        return result

    def get_cache_key_from_grid(self, grid):
        """
        Build a cache key based on the given grid object

        :param obj grid: The grid instance
        :returns: A valid dict key
        """
        pass

    def get_cache_key_from_operation(self, operation):
        """
        Build a cache key based on the given operation object

        :param obj operation: The AccountingOperation instance
        :returns: A valid dict key
        """
        pass

    def _get_new_measure(self, measure_type, grid_id):
        """
        Build a new measure
        """
        measure = self.measure_class(
            label=measure_type.label,
            grid_id=grid_id,
            measure_type_id=measure_type.id,
            order=measure_type.order,
        )
        self.session.add(measure)
        self.session.flush()
        return measure

    @abstractmethod
    def _clean_existing_grid(self, grid_item):
        """
        Clean an existing grid on first load
        specific to the Measure Types

        :param obj grid_item: A GridCacheItem instance
        """
        pass

    @abstractmethod
    def _query_grid(self, operation):
        pass

    @abstractmethod
    def _get_new_grid(self, operation):
        pass

    def get_grid_item(self, operation):
        """
        Retrieve the grid related to the given operation datas

        :param obj operation: an AccountingOperation instance
        :returns: A Grid instance
        """
        key = self.get_cache_key_from_operation(operation)
        grid_item = self.cache.get(key)
        if grid_item is None:
            grid = self._query_grid(operation)
            if grid is None:
                grid = self._get_new_grid(operation)
                self.session.add(grid)
                self.session.flush()
                grid_item = self.cache.store_grid(key, grid)
            else:
                grid_item = self.cache.store_grid(key, grid)
                self._clean_existing_grid(grid_item)
        return grid_item

    def get_values_for_computation(self, grid_item):
        """
        Collect total values in a dict for complex datas computation

        :param obj grid_item: An instance of GridCacheItem
        """
        result = {}
        if self.categories:
            for category in self.categories:
                result[category.label] = grid_item.get_category_total(category.id)

        for typ_ in self.common_measure_types:
            result[typ_.label] = grid_item.get_type_total(typ_.id)

        for typlist_ in list(self.computed_measure_types.values()):
            for typ_ in typlist_:
                value = grid_item.get_type_total(typ_.id)
                result[typ_.label] = value

        return result

    def _cache_grid_totals(self):
        """
        Cache all grid totals in order to use them in computation
        """
        for grid_item in self.processed_grids:
            for measure in list(grid_item.get_measures().values()):
                grid_item.set_total_type(measure)
                grid_item.update_category_total(measure)

    def _process_common_measures(self):
        """
        Compile common measures (related to an account prefix) with the given
        operations

        :returns: A list of GridCacheItem
        """
        logger.debug("    + Processing datas with {}".format(self.__class__.__name__))
        for operation in self.operations:
            if operation.company_id is None:
                continue

            current_grid_item = self.get_grid_item(operation)
            grid = current_grid_item.grid
            if current_grid_item not in self.processed_grids:
                self.processed_grids.append(current_grid_item)

            measures = current_grid_item.get_measures()

            for measure_type in self.common_measure_types:
                if measure_type.match(operation.general_account):
                    measure = measures.get(measure_type.id)
                    if measure is None:
                        measure = self._get_new_measure(
                            measure_type,
                            grid.id,
                        )
                        current_grid_item.store_measure(measure)

                    operation_sign = measure_type.sign()

                    measure.value += operation_sign * operation.total()

                    self.session.merge(measure)
                    self.session.flush()

        return self.processed_grids

    def _complete_grids_with_common_measures(self):
        """
        Insert common measures in the grids if not set yet
        """
        for grid_item in self.processed_grids:
            measures = grid_item.get_measures()
            for measure_type in self.common_measure_types:
                measure = measures.get(measure_type.id)
                if measure is None:
                    measure = self._get_new_measure(
                        measure_type,
                        grid_item.grid.id,
                    )
                    grid_item.store_measure(measure)
                else:
                    measure.order = measure_type.order
                    self.session.merge(measure)

    def _process_computed_measures(self):
        """
        Process dynamically computed measures (based on the other ones)

        :returns: A list of GridCacheItem
        """
        for grid_item in self.processed_grids:
            measures = grid_item.get_measures()
            for category_id, measure_types in list(self.computed_measure_types.items()):
                for measure_type in measure_types:
                    values = self.get_values_for_computation(grid_item)
                    value = measure_type.compute_total(values)
                    measure = measures.get(measure_type.id)
                    if measure is None:
                        measure = self._get_new_measure(
                            measure_type,
                            grid_item.grid.id,
                        )
                        grid_item.store_measure(measure)
                    else:
                        measure.order = measure_type.order

                    measure.value = measure_type.sign() * value
                    self.session.merge(measure)
                    grid_item.set_total_type(measure)

        return self.processed_grids

    def process_datas(self):
        """
        Main entry point to process measure computation
        """
        self._process_common_measures()
        self._complete_grids_with_common_measures()
        self.session.flush()
        self._cache_grid_totals()
        self._process_computed_measures()
        self.session.flush()
        return [griditem.grid for griditem in self.processed_grids]

    def _get_date_to_use_for_grid(self):
        """
        For single grids (BalanceSheet, Treasury), return the date to use for the grid
        """
        if self.upload.filetype == self.upload.SYNCHRONIZED_ACCOUNTING:
            # Remontée auto, on veut la date de mise à jour,
            # pas la date de création (qui date du premier upload, surement
            # le 1er janvier)
            date_to_use = self.upload.updated_at.date()
        else:
            # Cas des fichiers, on veut la date (données du fichier),
            # pas la date de mise à jour (date d'upload)
            date_to_use = self.upload.date
        this_year = datetime.date.today().year

        # si les écritures datent d'années précédentes à l'année en cours,
        if self.upload.date.year < this_year:
            # Only works for 31/12 exercice closure, not a problem as long as
            # synchronized accounting works year by year
            date_to_use = datetime.date(day=31, month=12, year=self.upload.date.year)

        return date_to_use


class BalanceSheetMeasureCompiler(BaseMeasureCompiler):
    measure_type_class = BalanceSheetMeasureType
    measure_type_category_class = None
    measure_grid_class = BalanceSheetMeasureGrid
    measure_class = BalanceSheetMeasure
    label = "Génération des bilans"

    def get_message(self, grids):
        return """Génération des bilans

Bilans générés : {}

""".format(
            len(grids)
        )

    def get_cache_key_from_operation(self, operation):
        """
        Build a cache key based on the given operation object
        """
        date_to_use = self._get_date_to_use_for_grid()
        key = (operation.company_id, date_to_use)

        return key

    def get_cache_key_from_grid(self, grid):
        """
        Build a cache key based on the given grid object
        """
        key = (grid.company_id, grid.date)
        return key

    def _query_grid(self, operation):
        """
        Query a grid associated to the given operation

        Query filters should match the get_cache_key_from_operation options
        """
        date_to_use = self._get_date_to_use_for_grid()
        query = (
            BalanceSheetMeasureGrid.query()
            .filter_by(date=date_to_use)
            .filter_by(company_id=operation.company_id)
        )

        query = query.order_by(desc(BalanceSheetMeasureGrid.datetime))
        return query.first()

    def _get_new_grid(self, operation):
        """
        Build a new grid based on the given operation

        :param obj operation: The AccountingOperation from which we build
        measure
        """
        date_to_use = self._get_date_to_use_for_grid()
        return BalanceSheetMeasureGrid(
            date=date_to_use,
            company_id=operation.company_id,
            upload=self.upload,
        )

    def _clean_existing_grid(self, grid_item):
        """
        Clean an existing grid on first load

        :param obj grid_item: A GridCacheItem instance
        """
        for measure in grid_item.grid.measures:
            self.session.delete(measure)

    def _process_computed_measures(self):
        for grid_item in self.processed_grids:
            measures = grid_item.get_measures()
            for category_id, measure_types in list(self.computed_measure_types.items()):
                for measure_type in measure_types:
                    if measure_type.total_type == "complex_total":
                        values = self._get_values_for_computation(grid_item)
                        value = measure_type.compute_total(values)
                        measure = measures.get(measure_type.id)

                    if measure_type.total_type == "categories":
                        # Total of passive and active (not necessarily meaningfull
                        # in real life)
                        if (
                            measure_type.account_prefix == "active,passive"
                            or measure_type.account_prefix == "passive,active"
                        ):
                            value = self._get_balance_sheet_passive_active_total_value(
                                grid_item, measure_type
                            )
                        elif isinstance(measure_type, ActiveBalanceSheetMeasureType):
                            value = self._get_balance_sheet_total_value(grid_item, True)
                        elif isinstance(measure_type, PassiveBalanceSheetMeasureType):
                            value = self._get_balance_sheet_total_value(
                                grid_item, False
                            )
                        else:
                            raise Exception(
                                "Unexpected measure type (passive or active expected)"
                            )

                    measure = measures.get(measure_type.id)
                    if measure is None:
                        measure = self._get_new_measure(
                            measure_type,
                            grid_item.grid.id,
                        )
                        grid_item.store_measure(measure)
                    else:
                        measure.order = measure_type.order

                    measure.value = measure_type.sign() * value
                    self.session.merge(measure)
                    grid_item.set_total_type(measure)

        return self.processed_grids

    def _get_values_for_computation(self, grid_item):
        """
        Collect total values in a dict for complex datas computation

        :param obj grid_item: An instance of GridCacheItem
        """
        result = {}
        result["Total Actif"] = self._get_balance_sheet_total_value(grid_item, True)
        result["Total Passif"] = self._get_balance_sheet_total_value(grid_item, False)

        for typ_ in self.common_measure_types:
            result[typ_.label] = grid_item.get_type_total(typ_.id)

        for typlist_ in list(self.computed_measure_types.values()):
            for typ_ in typlist_:
                value = grid_item.get_type_total(typ_.id)
                result[typ_.label] = value

        return result

    def _get_balance_sheet_total_value(self, grid_item, active):
        if active:
            polymorphic_id = "active_balance_sheet"
        else:
            polymorphic_id = "passive_balance_sheet"

        query = (
            self.session.query(func.sum(BalanceSheetMeasure.value))
            .filter(BalanceSheetMeasure.grid_id == grid_item.grid.id)
            .outerjoin(BalanceSheetMeasure.measure_type)
            .filter(BalanceSheetMeasureType.type_ == polymorphic_id)
            .filter(BalanceSheetMeasureType.is_total == False)
        )

        if query.first() and query.first()[0] is not None:
            return query.first()[0]
        else:
            return 0

    def _get_balance_sheet_passive_active_total_value(self, grid_item, measure_type):
        query = (
            self.session.query(func.sum(BalanceSheetMeasure.value))
            .filter(BalanceSheetMeasure.grid_id == grid_item.grid.id)
            .outerjoin(BalanceSheetMeasure.measure_type)
            .filter(BalanceSheetMeasureType.is_total == False)
        )

        if query.first() and query.first()[0] is not None:
            return query.first()[0]
        else:
            return 0


class TreasuryMeasureCompiler(BaseMeasureCompiler):
    measure_type_class = TreasuryMeasureType
    measure_type_category_class = TreasuryMeasureTypeCategory
    measure_grid_class = TreasuryMeasureGrid
    measure_class = TreasuryMeasure
    label = "Génération des états de trésorerie"

    def get_message(self, grids):
        return """Génération des états de trésorerie

États de trésorerie générés : {}

""".format(
            len(grids)
        )

    def get_cache_key_from_operation(self, operation):
        """
        Build a cache key based on the given operation object
        """
        date_to_use = self._get_date_to_use_for_grid()
        key = (operation.company_id, date_to_use)

        return key

    def get_cache_key_from_grid(self, grid):
        """
        Build a cache key based on the given grid object
        """
        key = (grid.company_id, grid.date)
        return key

    def _query_grid(self, operation):
        """
        Query a grid associated to the given operation

        Query filters should match the get_cache_key_from_operation options
        """
        date_to_use = self._get_date_to_use_for_grid()
        query = (
            TreasuryMeasureGrid.query()
            .filter_by(date=date_to_use)
            .filter_by(company_id=operation.company_id)
        )

        query = query.order_by(desc(TreasuryMeasureGrid.datetime))
        return query.first()

    def _get_new_grid(self, operation):
        """
        Build a new grid based on the given operation

        :param obj operation: The AccountingOperation from which we build
        measure
        """
        date_to_use = self._get_date_to_use_for_grid()
        return TreasuryMeasureGrid(
            date=date_to_use,
            company_id=operation.company_id,
            upload=self.upload,
        )

    def _clean_existing_grid(self, grid_item):
        """
        Clean an existing grid on first load

        :param obj grid_item: A GridCacheItem instance
        """
        for measure in grid_item.grid.measures:
            self.session.delete(measure)


class IncomeStatementMeasureCompiler(BaseMeasureCompiler):
    measure_type_class = IncomeStatementMeasureType
    measure_type_category_class = IncomeStatementMeasureTypeCategory
    measure_grid_class = IncomeStatementMeasureGrid
    measure_class = IncomeStatementMeasure
    label = "Génération des comptes de résultat"

    def get_message(self, grids):
        return """Génération des comptes de résultat :

Comptes de résultat traités : {}

""".format(
            int(len(grids) / 12)
        )

    def get_cache_key_from_operation(self, operation):
        """
        Build a cache key based on the given operation object
        """
        return (operation.company_id, operation.date.year, operation.date.month)

    def get_cache_key_from_grid(self, grid):
        """
        Build a cache key based on the given grid object
        """
        return (grid.company_id, grid.year, grid.month)

    def _query_grid(self, operation):
        """
        Query a grid associated to the given operation

        Query filters should match the get_cache_key_from_operation options
        """
        return (
            IncomeStatementMeasureGrid.query()
            .filter_by(year=operation.date.year)
            .filter_by(month=operation.date.month)
            .filter_by(company_id=operation.company_id)
            .first()
        )

    def _get_new_grid(self, operation):
        """
        Build a new grid based on the given operation

        :param obj operation: The AccountingOperation from which we build
        measure
        """
        return IncomeStatementMeasureGrid(
            year=operation.date.year,
            month=operation.date.month,
            company_id=operation.company_id,
            upload=self.upload,
        )

    def _clean_existing_grid(self, grid_item):
        """
        Clean an existing grid on first load

        :param obj grid_item: A GridCacheItem instance
        """
        # Only clean the old grid item measures (keep existing)
        old_measures = grid_item.clean_old_measures(self.all_type_ids)
        for measure in old_measures:
            self.session.delete(measure)

    def _process_common_measures(self):
        """
        Add specific process for IncomeStatementMeasureGrid, for now
        setting the updated_at attribute
        """
        logger.debug(
            "  + Processing specific datas for child {}".format(self.__class__.__name__)
        )

        # Calling parent to really process measures
        logger.debug("  + Calling parent process common measures")
        BaseMeasureCompiler._process_common_measures(self)

        # On choisit la date à utiliser comme date de mise à jour des grids
        date_to_set = None
        if self.upload.filetype == AccountingOperationUpload.SYNCHRONIZED_ACCOUNTING:
            date_to_set = self.upload.updated_at
        else:
            # Techniquement c'est la même chose que updated_at
            # mais c'est plus explicite d'utiliser created_at
            date_to_set = self.upload.created_at

        # Setting the date in the non void grids
        for grid in self.processed_grids:
            if grid is not None:
                grid.grid.updated_at = date_to_set
                self.session.merge(grid.grid)

        self.session.flush()
        return self.processed_grids


GRID_COMPILERS = {
    "treasury": TreasuryMeasureCompiler,
    "income_statement": IncomeStatementMeasureCompiler,
    "balance_sheet": BalanceSheetMeasureCompiler,
}


def get_measure_compilers(grid_type=None) -> List[Type[BaseMeasureCompiler]]:
    """
    Retrieve the measure compilers to be used
    """
    if grid_type is not None:
        return [GRID_COMPILERS[grid_type]]
    else:
        return list(GRID_COMPILERS.values())


MAIL_ERROR_SUBJECT = "[Erreur] {}"
MAIL_SUCCESS_SUBJECT = "[Succès] {}"


def send_success(request, mail_addresses, type_label, message):
    """
    Send a success email

    :param obj request: The current request object
    :param list mail_addresses: List of recipients e-mails
    :param str message: message to send
    """
    if mail_addresses:
        try:
            subject = MAIL_SUCCESS_SUBJECT.format(type_label)
            send_mail(request, mail_addresses, message, subject)
        except Exception:
            logger.exception("Error sending email")


def send_error(request, mail_addresses, type_label, message):
    """
    Send an error email

    :param obj request: The current request object
    :param list mail_addresses: List of recipients e-mails
    :param str message: message to send
    """
    if mail_addresses:
        try:
            subject = MAIL_ERROR_SUBJECT.format(type_label)
            send_mail(request, mail_addresses, message, subject)
        except Exception:
            logger.exception("Error sending email")


def get_closure_day_and_month() -> Tuple[int, int]:
    # Get data from caerp's configuration
    closure_day = Config.get_value("accounting_closure_day", default=31, type_=int)
    closure_month = Config.get_value("accounting_closure_month", default=12, type_=int)
    return closure_day, closure_month


def get_exercice_dates_from_date(
    date: datetime.date,
) -> tuple[datetime.date, datetime.date]:
    """
    Return the start and end dates of the fiscal year of the given date
    """
    # Reference year for collecting data
    current_year = date.year
    closure_day, closure_month = get_closure_day_and_month()

    # Find exercice start day and month
    temp_date = datetime.date(
        current_year, closure_month, closure_day
    ) + datetime.timedelta(days=1)
    start_day = temp_date.day
    start_month = temp_date.month

    # Collecting operation for current exercice fiscal
    exercice_start_date = datetime.date(current_year, start_month, start_day)
    exercice_end_date = datetime.date(current_year, closure_month, closure_day)

    # If closure day is not 31/12 we have an exercice overlaping two years
    if not (closure_day == 31 and closure_month == 12):
        # Is the given date after the closure ?
        this_month = date.month
        this_day = date.day
        is_after_the_closure = None
        if this_month > closure_month:
            is_after_the_closure = True
        elif this_month == closure_month:
            if this_day > closure_day:
                is_after_the_closure = True
            else:
                is_after_the_closure = False
        else:
            is_after_the_closure = False

        # If so or not we set the corresponding exercice dates
        if is_after_the_closure:
            exercice_start_date = exercice_start_date.replace(year=current_year)
            exercice_end_date = exercice_end_date + relativedelta(years=1)
        else:
            exercice_start_date = exercice_start_date - relativedelta(years=1)
            exercice_end_date = exercice_end_date.replace(year=current_year)

    return exercice_start_date, exercice_end_date


def collect_operations_by_fiscal_year(
    upload: AccountingOperationUpload, exclude_future_operations: bool = False
) -> List[AccountingOperation]:
    """
    Return the operations needed.
    Collect the operations ("écritures") according to the "exercice fiscal".
    If the "exercice" has been set "closed" in MoOGLi we don't collect the
    operation of former years (because à-nouveau operation have been done by
    the accountant.
    For now, this function is only for the treasury measures, in the future
    it might also be for the income statement measure.
    """
    logger.info(
        "  + Collecting operations for upload {} (upload_id={})".format(
            upload.date.year, upload.id
        )
    )

    # Get exercice start and end dates
    if upload.date.year == datetime.datetime.now().year:
        ref_date = datetime.datetime.now()
    else:
        ref_date = datetime.date(upload.date.year, 12, 31)
    (exercice_start_date, exercice_end_date) = get_exercice_dates_from_date(ref_date)
    logger.info(
        "  + Exercice starts the {} and ends the {}".format(
            exercice_start_date, exercice_end_date
        )
    )

    # Compute first operation date (through former exercices)
    first_operation_date = exercice_start_date
    first_exercice = (
        DBSESSION().query(extract("year", func.min(AccountingOperation.date))).scalar()
    )
    previous_exercice = exercice_end_date.year - 1
    for exercice in range(previous_exercice, first_exercice - 1, -1):
        exercice_closure = AccountingClosure.query().filter_by(year=exercice).first()
        closure_is_done = exercice_closure.active if exercice_closure else False
        if closure_is_done:
            # Stop on first closure
            break
        else:
            first_operation_date = exercice_start_date - relativedelta(
                years=(exercice_end_date.year - exercice)
            )

    # Compute last operation date (exclude future operations if needed)
    last_operation_date = exercice_end_date
    if exclude_future_operations:
        last_operation_date = min(exercice_end_date, datetime.date.today())

    # Collect operations on computed period
    logger.info(
        "  + Date range is from {} to {}".format(
            first_operation_date, last_operation_date
        )
    )
    collected_operations = (
        AccountingOperation.query()
        .filter(
            AccountingOperation.date.between(first_operation_date, last_operation_date)
        )
        .all()
    )
    logger.info("  + {} operations collected".format(len(collected_operations)))

    return collected_operations


def collect_operations(
    compiler_type: str, upload: AccountingOperationUpload
) -> List[AccountingOperation]:
    """collect operations to use for the given compiler_type

    :param grid_type: _description_
    :type grid_type: str
    :param upload: _description_
    :type upload: AccountingOperationUpload
    :return: _description_
    :rtype: List[AccountingOperation]
    """
    if compiler_type == "income_statement":
        return AccountingOperation.query().filter(
            AccountingOperation.upload_id == upload.id
        )
    elif compiler_type == "balance_sheet":
        return (
            AccountingOperation.query()
            .filter(AccountingOperation.upload_id == upload.id)
            .filter(AccountingOperation.date <= datetime.date.today())
        )
    else:
        return collect_operations_by_fiscal_year(upload, exclude_future_operations=True)


def run_compiler(compiler_type: str, upload_id: int, mail: bool = True):
    """
    Collect accounting operations to be used by the compiler factory
    """
    logger.info(
        f"# Compiling {compiler_type} for AccoutingOperationUpload : {upload_id}"
    )

    messages = []
    transaction.begin()
    upload = AccountingOperationUpload.get(upload_id)
    if upload is None:
        logger.error("  - Upload doesn't exist")
        transaction.abort()
        return False

    operations = collect_operations(compiler_type, upload)
    if not operations:
        logger.error("Can't find any operation")
        transaction.abort()
        return False

    factory = GRID_COMPILERS[compiler_type]
    try:
        compiler = factory(upload, operations)
        grids = compiler.process_datas()
        messages.append(compiler.get_message(grids))
    except Exception as exc:
        logger.exception("Error while generating measures")
        transaction.abort()
        if mail:
            request = get_request()
            mail_addresses = get_recipients_addresses(request)
            message = getattr(exc, "message", str(exc))
            send_error(
                request,
                mail_addresses,
                factory.label,
                message,
            )
        return False
    else:
        logger.info("{0} measure grids were handled".format(len(grids)))
        if mail:
            request = get_request()
            mail_addresses = get_recipients_addresses(request)
            send_success(
                request,
                mail_addresses,
                compiler.label,
                compiler.get_message(grids),
            )
            logger.info("A success email has been sent to {0}".format(mail_addresses))

    transaction.commit()
    logger.info("The transaction has been commited")
    return True


LOCK_NAME = "measure_compute"


def compile_measures(
    upload_id: int, grid_type: Optional[str] = None, mail: bool = True
):
    """Compile accounting measures related to upload id

    :param grid_type: One of the available grid_type (income_statement,
    treasury, balance_sheet)
    """
    logger.info(f"Compiling Accounting States for upload {upload_id}")
    if is_locked(LOCK_NAME):
        logger.error("Other task is running : Cancel")
        return False

    acquire_lock(LOCK_NAME)
    try:
        if grid_type is not None:
            logger.info(f"  + Only compiling {grid_type} grids")
            grid_types = [grid_type]
        else:
            grid_types = list(GRID_COMPILERS.keys())

        for grid_type in grid_types:
            run_compiler(grid_type, upload_id, mail)
    except Exception:
        logger.exception("Erreur inconnue")

    release_lock(LOCK_NAME)
    return True


@celery_app.task(bind=True)
def compile_measures_task(self, upload_id, grid_type=None):
    """
    Celery task handling measures compilation
    """
    logger.info("# Launching the compile measure task #")
    res = compile_measures(upload_id, grid_type)
    if res:
        logger.info("===> Task Finished")


@celery_app.task(bind=True)
def scheduled_compile_measure_task(self, force=False):
    """
    Scheduled Celery task to handle automatic measures compilation for synchronized datas

    ACTIVATE THIS TASK IN CELERY'S INI CONFIG FILE IF NEEDED
    Eg:
        [celerybeat:accounting_measure_compute]
        task = caerp.celery.tasks.accounting_measure_compute.scheduled_compile_measure_task
        type = crontab
        schedule = {"minute": 0, "hour": 6}
    """
    logger.info("# Launching scheduled compile measure task for synchronized datas")
    yesterday = datetime.datetime.today() - datetime.timedelta(1)
    uploads = (
        AccountingOperationUpload.query()
        .filter(
            AccountingOperationUpload.filetype
            == AccountingOperationUpload.SYNCHRONIZED_ACCOUNTING
        )
        .filter(AccountingOperationUpload.updated_at >= yesterday)
        .filter(AccountingOperationUpload.is_upload_valid == True)
        .order_by(AccountingOperationUpload.date)
        .all()
    )
    if not uploads or len(uploads) == 0:
        logger.error(
            "ABORT : No valid synchronized accounting upload whithin the last 24h"
        )
    else:
        for upload in uploads:
            compile_measures(upload.id, mail=False)
        logger.info("==> End of scheduled compile measure task for synchronized datas")
