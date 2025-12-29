import logging
from typing import Dict, Iterable, List, Optional, Union

import colander
import deform
from sqlalchemy import func, inspect, or_, select
from sqlalchemy.orm import load_only

from caerp.consts.permissions import PERMISSIONS
from caerp.forms.company import (
    DECIMAL_TO_DISPLAY_VALUES,
    get_company_schema,
    get_company_task_mention_filter_schema,
    get_company_task_mention_schema,
    get_mapsearch_schema,
)
from caerp.forms.files import (
    FileUploadSchema,
    ImageNode,
    deferred_parent_id_validator,
    get_file_upload_preparer,
)
from caerp.forms.jsonschema import convert_to_jsonschema
from caerp.forms.user import get_antenne_options, get_users_options
from caerp.models.base import DBBASE
from caerp.models.company import Company, CompanyActivity
from caerp.models.files import File
from caerp.models.task.mentions import CompanyTaskMention
from caerp.models.user.login import ACCOUNT_TYPES, Login
from caerp.models.user.user import User
from caerp.services.serializers import serializers
from caerp.services.serializers.base import BaseSerializer
from caerp.services.smtp.smtp import (
    get_company_smtp_by_company_id,
    get_smtp_by_company_id,
    smtp_settings_to_json,
)
from caerp.services.task.mentions import company_task_mention_is_used
from caerp.utils.image import ImageRatio, ImageResizer
from caerp.utils.rest.parameters import FieldOptions, LoadOptions
from caerp.views import BaseRestView, BaseRestViewV2, RestListMixinClass
from caerp.views.files.rest_api import FileRestView
from caerp.views.status.rest_api import StatusLogEntryRestView
from caerp.views.status.utils import get_visibility_options

from .routes import (
    API_HEADER_ITEM_ROUTE,
    API_HEADER_ROUTE,
    API_ITEM_ROUTE,
    API_LOGO_ITEM_ROUTE,
    API_LOGO_ROUTE,
    API_ROUTE,
    API_ROUTE_GEOJSON,
    API_TASK_MENTION_ITEM_ROUTE,
    API_TASK_MENTION_ROUTE,
)
from .views import get_enabled_bookeeping_modules

logger = logging.getLogger(__name__)


class CompanyMapSearchTools:
    """
    Filters and schema for map search.
    Sur la même logique que UserFilterTools
    """

    list_schema = get_mapsearch_schema()

    def filter_search(self, query, appstruct):
        search = appstruct.get("search")
        if search:
            query = query.filter(
                or_(
                    Company.name.like("%" + search + "%"),
                    Company.goal.like("%" + search + "%"),
                    Company.employees.any(User.lastname.like("%" + search + "%")),
                    Company.employees.any(User.firstname.like("%" + search + "%")),
                    Company.employees.any(
                        User.login.has(Login.login.like("%" + search + "%"))
                    ),
                ),
            )
        return query

    def filter_activity_id(self, query, appstruct):
        activity_id = appstruct.get("activity_id")
        if activity_id:
            query = query.filter(
                Company.activities.any(CompanyActivity.id == activity_id)
            )
        return query

    def filter_postcode(self, query, appstruct):
        postcode = appstruct.get("postcode")
        if postcode:
            query = query.filter(Company.zip_code == postcode)
        return query


class CompanyRestListMixin(
    CompanyMapSearchTools,
    RestListMixinClass,
):
    """
    Rest list logic for Company
    """

    # list_schema defined in the filter class
    authorized_fields = {
        "id",
        "name",
        "goal",
        "email",
        "mobile",
        "phone",
        "zip_code",
        "latitude",
        "longitude",
        "users_gallery",
        "activities_labels",
    }

    def query(self):
        query = Company.query()
        fields = self.collection_fields()
        if fields:
            logger.info("Returning only {}".format(fields))
            mapper_fields = set(self._mapper_fields()).intersection(fields)
            query = query.options(load_only(*mapper_fields))
        return query

    def format_collection(self, query):
        fields = self.collection_fields()
        return [
            dict((field, getattr(company, field)) for field in fields)
            for company in query
        ]

    def collection_fields(self):
        fields = set(self.request.params.getall("fields"))

        # Only authorize public informations for non-admins
        if not self.request.has_permission(PERMISSIONS["global.company_view"]):
            fields = fields.intersection(self.authorized_fields)
        if not fields:
            fields = ["id", "name"]
        return fields

    @staticmethod
    def _mapper_fields() -> Iterable[str]:
        """
        Returns mapped column names available on a Company
        :return:
        """
        mapper = inspect(Company)
        return (i.key for i in mapper.attrs)


