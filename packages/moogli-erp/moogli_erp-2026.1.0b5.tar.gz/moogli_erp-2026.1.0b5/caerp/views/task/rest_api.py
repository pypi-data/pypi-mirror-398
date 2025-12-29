import logging
from typing import Optional

import colander
from colanderalchemy import SQLAlchemySchemaNode
from pyramid.csrf import get_csrf_token
from pyramid.httpexceptions import HTTPForbidden

from caerp.compute.math_utils import percentage, str_to_float
from caerp.consts.permissions import PERMISSIONS
from caerp.controllers.state_managers import get_validation_allowed_actions
from caerp.controllers.task.discount_line import discountline_on_before_commit
from caerp.controllers.task.post_ttc_line import post_ttc_line_on_before_commit
from caerp.controllers.task.task import (
    bulk_edit_tva_and_product_id,
    task_on_before_commit,
    taskline_from_sale_product,
    tasklinegroup_from_sale_product_work,
)
from caerp.controllers.task.task_line import taskline_on_before_commit
from caerp.controllers.task.task_line_group import tasklinegroup_on_before_commit
from caerp.forms.files import get_file_upload_schema
from caerp.forms.jsonschema import convert_to_jsonschema
from caerp.forms.tasks.task import (
    get_add_edit_discountline_schema,
    get_add_edit_post_ttc_line_schema,
    get_add_edit_taskline_schema,
    get_add_edit_tasklinegroup_schema,
    get_add_task_schema,
)
from caerp.forms.tva import get_tva_id_product_id_schema
from caerp.models.company import Company
from caerp.models.project import Project
from caerp.models.sale_product.base import BaseSaleProduct
from caerp.models.sale_product.work import SaleProductWork
from caerp.models.task import DiscountLine, Task
from caerp.models.third_party import Customer
from caerp.services import get_model_by_id
from caerp.services.config import get_config_value
from caerp.services.task.mentions import get_company_task_mentions
from caerp.services.tva import (
    get_product_by_id,
    get_products,
    get_task_default_product,
    get_task_default_tva_and_product,
    get_tva_by_id,
    get_tvas,
)
from caerp.utils.image import ImageResizer
from caerp.utils.rest.apiv1 import RestError
from caerp.views import BaseRestView
from caerp.views.business.routes import BUSINESS_ITEM_OVERVIEW_ROUTE
from caerp.views.files.rest_api import FileRestView
from caerp.views.project.routes import API_COMPANY_PROJECTS
from caerp.views.status.rest_api import (
    StatusLogEntryRestView,
    get_other_users_for_notification,
)
from caerp.views.third_party.customer.routes import API_COMPANY_CUSTOMERS_ROUTE

from ..status.utils import get_visibility_options
from .utils import (
    collect_price_study_product_types,
    get_business_types,
    get_field_definition,
    get_mentions,
    get_task_insurance_options,
    get_task_url,
    get_task_view_type,
    get_workunits,
)

logger = logging.getLogger(__name__)


class TaskAddRestView(BaseRestView):
    """
    Rest api used to add a new task
    """

    factory = Task

    class GetParamsSchema(colander.Schema):
        customer_id = colander.SchemaNode(colander.Integer(), missing=colander.drop)
        project_id = colander.SchemaNode(colander.Integer(), missing=colander.drop)
        phase_id = colander.SchemaNode(colander.Integer(), missing=colander.drop)

    def get_schema(self, submitted: Optional[dict] = None) -> SQLAlchemySchemaNode:
        params = self.GetParamsSchema().deserialize(self.request.GET)
        return get_add_task_schema(
            self.request, self.factory, company_id=self.get_company_id(), **params
        ).bind(request=self.request)

    def get_company_id(self) -> int:
        if isinstance(self.context, Company):
            return self.context.id
        elif hasattr(self.context, "company_id"):
            return self.context.company_id

    def option_urls(self):
        cid = self.get_company_id()
        _query = {"form_config": 1}
        return {
            "customers_url": self.request.route_path(
                API_COMPANY_CUSTOMERS_ROUTE, id=cid
            ),
            "customers_config_url": self.request.route_path(
                API_COMPANY_CUSTOMERS_ROUTE, id=cid, _query=_query
            ),
            "projects_url": self.request.route_path(API_COMPANY_PROJECTS, id=cid),
            "projects_config_url": self.request.route_path(
                API_COMPANY_PROJECTS, id=cid, _query=_query
            ),
        }

    def form_config(self) -> dict:
        schema = self.get_schema()
        return {
            "options": self.option_urls(),
            "schemas": {
                "default": convert_to_jsonschema(schema),
            },
        }

    def _add_element(self, schema, attributes):
        attributes["company"] = self.context
        attributes["project"] = project = Project.get(attributes["project_id"])
        attributes["user"] = self.request.identity
        customer = Customer.get(attributes["customer_id"])
        if project not in customer.projects:
            customer.projects.append(project)
            self.dbsession.merge(customer)
        return self.factory.create(self.request, customer, attributes)

    def put(self):
        raise HTTPForbidden()


