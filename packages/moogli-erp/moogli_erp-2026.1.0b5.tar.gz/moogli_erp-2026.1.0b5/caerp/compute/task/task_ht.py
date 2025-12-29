"""
    Task computing tool
    Used to compute invoice, estimation or cancelinvoice totals
"""
import logging
import operator
from typing import Dict

from caerp.compute import math_utils
from caerp.compute.task.common import (
    CommonDiscountLineCompute,
    CommonGroupCompute,
    CommonLineCompute,
    CommonTaskCompute,
)
from caerp.models.tva import Tva

logger = logging.getLogger(__name__)


class TaskCompute(CommonTaskCompute):
    """
    class A(TaskCompute):
        pass

    A.total()
    """

    # TVA computing
    def get_tvas(self, with_discounts=True) -> Dict[Tva, float]:
        """
        return a dict with the tvas amounts stored by tva
        {1960:450.56, 700:45}
        """
        ret_dict = {}
        for group in self.task.line_groups:
            for tva, value in group.get_tvas().items():
                val = ret_dict.get(tva, 0)
                val += value
                ret_dict[tva] = val

        if with_discounts:
            for discount in self.task.discounts:
                val = ret_dict.get(discount.tva, 0)
                val -= discount.tva_amount()
                ret_dict[discount.tva] = val

        for key in ret_dict:
            ret_dict[key] = self.floor(ret_dict[key])
        return ret_dict

    def get_tvas_by_product(self) -> dict:
        """
        Return tvas stored by product type
        """
        ret_dict = {}
        for group in self.task.line_groups:
            for key, value in group.get_tvas_by_product().items():
                val = ret_dict.get(key, 0)
                val += value
                ret_dict[key] = val

        for discount in self.task.discounts:
            val = ret_dict.get("rrr", 0)
            val += discount.tva_amount()
            ret_dict["rrr"] = val

        for key in ret_dict:
            ret_dict[key] = self.floor(ret_dict[key])

        return ret_dict

    def tva_native_parts(self, with_discounts=True) -> Dict[Tva, int]:
        """
        Return a dict with the HT amounts stored by corresponding tva value
        dict(tva=tva_part,)
        for each tva value *in native compute mode* (eg: HT when task.mode == 'ht')
        """
        return self.tva_ht_parts(with_discounts)

    def tva_ht_parts(self, with_discounts=True) -> Dict[Tva, int]:
        """
        Return a dict with the HT amounts stored by corresponding tva value
        dict(tva=ht_tva_part,)
        for each tva value
        """
        ret_dict = {}
        lines = []
        for group in self.task.line_groups:
            lines.extend(group.lines)
        ret_dict = self.add_ht_by_tva(ret_dict, lines)
        if with_discounts:
            ret_dict = self.add_ht_by_tva(ret_dict, self.task.discounts, operator.sub)

        return ret_dict

    def tva_ttc_parts(self, with_discounts=True) -> Dict[Tva, float]:
        """
        Return a dict with TTC amounts stored by corresponding tva
        """
        ret_dict = {}
        ht_parts = self.tva_ht_parts(with_discounts)
        tva_parts = self.get_tvas(with_discounts)

        for tva, amount in ht_parts.items():
            ret_dict[tva] = amount + tva_parts.get(tva, 0)
        return ret_dict

    def tva_amount(self) -> int:
        """
        Compute the sum of the TVAs amount of TVA
        """
        return self.floor(
            sum(tva_amount for tva_amount in list(self.get_tvas().values()))
        )

    def total_ht(self) -> int:
        """
        compute the HT amount
        """
        total_ht = self.groups_total_ht() - self.discount_total_ht()
        return self.floor(total_ht)

    def total_ttc(self) -> int:
        """
        Compute the TTC total
        """
        return self.total_ht() + self.tva_amount()

    def total(self) -> int:
        """
        Compute TTC after tax removing
        """
        return self.total_ttc()


class GroupCompute(CommonGroupCompute):
    task_line_group = None

    def total_ttc(self):
        """
        Returns the TTC total for this group
        """
        return self.total_ht() + self.tva_amount()


class LineCompute(CommonLineCompute):
    """
    Computing tool for line objects
    """

    def unit_ht(self) -> int:
        return self.task_line.cost

    def unit_ttc(self) -> int:
        if self.task_line.tva:
            unit_tva = math_utils.compute_tva(self.unit_ht(), self.task_line.tva.value)
        else:
            unit_tva = 0
        return self.unit_ht() + unit_tva

    def total_ht(self):
        """
        Compute the line's total
        """
        cost = self.task_line.cost or 0
        quantity = self._get_quantity()
        return cost * quantity

    def tva_amount(self):
        """
        compute the tva amount of a line
        """
        total_ht = self.total_ht()
        if self.task_line.tva:
            return math_utils.compute_tva(total_ht, self.task_line.tva.value)
        else:
            return 0

    def total(self):
        """
        Compute the ttc amount of the line
        """
        return self.tva_amount() + self.total_ht()


class DiscountLineCompute(CommonDiscountLineCompute):
    """
    Computing tool for discount_line objects
    """

    def total_ht(self):
        return float(self.discount_line.amount)

    def tva_amount(self):
        """
        compute the tva amount of a line
        """
        total_ht = self.total_ht()
        return math_utils.compute_tva(total_ht, self.discount_line.tva.value)

    def total(self):
        return self.tva_amount() + self.total_ht()
