COMMON_DASH_LOOK_FIELDS = (
    "id",
    "title",
    "description",
    "folder_id",
    "created_at",
    "deleted_at",
    "last_accessed_at",
    "last_viewed_at",
    "view_count",
    "user_id",
)
FOLDER_FIELDS = (
    "id",
    "name",
    "parent_id",
    "creator_id",
    "is_personal",
    "is_personal_descendant",
)

DASHBOARD_FILTERS = (
    "id",
    "name",
    "title",
    "type",
    "model",
    "name",
    "dimension",
)

DASHBOARD_ELEMENTS = (
    "id",
    "body_text",
    "note_text",
    "subtitle_text",
    "title",
    "title_text",
    "title_hidden",
    "type",
    {
        "query": ("model", "view", "fields"),
        "look": ("id", {"query": ("model", "view", "fields")}),
        "result_maker": (
            "id",
            "vis_config",
            {"query": ("model", "view", "fields")},
        ),
    },
)

DASHBOARD_FIELDS = (
    *COMMON_DASH_LOOK_FIELDS,
    {
        "dashboard_elements": DASHBOARD_ELEMENTS,
        "dashboard_filters": DASHBOARD_FILTERS,
        "slug": "slug",
    },
)

LOOK_FIELDS = (
    *COMMON_DASH_LOOK_FIELDS,
    "updated_at",
    "last_updater_id",
    "query_id",
    "is_run_on_load",
    "model",  # { id, label }
)

USER_FIELDS = (
    "id",
    "avatar_url",
    "display_name",
    "email",
    "is_disabled",
    "group_ids",
    "role_ids",
)
LOOKML_FIELDS = (
    "name",
    "label",
    "has_content",
    "project_name",
    {"explores": ("name", "description", "label", "hidden", "group_label")},
)

CONNECTION_FIELDS = (
    "name",
    "dialect",
    "pdts_enabled",
    "host",
    "database",
    "schema",
    "tmp_db_name",
    "jdbc_additional_params",
    "dialect_name",
    "created_at",
    "user_id",
    "example",
    "user_attribute_fields",
    "sql_writing_with_info_schema",
)

PROJECT_FIELDS = (
    "id",
    "name",
    "uses_git",
    "git_remote_url",
    "git_username",
    "git_production_branch_name",
    "use_git_cookie_auth",
    "git_password_user_attribute",
    "git_service_name",
    "git_application_server_http_port",
    "git_application_server_http_scheme",
    "pull_request_mode",
    "validation_required",
    "git_release_mgmt_enabled",
    "allow_warnings",
    "is_example",
)

EXPLORE_FIELD_FIELDS = (
    "description",
    "field_group_label",
    "field_group_variant",
    "hidden",
    "is_filter",
    "label",
    "label_short",
    "measure",
    "name",
    "parameter",
    "primary_key",
    "project_name",
    "scope",
    "sortable",
    "sql",
    "tags",  # string[]
    "type",
    "view",
    "view_label",
    "times_used",
)

EXPLORE_JOIN_FIELDS = (
    "name",
    "dependent_fields",  # string[]
    "fields",  # string[]
    "foreign_key",
    "from_",
    "outer_only",
    "relationship",
    "required_joins",  # string[]
    "sql_foreign_key",
    "sql_on",
    "sql_table_name",
    "type",
    "view_label",
)

EXPLORE_FIELDS = (
    "id",
    "description",
    "name",
    "label",
    "title",
    "scopes",  # string[]
    "project_name",
    "model_name",
    "view_name",
    "hidden",
    "sql_table_name",
    "group_label",
    "tags",  # string[]
    {
        "fields": {
            "dimensions": EXPLORE_FIELD_FIELDS,
            "measures": EXPLORE_FIELD_FIELDS,
        },
        "joins": EXPLORE_JOIN_FIELDS,
    },
)

GROUPS_HIERARCHY_FIELDS = (
    "id",
    "include_by_default",
    "name",
    "user_count",
    "parent_group_ids",
)

GROUPS_ROLES_FIELDS = (
    "can_add_to_content_metadata",
    "id",
    "name",
    "user_count",
    {
        "roles": (
            "id",
            "name",
            {"permission_set": ("id", "name", "permission")},
            {"model_set": ("id", "models", "name")},
        ),
    },
)

CONTENT_VIEWS_FIELDS = (
    "dashboard_id",
    "look_id",
    "start_of_week_date",
    "user_id",
    "view_count",
)
CONTENT_VIEWS_HISTORY_DAYS = 30

USERS_ATTRIBUTES_FIELDS = ("default_value", "id", "label", "name", "type")


# Model from looker
LOOKML_PROJECT_NAME_BLOCKLIST = ("looker-data", "system__activity")