class TaskRestView(BaseRestView):
    """
    Base class for task rest api

    The views contexts are instances of self.factory

    Collection Views

        POST

            Create a new task

    Item views

        GET

            Returns the context in json format

        GET?form_config

            returns the form configuration

        PUT / PATCH

            Edit the current element

        DELETE

            Delete the current element

    Form Configuration  ?action=form_config url

    options

        The available options returned to the UI

    sections

        Description of the different section of the form
        Keys provided in "sections" must be handled by the JS code.

        TODO : Enhance this part to make it more generic.
    """

    factory = None

    def get_schema(self, submitted):
        """
        Return the schema for Task add/edition

        :param dict submitted: The submitted datas
        :returns: A colander.Schema
        """
        raise NotImplementedError("Should be implemented in subclass")

    def form_config(self):
        """
        Form display options

        :returns: The sections that the end user can edit, the options
        available
        for the different select boxes
        """
        result = {
            "actions": {
                "main": self._get_status_actions(),
                "more": self._get_other_actions(),
            }
        }
        result = self._add_form_options(result)
        result = self._add_form_sections(result)
        return result

    def _more_form_options(self, options: dict) -> dict:
        return {}

    def _add_form_options(self, form_config):
        """
        Add the main options provided to the end user UI

        :param dict form_config: The current form configuration
        :returns: The dict with a new 'options' key
        """
        tvas = get_tvas(self.request, internal=self.context.internal)
        products = get_products(self.request, internal=self.context.internal)
        default_tva, default_product = get_task_default_tva_and_product(
            self.request, self.context
        )

        options = {
            # Utilisé globalement dans l'interface
            "compute_mode": self.context.mode,
            "tvas": tvas,
            "workunits": get_workunits(self.request),
            "products": products,
            "mentions": get_mentions(self.request),
            "company_mentions": get_company_task_mentions(
                self.request, self.context.company_id
            ),
            "insurance_options": get_task_insurance_options(self.request),
            "business_types": get_business_types(self.request),
            "csrf_token": get_csrf_token(self.request),
            "decimal_to_display": self.context.decimal_to_display,
            "defaults": {
                "tva_id": getattr(default_tva, "id", ""),
                "product_id": getattr(default_product, "id", ""),
                "quantity": 1,
                "mode": self.context.mode,  # Pour les nouveaux modèles
            },
        }

        if self.context.has_price_study():
            options["defaults"].update(
                {
                    "margin_rate": self.context.company.margin_rate,
                }
            )
            options["product_types"] = collect_price_study_product_types()

        options = self._more_form_options(options)

        # Mémo
        options["visibilities"] = get_visibility_options(self.request)
        options["notification_recipients"] = get_other_users_for_notification(
            self.request, self.context
        )
        form_config["options"] = options
        return form_config

    def _price_study_form_section(self):
        result = {
            "edit": True,
            "common": {
                "general_overhead": {"edit": True},
                "margin_rate": {"edit": True},
            },
            "products": {"mode": {"edit": True}},
        }
        # Si on force le ht (comme pour une facture issue d'un devis)
        # On ne veut pas de formule de calcul ..., tout est en HT
        if self.context.price_study.force_ht:
            result["common"].pop("general_overhead")
            result["common"]["margin_rate"]["edit"] = False
            result["products"]["mode"]["edit"] = False
        elif get_config_value(
            self.request, "price_study_lock_general_overhead", type_=bool, default=False
        ):
            if not self.request.has_permission(PERMISSIONS["global.config_company"]):
                result["common"]["general_overhead"]["edit"] = False
        return result

    def _more_form_sections(self, sections):
        return sections

    def _add_form_sections(self, form_config):
        """
        Return the sections that should be displayed to the end user

        :param dict form_config: The current form_config
        """
        sections = {
            "general": {"edit": True},
            "files": {
                "edit": True,
                "can_validate": False,
            },
            "common": {"edit": True},
            "display_options": {
                "display_units": True,
                "display_ttc": True,
                "input_mode_edit": False,
            },
            "composition": {
                "edit": True,
                "mode": "classic",  # étude de prix / classique / avancement
                "classic": {
                    "lines": {
                        "can_add": True,
                        "can_delete": True,
                        "cost": {"edit": True},
                        "tva": {"edit": True},
                        "quantity": {"edit": True},
                        "product_id": {"edit": True},
                    },
                },
            },
            "notes": {"edit": True},
        }

        # TODO : améliorer la personnalisation en la rendant plus générique
        # Ref #1839 : Champs customs
        for field in (
            "workplace",
            "insurance_id",
            "start_date",
            "end_date",
            "first_visit",
        ):
            sections["common"].update(get_field_definition(field))

        task_type = get_task_view_type(self.context)
        if self.request.has_permission(PERMISSIONS[f"context.validate_{task_type}"]):
            sections["files"]["can_validate"] = True

        # Mode voyage
        if form_config["options"]["business_types"][0]["tva_on_margin"]:
            sections["display_options"]["display_ttc"] = False

        # Mode étude de prix
        if self.context.has_price_study():
            sections["composition"]["price_study"] = self._price_study_form_section()
            sections["composition"]["mode"] = "price_study"
            # On a le droit de changer le mode de saisie que si l'étude de prix
            # n'est pas obligatoire
            if not self.context.project.project_type.price_study_mandatory():
                sections["display_options"]["input_mode_edit"] = True

        elif self.context.project.project_type.include_price_study:
            sections["display_options"]["input_mode_edit"] = True

        if self.context.mode == "ttc":

            sections["composition"]["mode"] = "ttc"

        if hasattr(self, "_more_form_sections"):
            sections = self._more_form_sections(sections)

        form_config["sections"] = sections

        return form_config

    def _get_status_actions(self):
        """
        Returned datas describing available actions on the current item
        :returns: List of actions
        :rtype: list of dict
        """
        actions = []
        url = self.request.current_route_path(_query={"action": "status"})

        for action in get_validation_allowed_actions(self.request, self.context):
            json_resp = action.__json__(self.request)
            json_resp["url"] = url
            json_resp["widget"] = "status"
            actions.append(json_resp)

        if self.context.business.visible:
            url = self.request.route_path(
                BUSINESS_ITEM_OVERVIEW_ROUTE, id=self.context.business_id
            )
            link = {
                "widget": "anchor",
                "option": {
                    "url": url,
                    "label": "Voir l'affaire",
                    "title": f"Voir l'affaire : {self.context.business.name}",
                    "css": "btn icon",
                    "icon": "folder",
                },
            }
            actions.insert(0, link)
        return actions

    def _get_other_actions(self):
        """
        Return the description of other available actions :
            signed_status
            duplicate
            ...
        """
        result = []
        view_type = get_task_view_type(self.context)

        if (
            self.context.business.business_type.bpf_related
            and self.request.has_permission(
                PERMISSIONS["context.edit_bpf"], self.context.business
            )
        ):
            url = self.request.route_path(
                "/businesses/{id}/bpf", id=self.context.business_id
            )
            result.append(
                {
                    "widget": "anchor",
                    "option": {
                        "url": url,
                        "label": "BPF",
                        "title": "Voir les données BPF de l'affaire",
                        "css": "btn",
                        "icon": "chart-pie",
                    },
                }
            )

        if self.request.has_permission(PERMISSIONS[f"context.duplicate_{view_type}"]):
            url = get_task_url(self.request, suffix="/duplicate")
            result.append(
                {
                    "widget": "anchor",
                    "option": {
                        "url": url,
                        "title": "Créer un nouveau document à partir de celui-ci",
                        "css": "btn icon only",
                        "icon": "copy",
                    },
                }
            )

        if self.request.has_permission(PERMISSIONS[f"context.delete_{view_type}"]):
            url = get_task_url(self.request, suffix="/delete")
            result.append(
                {
                    "widget": "POSTButton",
                    "option": {
                        "url": url,
                        "title": "Supprimer définitivement ce document",
                        "css": "btn icon only negative",
                        "icon": "trash-alt",
                        "confirm_msg": (
                            "Êtes-vous sûr de vouloir supprimer cet élément ?"
                        ),
                    },
                }
            )

        return result

    def pre_format(self, datas, edit=False):
        # Si on change l'input mode, on change les classes rattachés à la Task
        if edit:
            input_mode = datas.pop("input_mode", None)
            if input_mode == "price_study":
                self.context.set_price_study(self.request)
            elif input_mode == "classic" and self.context.has_price_study():
                self.context.unset_price_study(self.request)
        return super().pre_format(datas, edit=edit)

    def after_flush(self, entry, edit, attributes):
        if edit:
            action = "update"
        else:
            raise Exception("We should not add a task through this api endpoint")
            action = "add"
        task_on_before_commit(self.request, self.context, action, attributes)
        return super().after_flush(entry, edit, attributes)

    def bulk_edit_post_endpoint(self):
        """
        Permet de mettre la même tva ou le même product_id sur toutes les task_line de la Task
        """
        post_data = self.get_posted_data()
        try:
            schema = get_tva_id_product_id_schema(
                self.request, internal=self.context.internal
            )
            schema = schema.bind(request=self.request)
            validated_data = schema.deserialize(post_data)

        except colander.Invalid as err:
            self.logger.exception("  - Erreur")
            self.logger.exception(post_data)
            raise RestError(err.asdict(), 400)

        tva_id = validated_data["tva_id"]
        product_id = validated_data.get("product_id")
        tva = get_tva_by_id(self.request, tva_id)
        if not tva:
            raise RestError({"tva_id": ["TVA inconnue"]}, 400)
        product = get_product_by_id(self.request, product_id)
        bulk_edit_tva_and_product_id(self.request, self.context, tva, product)
        taskline_on_before_commit(
            self.request,
            self.context.all_lines,
            "update",
            {"tva_id": tva_id, "product_id": product_id},
        )
        return self.get()