class CompanyRestView(
    CompanyRestListMixin,
    BaseRestView,
):
    """
    Rest Class for company
    """

    def get_schema(self, submitted: Optional[dict] = None) -> colander.Schema:
        is_accountant = bool(
            self.request.has_permission(PERMISSIONS["global.manage_accounting"])
        )
        is_company_admin = bool(
            self.request.has_permission(PERMISSIONS["global.create_company"])
        )
        is_company_supervisor = bool(
            self.request.has_permission(PERMISSIONS["global.company_view"])
        )
        modules = get_enabled_bookeeping_modules()
        excludes = [key for key, value in modules.items() if not value]

        return get_company_schema(
            self.request,
            is_accountant=is_accountant,
            is_company_admin=is_company_admin,
            is_company_supervisor=is_company_supervisor,
            excludes=excludes,
        )

    def pre_format(self, datas, edit=False):
        result = super().pre_format(datas, edit)

        # Exit la modification du nom pour les personnes n'ayant pas le rôle
        # global.create_company
        if (
            edit
            and "name" in result
            and not self.request.has_permission("global.create_company")
        ):
            result.pop("name")
        return result

    def after_flush(self, company, edit, appstruct):
        user_id = appstruct.pop("user_id", None)
        if user_id is not None:
            user_account = User.get(user_id)
            if user_account is not None:
                company.employees.append(user_account)
                company.set_datas_from_user(user_account)
        return company

    def format_item_result(self, model) -> Union[dict, object]:
        out = super().format_item_result(model)
        if isinstance(out, DBBASE):
            out: dict = out.__json__(self.request)

        if "activities" in out:
            # De-hydrate property
            out["activities"] = [i.id for i in out["activities"]]

        company_smtp_settings = get_smtp_by_company_id(self.request, model.id)
        if company_smtp_settings:
            out["company_smtp_settings_id"] = company_smtp_settings.id
        smtp_settings = get_company_smtp_by_company_id(self.request, model.id)
        if smtp_settings:
            out["smtp_settings"] = smtp_settings_to_json(self.request, smtp_settings)
        return out

    @staticmethod
    def _get_decimal_to_display_options() -> List[Dict]:
        return [{"id": id, "label": label} for id, label in DECIMAL_TO_DISPLAY_VALUES]

    @staticmethod
    def _get_antennes_options():
        return [{"id": id, "label": label} for id, label in get_antenne_options()]

    @staticmethod
    def _get_follower_options():
        return [
            {"id": id, "label": label}
            for id, label in get_users_options(
                account_type=ACCOUNT_TYPES["equipe_appui"]
            )
        ]

    @staticmethod
    def _get_deposit_options():
        return [{"id": value, "label": f"{value} %"} for value in range(0, 90, 10)]

    def form_config(self):
        if isinstance(self.context, Company):
            company_id = self.context.id
        else:
            company_id = None

        return {
            "options": {
                "company_id": company_id,
                "visibilities": get_visibility_options(self.request),
                "activities": self.get_activities_options(),
                "decimal_to_display": self._get_decimal_to_display_options(),
                "antennes_options": self._get_antennes_options(),
                "follower_options": self._get_follower_options(),
                "deposit_options": self._get_deposit_options(),
            },
            "schemas": {
                "default": convert_to_jsonschema(self.get_schema()),
                "company_task_mention": convert_to_jsonschema(
                    get_company_task_mention_schema(self.request)
                ),
            },
        }

    @staticmethod
    def get_activities_options():
        return [
            {"id": c.id, "label": c.label}
            for c in CompanyActivity.query("id", "label").all()
        ]


