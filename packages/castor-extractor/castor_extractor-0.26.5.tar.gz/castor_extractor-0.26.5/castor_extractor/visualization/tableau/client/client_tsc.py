from collections.abc import Iterable, Iterator
from typing import Any

import tableauserverclient as TSC  # type: ignore

from ....utils import JsonType, SerializedAsset
from ..assets import TableauAsset
from .rest_fields import REST_FIELDS


def _pick(element: Any, key: str) -> JsonType:
    if isinstance(element, dict):
        return element[key]
    else:
        return getattr(element, key)


class TableauClientTSC:
    """
    Extract Tableau Assets using TableauServerClient (TSC)
    https://tableau.github.io/server-client-python/docs/api-ref
    """

    def __init__(
        self,
        server: TSC.Server,
    ):
        self._server = server

    def _pick_fields(
        self,
        data: Iterable,
        asset: TableauAsset,
    ) -> Iterator[dict]:
        keys = REST_FIELDS[asset]

        for row in data:
            fields = {key: _pick(row, key) for key in keys}
            if asset == TableauAsset.USER:
                self._server.users.populate_groups(row)
                fields["group_ids"] = [group.id for group in row.groups]

            yield fields

    def fetch(
        self,
        asset: TableauAsset,
    ) -> SerializedAsset:
        if asset == TableauAsset.DATASOURCE:
            data = TSC.Pager(self._server.datasources)

        elif asset == TableauAsset.PROJECT:
            data = TSC.Pager(self._server.projects)

        elif asset == TableauAsset.USAGE:
            data = TSC.Pager(self._server.views, usage=True)

        elif asset == TableauAsset.USER:
            data = TSC.Pager(self._server.users)

        elif asset == TableauAsset.WORKBOOK:
            data = TSC.Pager(self._server.workbooks)

        else:
            raise AssertionError(f"Fetching from TSC not supported for {asset}")

        return list(self._pick_fields(data, asset))