class TaskLineGroupRestView(BaseRestView):
    """
    Rest views handling the task line groups

    Collection views : Context Task

        GET

            Return all the items belonging to the parent task

        POST

            Add a new item

    Item views

        GET

            Return the Item

        PUT/PATCH

            Edit the item

        DELETE

            Delete the item
    """

    def get_schema(self, submitted):
        """
        Return the schema for TaskLineGroup add/edition

        :param dict submitted: The submitted datas
        :returns: A colander.Schema
        """
        excludes = ("task_id",)
        return get_add_edit_tasklinegroup_schema(self.request, excludes=excludes)

    def collection_get(self):
        """
        View returning the task line groups attached to this estimation
        """
        return self.context.line_groups

    def post_format(self, entry, edit, attributes):
        """
        Associate a newly created element to the parent task
        """
        if not edit:
            entry.task = self.context
        return entry

    def post_load_groups_from_catalog_view(self):
        """
        View handling product group loading

        expects sale_product_group_quantities: {id1: quantity1, id2: quantity2} as json POST params
        """
        sale_product_groups = self.request.json_body.get("sale_products", [])
        # handle the case where sale_product_quantity is not retrieved in the request
        groups = []
        for id_, quantity in sale_product_groups.items():
            group = tasklinegroup_from_sale_product_work(
                self.request,
                sale_product_work=get_model_by_id(self.request, SaleProductWork, id_),
                document=self.context,
                quantity=quantity,
            )
            self.context.line_groups.append(group)
            groups.append(group)
        self.request.dbsession.flush()
        if groups:
            tasklinegroup_on_before_commit(self.request, groups, "add")
        return groups

    def on_delete(self):
        tasklinegroup_on_before_commit(self.request, [self.context], "delete")

    def after_flush(self, entry, edit, attributes):
        if edit:
            action = "update"
        else:
            action = "add"
        tasklinegroup_on_before_commit(self.request, [entry], action, attributes)
        return super().after_flush(entry, edit, attributes)

    def bulk_edit_post_endpoint(self):
        """
        Permet de mettre la même tva ou le même product_id sur toutes les task_line du groupe
        """
        post_data = self.get_posted_data()
        try:
            schema = get_tva_id_product_id_schema(
                self.request, internal=self.context.task.internal
            )
            schema = schema.bind(request=self.request)
            validated_data = schema.deserialize(post_data)

        except colander.Invalid as err:
            self.logger.exception("  - Erreur")
            self.logger.exception(post_data)
            raise RestError(err.asdict(), 400)

        tva_id = validated_data["tva_id"]
        product_id = validated_data.get("product_id")
        tva = get_tva_by_id(self.request, tva_id)
        if not tva:
            raise RestError({"tva_id": ["TVA inconnue"]}, 400)
        product = get_product_by_id(self.request, product_id)
        bulk_edit_tva_and_product_id(self.request, self.context, tva, product)
        # On indique que les tasklines du groupe ont été modifiées
        taskline_on_before_commit(
            self.request,
            self.context.lines,
            "update",
            {"tva_id": tva_id, "product_id": product_id},
        )
        return self.get()


