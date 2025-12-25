from argparse import ArgumentParser

from castor_extractor.utils import parse_filled_arguments  # type: ignore
from castor_extractor.visualization import looker_studio  # type: ignore


def main():
    parser = ArgumentParser(
        description="Extract data from Looker Studio and related BigQuery source queries"
    )
    parser.add_argument("-o", "--output", help="Directory to write to")

    mode_group = parser.add_argument_group("Execution mode")
    mode_group.add_argument(
        "--source-queries-only",
        action="store_true",
        default=False,
        help="If selected, only extracts BigQuery source queries (bypasses Looker Studio extraction)",
    )
    mode_group.add_argument(
        "--skip-view-activity-logs",
        action="store_true",
        default=False,
        help="Skip extraction of activity logs (use if credentials lack required scopes)",
    )

    looker_group = parser.add_argument_group("Looker Studio extraction")
    looker_group.add_argument(
        "-c",
        "--credentials",
        help="File path to Service Account credentials with Looker Studio access",
    )
    looker_group.add_argument(
        "-a",
        "--admin-email",
        help="Email of a Google Workspace user with admin access",
    )
    looker_group.add_argument(
        "--users-file-path",
        help=(
            "Optional path to a JSON file with user email addresses "
            'as a list of strings (e.g. ["foo@bar.com", "fee@bar.com"]). '
            "If provided, only extracts assets owned by the specified users."
        ),
    )

    bigquery_group = parser.add_argument_group("Source queries extraction")
    bigquery_group.add_argument(
        "-b",
        "--bigquery-credentials",
        help=(
            "File path to Service Account credentials with BigQuery access. "
            "Can point to the same file as Looker Studio credentials."
        ),
    )
    bigquery_group.add_argument(
        "--db-allowed",
        nargs="*",
        help="Optional list of GCP projects to allow for source queries extraction",
    )
    bigquery_group.add_argument(
        "--db-blocked",
        nargs="*",
        help="Optional list of GCP projects to block from source queries extraction",
    )

    looker_studio.extract_all(**parse_filled_arguments(parser))