class CompanyRestGeoJSONView(CompanyRestView):
    """
    Get companies in GeoJSON format
    """

    def collection_fields(self):
        fields = super().collection_fields()
        fields.add("latitude")
        fields.add("longitude")
        return fields

    def query(self):
        query = super().query()
        query = query.filter(Company.latitude.isnot(None))
        query = query.filter(Company.longitude.isnot(None))
        return query

    def company_to_geojson_feature(self, company: Company):
        fields = self.collection_fields()
        db_fields = [
            i
            for i in fields
            if i not in ("users_gallery", "latitude", "longitude", "activities_labels")
        ]
        properties = {key: getattr(company, key) for key in db_fields}
        if "users_gallery" in fields:
            properties["users_gallery"] = [
                dict(
                    fullname=f"{user.firstname} {user.lastname}",
                    logo_url=(
                        f"/files/{user.photo_id}?action=download"
                        if user.photo_id and user.photo_is_publishable
                        else None
                    ),
                )
                for user in company.employees
            ]
        if "activities_labels" in fields:
            properties["activities_labels"] = [i.label for i in company.activities]

        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [company.longitude, company.latitude],
            },
            "properties": properties,
        }

    def format_collection(self, query):
        features = [self.company_to_geojson_feature(company) for company in query]
        geojson = {"type": "FeatureCollection", "features": features}

        return geojson


class CompanyLogoSchema(FileUploadSchema):
    filters = [
        ImageResizer(800, 800),
    ]
    upload = ImageNode(preparer=get_file_upload_preparer(filters))
    parent_id = colander.SchemaNode(
        colander.Integer(),
        missing=colander.drop,
        widget=deform.widget.HiddenWidget(),
        validator=deferred_parent_id_validator,
    )


class CompanyLogoRestView(FileRestView):
    def get_schema(self, submitted: Optional[dict] = None):
        return CompanyLogoSchema()


class CompanyHeaderSchema(colander.Schema):
    filters = [
        ImageRatio(4, 1),
        ImageResizer(2000, 500),
    ]
    upload = ImageNode(preparer=get_file_upload_preparer(filters))
    parent_id = colander.SchemaNode(
        colander.Integer(),
        missing=colander.drop,
        widget=deform.widget.HiddenWidget(),
        validator=deferred_parent_id_validator,
    )


class CompanyHeaderRestView(FileRestView):
    def get_schema(self, submitted: Dict):
        return CompanyHeaderSchema()


class CompanyTaskMentionRestView(BaseRestViewV2):
    sort_columns = {"order": "order", "title": "title"}
    default_sort = "order"
    default_sort_direction = "asc"

    default_fields = FieldOptions.from_dict(
        {
            "attributes": [
                "id",
                "label",
                "order",
                "company_id",
                "title",
                "full_text",
                "help_text",
                "active",
            ]
        }
    )

    def get_schema(self, submitted: dict):
        return get_company_task_mention_schema(self.request)

    def _get_serializer(self, fields) -> BaseSerializer:
        company_serializer = serializers["company_task_mentions"]

        result = company_serializer(fields=fields, serializer_registry=serializers)
        return result

    def get_filter_schema(self, load_options: LoadOptions):
        return get_company_task_mention_filter_schema()

    def build_collection_query(
        self, filters: Optional[dict], fields: Optional[FieldOptions]
    ):
        return (
            select(
                CompanyTaskMention,
                func.count(CompanyTaskMention.id).over().label("total"),
            )
            .filter(CompanyTaskMention.company_id == self.context.id)
            .filter(CompanyTaskMention.active == True)
        )

    def post_format(self, entry, edit, attributes):
        if not edit:
            entry.company_id = self.context.id
        return entry

    def form_config(self):
        return {
            "schemas": {
                "default": convert_to_jsonschema(self.get_schema({})),
            }
        }

    def delete(self):
        if company_task_mention_is_used(self.request, self.context.id):
            self.context.active = False
            self.dbsession.merge(self.context)
            return {}
        else:
            return super().delete()