class TaskLineRestView(BaseRestView):
    """
    Rest views used to handle the task lines

    Collection views : Context Task

        GET

            Return all the items belonging to the parent task

        POST

            Add a new item

    Item views

        GET

            Return the Item

        PUT/PATCH

            Edit the item

        DELETE

            Delete the item
    """

    def get_schema(self, submitted):
        """
        Return the schema for TaskLine add/edition

        :param dict submitted: The submitted datas
        :returns: A colander.Schema
        """
        excludes = ("group_id",)
        return get_add_edit_taskline_schema(self.request, excludes=excludes)

    def collection_get(self):
        return self.context.lines

    def post_format(self, entry, edit, attributes):
        """
        Associate a newly created element to the parent group
        """
        if not edit:
            self.context.lines.append(entry)

        if (
            "tva_id" in attributes
            and "product_id" not in attributes
            and entry.tva_id is not None
        ):
            tva = get_tva_by_id(self.request, entry.tva_id)
            product = get_task_default_product(
                self.request, self.context.task, default_tva=tva
            )
            if product:
                entry.product_id = product.id
            else:
                entry.product_id = None
        return entry

    def post_load_from_catalog_view(self):
        """
        View handling sale_product loading

        expects these json POST params :
        - sale_product_ids: [id1, id2]
        - sale_product_quantities: [qty1, qty2]
        """
        sale_products: dict = self.request.json_body.get("sale_products", {})

        lines = []
        for id_, quantity in sale_products.items():
            line = taskline_from_sale_product(
                self.request,
                get_model_by_id(self.request, BaseSaleProduct, id_),
                quantity=quantity,
                document=self.context.task,
            )
            self.context.lines.append(line)
            lines.append(line)

        self.request.dbsession.flush()
        if lines:
            taskline_on_before_commit(self.request, lines, "add")
        return lines

    def on_delete(self):
        taskline_on_before_commit(self.request, [self.context], "delete")

    def after_flush(self, entry, edit, attributes):
        if edit:
            state = "update"
        else:
            state = "add"
        taskline_on_before_commit(self.request, [entry], state, attributes)
        return super().after_flush(entry, edit, attributes)


