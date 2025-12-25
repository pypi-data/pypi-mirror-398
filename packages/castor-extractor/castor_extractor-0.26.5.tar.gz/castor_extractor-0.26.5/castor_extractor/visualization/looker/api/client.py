import functools
import logging
from collections.abc import Callable, Iterator, Sequence
from datetime import date, timedelta

from dateutil.utils import today
from looker_sdk import init40
from looker_sdk.sdk.api40.models import (
    ContentView,
    Dashboard,
    DBConnection,
    Folder,
    GroupHierarchy,
    GroupSearch,
    Look,
    LookmlModel,
    LookmlModelExplore,
    Project,
    User,
    UserAttribute,
)
from looker_sdk.sdk.constants import sdk_version

from ....utils import Pager, PagerLogger, SafeMode, past_date, safe_mode
from ..assets import LookerAsset
from ..constants import DEFAULT_LOOKER_PAGE_SIZE
from ..fields import format_fields
from .constants import (
    CONNECTION_FIELDS,
    CONTENT_VIEWS_FIELDS,
    CONTENT_VIEWS_HISTORY_DAYS,
    DASHBOARD_FIELDS,
    FOLDER_FIELDS,
    GROUPS_HIERARCHY_FIELDS,
    GROUPS_ROLES_FIELDS,
    LOOK_FIELDS,
    LOOKML_FIELDS,
    LOOKML_PROJECT_NAME_BLOCKLIST,
    PROJECT_FIELDS,
    USER_FIELDS,
    USERS_ATTRIBUTES_FIELDS,
)
from .credentials import LookerCredentials
from .sdk import CastorApiSettings, has_admin_permissions

logger = logging.getLogger(__name__)


OnApiCall = Callable[[], None]


def _mondays(history_depth_in_days: int) -> Iterator[date]:
    """
    Fetch all Mondays of the elapsed period
    """
    _MSG = "History depth must be strictly positive"
    assert history_depth_in_days > 0, _MSG
    current_date = past_date(history_depth_in_days)
    end_date = today().date()
    while current_date < end_date:
        if current_date.weekday() == 0:
            yield current_date
        current_date += timedelta(days=1)


class ApiPagerLogger(PagerLogger):
    def __init__(self, on_api_call: OnApiCall | None):
        self._on_api_call = on_api_call

    def on_page(self, page: int, count: int):
        logger.info(f"Fetched page {page} / {count} results")
        self._on_api_call and self._on_api_call()

    def on_success(self, page: int, total: int):
        logger.info(f"All page fetched: {page} pages / {total} results")


