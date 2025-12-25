from ...types import ExternalAsset, classproperty


class LookerAsset(ExternalAsset):
    """Looker assets"""

    CONNECTIONS = "connections"
    CONTENT_VIEWS = "content_views"
    DASHBOARDS = "dashboards"
    EXPLORES = "explores"
    FOLDERS = "folders"
    GROUPS_HIERARCHY = "groups_hierarchy"
    GROUPS_ROLES = "groups_roles"
    LOOKML_MODELS = "lookml_models"
    LOOKS = "looks"
    PROJECTS = "projects"
    USERS = "users"
    USERS_ATTRIBUTES = "users_attributes"

    @classproperty
    def optional(cls) -> set["LookerAsset"]:
        return {
            LookerAsset.CONNECTIONS,
            LookerAsset.CONTENT_VIEWS,
            LookerAsset.GROUPS_HIERARCHY,
            LookerAsset.GROUPS_ROLES,
            LookerAsset.PROJECTS,
            LookerAsset.USERS_ATTRIBUTES,
        }