class DiscountLineRestView(BaseRestView):
    """
    Rest views used to handle the task lines


    Collection views : Context Task

        GET

            Return all the items belonging to the parent task

        POST

            Add a new item

    Item views

        GET

            Return the Item

        PUT/PATCH

            Edit the item

        DELETE

            Delete the item
    """

    def get_schema(self, submitted):
        """
        Return the schema for DiscountLine add/edition

        :param dict submitted: The submitted datas
        :returns: A colander.Schema
        """
        excludes = ("task_id",)
        schema = get_add_edit_discountline_schema(self.request, excludes=excludes)
        return schema

    def collection_get(self):
        """
        View returning the task line groups attached to this estimation
        """
        return self.context.discounts

    def post_format(self, entry, edit, attributes):
        """
        Associate a newly created element to the parent task
        after edition
        """
        if not edit:
            entry.task = self.context
        return entry

    def _get_percent_discount_lines(self, description, percent):
        """
        Build DiscountLine instances representing a percentage of the global
        values

        One DiscountLine is generated for each tva used in the document

        :param str description: A description for the discounts
        :param float percent: The percentage to apply
        """
        lines = []

        if percent is not None and description is not None:
            if self.context.mode == "ttc":
                tva_parts = self.context.tva_ttc_parts()
            else:
                tva_parts = self.context.tva_ht_parts()

            for tva, ht in list(tva_parts.items()):
                amount = percentage(ht, percent)
                line = DiscountLine(
                    description=description,
                    amount=amount,
                    tva=tva,
                )
                self.request.dbsession.add(line)
                self.request.dbsession.flush()
                self.context.discounts.append(line)
                lines.append(line)
        else:
            raise RestError(
                {"errors": ["La description ou le pourcentage ne peuvent être vide"]},
                400,
            )
        if lines:
            discountline_on_before_commit(self.request, lines, "add")
        return lines

    def post_percent_discount_view(self):
        """
        View handling percent discount configuration

        Generates discounts for each tva used in this document

        current context : Invoice/Estimation/CancelInvoice
        """
        percent = self.request.json_body.get("percentage")
        description = self.request.json_body.get("description")
        percent = str_to_float(percent, None)
        return self._get_percent_discount_lines(description, percent)

    def on_delete(self):
        discountline_on_before_commit(self.request, [self.context], "delete")

    def after_flush(self, entry, edit, attributes):
        if edit:
            state = "update"
        else:
            state = "add"
        discountline_on_before_commit(self.request, [entry], state, attributes)
        return super().after_flush(entry, edit, attributes)