class ApiClient:
    """Looker client"""

    def __init__(
        self,
        credentials: LookerCredentials,
        on_api_call: OnApiCall = lambda: None,
        safe_mode: SafeMode | None = None,
        page_size: int = DEFAULT_LOOKER_PAGE_SIZE,
    ):
        settings = CastorApiSettings(
            credentials=credentials, sdk_version=sdk_version
        )
        sdk = init40(config_settings=settings)
        if not has_admin_permissions(sdk):
            raise PermissionError("User does not have admin access.")
        else:
            self._sdk = sdk
        self._on_api_call = on_api_call
        self._logger = ApiPagerLogger(on_api_call)
        self.per_page = page_size
        self._safe_mode = safe_mode

    def folders(self) -> list[Folder]:
        """Lists folders of the given Looker account"""

        def _search(page: int, per_page: int) -> Sequence[Folder]:
            return self._sdk.search_folders(
                fields=format_fields(FOLDER_FIELDS),
                per_page=per_page,
                page=page,
            )

        return Pager(_search, logger=self._logger).all(per_page=self.per_page)

    def dashboards(self, folder_id: str | None = None) -> list[Dashboard]:
        """
        Lists dashboards of the given Looker account using pagination.
        The optional folder_id allows restricting the search to the given folder.
        """

        def _search(
            page: int | None = None,
            per_page: int | None = None,
        ) -> Sequence[Dashboard]:
            return self._sdk.search_dashboards(
                folder_id=folder_id,
                fields=format_fields(DASHBOARD_FIELDS),
                per_page=per_page,
                page=page,
            )

        if folder_id:
            return list(_search())  # no pagination when using folder filter

        return Pager(_search, logger=self._logger).all(per_page=self.per_page)

    def looks(self, folder_id: str | None = None) -> list[Look]:
        """
        Fetch looks via `search_looks` using pagination. The optional folder_id
        allows restricting the search to the given folder.
        https://developers.looker.com/api/explorer/4.0/methods/Look/search_looks
        """

        def _search(
            page: int | None = None,
            per_page: int | None = None,
        ) -> Sequence[Look]:
            return self._sdk.search_looks(
                folder_id=folder_id,
                fields=format_fields(LOOK_FIELDS),
                per_page=per_page,
                page=page,
            )

        if folder_id:
            return list(_search())  # no pagination when using folder filter

        return Pager(_search, logger=self._logger).all(per_page=self.per_page)

    def _all_looks(self) -> list[Look]:
        """
        fetch looks via `all_looks`
        https://castor.cloud.looker.com/extensions/marketplace_extension_api_explorer::api-explorer/4.0/methods/Look/all_looks
        """
        # No pagination : see https://community.looker.com/looker-api-77/api-paging-limits-14598
        return list(self._sdk.all_looks(fields=format_fields(LOOK_FIELDS)))

    def users(self) -> list[User]:
        """Lists users of the given Looker account"""

        def _search(page: int, per_page: int) -> Sequence[User]:
            # HACK:
            # We use verified_looker_employee=False (filter out Looker employees)
            # Else api returns an empty list when no parameters are specified
            return self._sdk.search_users(
                fields=format_fields(USER_FIELDS),
                per_page=per_page,
                page=page,
                verified_looker_employee=False,
            )

        return Pager(_search, logger=self._logger).all(per_page=self.per_page)

    def lookml_models(self) -> list[LookmlModel]:
        """Iterates LookML models of the given Looker account"""

        models = self._sdk.all_lookml_models(
            fields=format_fields(LOOKML_FIELDS),
        )

        logger.info("All LookML models fetched")
        self._on_api_call()

        return [
            model
            for model in models
            if model.project_name not in LOOKML_PROJECT_NAME_BLOCKLIST
        ]

    def explores(
        self,
        explore_names=Iterator[tuple[str, str]],
    ) -> Iterator[LookmlModelExplore]:
        """Iterates explores of the given Looker account for the provided model/explore names"""

        @safe_mode(self._safe_mode)
        def _call(model_name: str, explore_name: str) -> LookmlModelExplore:
            explore = self._sdk.lookml_model_explore(model_name, explore_name)

            logger.info(f"Explore {model_name}/{explore_name} fetched")
            self._on_api_call()
            return explore

        for lookml_model_name, lookml_explore_name_ in explore_names:
            explore_ = _call(lookml_model_name, lookml_explore_name_)
            if explore_ is not None:
                yield explore_

    def connections(self) -> list[DBConnection]:
        """Lists databases connections of the given Looker account"""

        connections = self._sdk.all_connections(
            fields=format_fields(CONNECTION_FIELDS),
        )

        logger.info("All looker connections fetched")
        self._on_api_call()

        return list(connections)

    def projects(self) -> list[Project]:
        """Lists projects of the given Looker account"""

        projects = self._sdk.all_projects(fields=format_fields(PROJECT_FIELDS))

        logger.info("All looker projects fetched")
        self._on_api_call()

        return list(projects)

    def groups_hierarchy(self) -> list[GroupHierarchy]:
        """Lists groups with hierarchy of the given Looker account"""
        groups_hierarchy = self._sdk.search_groups_with_hierarchy(
            fields=format_fields(GROUPS_HIERARCHY_FIELDS),
        )
        logger.info("All looker groups_hierarchy fetched")
        return list(groups_hierarchy)

    def groups_roles(self) -> list[GroupSearch]:
        """Lists groups with roles of the given Looker account"""
        groups_roles = self._sdk.search_groups_with_roles(
            fields=format_fields(GROUPS_ROLES_FIELDS),
        )
        logger.info("All looker groups_roles fetched")
        return list(groups_roles)

    def content_views(self) -> list[ContentView]:
        """
        List the number of views per {user x week x dashboard|look}
        https://cloud.google.com/looker/docs/reference/looker-api/latest/types/ContentView
        """
        content_views: list[ContentView] = []

        for day in _mondays(history_depth_in_days=CONTENT_VIEWS_HISTORY_DAYS):
            formatted_day = day.strftime("%Y-%m-%d")
            logger.info(f"Fetching content views for week {formatted_day}")

            _fetch = functools.partial(
                self._sdk.search_content_views,
                fields=format_fields(CONTENT_VIEWS_FIELDS),
                start_of_week_date=formatted_day,
                user_id="NOT NULL",
            )
            look_views = list(_fetch(look_id="NOT NULL"))
            dashboard_views = list(_fetch(dashboard_id="NOT NULL"))

            content_views.extend(look_views + dashboard_views)

        logger.info(
            f"All looker content views fetched - {len(content_views)} rows",
        )
        return content_views

    def users_attributes(self) -> list[UserAttribute]:
        """Lists user attributes of the given Looker account"""
        user_attributes = list(
            self._sdk.all_user_attributes(
                fields=format_fields(USERS_ATTRIBUTES_FIELDS),
            ),
        )
        logger.info(
            f"All looker user_attributes fetched - {len(user_attributes)} rows",
        )
        self._on_api_call()

        return user_attributes

    def fetch(
        self,
        asset: LookerAsset,
        *,
        folder_id: str | None = None,
        explore_names: Iterator[tuple[str, str]] | None = None,
    ) -> list:
        if asset == LookerAsset.USERS:
            return self.users()
        if asset == LookerAsset.CONNECTIONS:
            return self.connections()
        if asset == LookerAsset.LOOKS:
            return self.looks(folder_id=folder_id)
        if asset == LookerAsset.DASHBOARDS:
            return self.dashboards(folder_id=folder_id)
        if asset == LookerAsset.CONTENT_VIEWS:
            return self.content_views()
        if asset == LookerAsset.EXPLORES:
            assert explore_names is not None
            return list(self.explores(explore_names=explore_names))
        if asset == LookerAsset.FOLDERS:
            return self.folders()
        if asset == LookerAsset.GROUPS_HIERARCHY:
            return self.groups_hierarchy()
        if asset == LookerAsset.GROUPS_ROLES:
            return self.groups_roles()
        if asset == LookerAsset.LOOKML_MODELS:
            return self.lookml_models()
        if asset == LookerAsset.PROJECTS:
            return self.projects()
        if asset == LookerAsset.USERS_ATTRIBUTES:
            return self.users_attributes()
        raise ValueError(f"Asset {asset.value} is not supported")