def includeme(config):
    config.add_rest_service(
        factory=CompanyRestView,
        route_name=API_ITEM_ROUTE,
        collection_route_name=API_ROUTE,
        view_rights=PERMISSIONS["company.view"],
        add_rights=PERMISSIONS["global.create_company"],
        edit_rights=PERMISSIONS["context.edit_company"],
        collection_view_rights=PERMISSIONS["global.authenticated"],
        context=Company,
    )

    for route_name, context, permission in (
        (API_ROUTE, None, "global.create_company"),
        # company.view et pas edit car utilisé pour les mémos
        (API_ITEM_ROUTE, Company, "company.view"),
    ):
        # form_config for both add and edit
        config.add_view(
            CompanyRestView,
            attr="form_config",
            route_name=route_name,
            renderer="json",
            request_param="form_config",
            permission=PERMISSIONS[permission],
            context=context,
        )

    config.add_rest_service(
        factory=CompanyRestGeoJSONView,
        collection_route_name=API_ROUTE_GEOJSON,
        collection_view_rights=PERMISSIONS["global.authenticated"],
    )

    config.add_view(
        CompanyRestGeoJSONView,
        attr="form_config",
        route_name=API_ROUTE_GEOJSON,
        renderer="json",
        request_param="form_config",
        permission=PERMISSIONS["global.authenticated"],
    )

    config.add_rest_service(
        StatusLogEntryRestView,
        "/api/v1/companies/{eid}/statuslogentries/{id}",
        collection_route_name="/api/v1/companies/{id}/statuslogentries",
        collection_view_rights=PERMISSIONS["company.view"],
        add_rights=PERMISSIONS["company.view"],
        view_rights=PERMISSIONS["context.view_statuslogentry"],
        edit_rights=PERMISSIONS["context.edit_statuslogentry"],
        delete_rights=PERMISSIONS["context.delete_statuslogentry"],
    )

    config.add_view(
        CompanyLogoRestView,
        request_method="POST",
        attr="post",
        route_name=API_LOGO_ROUTE,
        permission=PERMISSIONS["global.authenticated"],
        require_csrf=True,
        renderer="json",
    )

    config.add_rest_service(
        CompanyLogoRestView,
        route_name=API_LOGO_ITEM_ROUTE,
        view_rights=PERMISSIONS["context.view_file"],
        edit_rights=PERMISSIONS["context.edit_file"],
        delete_rights=PERMISSIONS["context.delete_file"],
        context=File,
    )

    config.add_view(
        CompanyHeaderRestView,
        request_method="POST",
        attr="post",
        route_name=API_HEADER_ROUTE,
        permission=PERMISSIONS["global.authenticated"],
        require_csrf=True,
        renderer="json",
    )

    config.add_rest_service(
        CompanyHeaderRestView,
        route_name=API_HEADER_ITEM_ROUTE,
        view_rights=PERMISSIONS["context.view_file"],
        edit_rights=PERMISSIONS["context.edit_file"],
        delete_rights=PERMISSIONS["context.delete_file"],
        context=File,
    )

    config.add_rest_service(
        CompanyTaskMentionRestView,
        collection_route_name=API_TASK_MENTION_ROUTE,
        collection_context=Company,
        route_name=API_TASK_MENTION_ITEM_ROUTE,
        context=CompanyTaskMention,
        view_rights=PERMISSIONS["company.view"],
        add_rights=PERMISSIONS["context.edit_company"],
        edit_rights=PERMISSIONS["context.edit_company_task_mention"],
        delete_rights=PERMISSIONS["context.edit_company_task_mention"],
    )
    config.add_view(
        CompanyTaskMentionRestView,
        attr="form_config",
        route_name=API_TASK_MENTION_ROUTE,
        context=Company,
        renderer="json",
        request_method="GET",
        request_param="form_config",
        permission=PERMISSIONS["context.edit_company"],
    )