class PostTTCLineRestView(BaseRestView):
    """
    Rest views used to handle the task lines


    Collection views : Context Task

        GET

            Return all the items belonging to the parent task

        POST

            Add a new item

    Item views

        GET

            Return the Item

        PUT/PATCH

            Edit the item

        DELETE

            Delete the item
    """

    def get_schema(self, submitted):
        """
        Return the schema for PostTTCLine add/edition

        :param dict submitted: The submitted datas
        :returns: A colander.Schema
        """
        excludes = ("task_id",)
        schema = get_add_edit_post_ttc_line_schema(self.request, excludes=excludes)
        return schema

    def collection_get(self):
        """
        View returning the task line groups attached to this estimation
        """
        return self.context.post_ttc_lines

    def post_format(self, entry, edit, attributes):
        """
        Associate a newly created element to the parent task
        after edition
        """
        if not edit:
            entry.task = self.context
        return entry

    def on_delete(self):
        post_ttc_line_on_before_commit(self.request, self.context, "delete")

    def after_flush(self, entry, edit, attributes):
        if edit:
            state = "update"
        else:
            state = "add"
        post_ttc_line_on_before_commit(self.request, entry, state, attributes)
        return super().after_flush(entry, edit, attributes)


class TaskFileRequirementRestView(BaseRestView):
    def collection_get(self):
        return self.context.file_requirements

    def get(self):
        return self.context

    def validation_status(self):
        validation_status = self.request.json_body.get("validation_status")
        if validation_status in self.context.VALIDATION_STATUS:
            return self.context.set_validation_status(validation_status)
        else:
            return RestError(["Statut inconnu"])


class TaskFileRestView(FileRestView):
    def get_schema(self, submitted):
        return get_file_upload_schema([ImageResizer(1200, 1200, "PDF")])


def task_total_view(context, request):
    """
    Return the Task total representation in json

    Allow to avoid computing totals js side
    """
    return context.json_totals(request)


class TaskStatusLogEntryRestView(StatusLogEntryRestView):
    def get_node_url(self, node):
        return get_task_url(self.request, task=node)
