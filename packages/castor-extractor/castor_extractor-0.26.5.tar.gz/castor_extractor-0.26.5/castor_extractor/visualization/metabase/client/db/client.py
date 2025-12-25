import json
import logging
import os

from sqlalchemy.exc import OperationalError

from .....utils import ExtractionQuery, PostgresClient, SerializedAsset
from ...assets import EXPORTED_FIELDS, MetabaseAsset
from ...errors import EncryptionSecretKeyRequired, MetabaseLoginError
from ..decryption import decrypt
from ..shared import DETAILS_KEY, get_dbname_from_details
from .credentials import MetabaseDbCredentials

logger = logging.getLogger(__name__)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

SQL_FILE_PATH = "queries/{name}.sql"


class DbClient(PostgresClient):
    """
    Connect to Metabase Database and fetch main assets.
    """

    @staticmethod
    def name() -> str:
        """return the name of the client"""
        return "Metabase/DB"

    def _engine_options(self, credentials: dict) -> dict:
        sslmode = "require" if self.require_ssl else "prefer"
        return {"connect_args": {"sslmode": sslmode}}

    def __init__(
        self,
        credentials: MetabaseDbCredentials,
    ):
        self._credentials = credentials
        self.require_ssl = self._credentials.require_ssl
        try:
            super().__init__(self._credentials.dict())
        except OperationalError as err:
            raise MetabaseLoginError(
                credentials_info=self._credentials,
                error_details=err.args,
            )

    def _load_query(self, name: str) -> ExtractionQuery:
        """load SQL text from file"""
        filename = SQL_FILE_PATH.format(name=name)
        path = os.path.join(CURRENT_DIR, filename)
        with open(path) as f:
            content = f.read()
            statement = content.format(schema=self._credentials.schema_)
            return ExtractionQuery(statement=statement, params={})

    @property
    def base_url(self) -> str:
        """Fetches the `base_url` of the Metabase instance"""
        query = self._load_query(name="base_url")
        rows = list(self.execute(query))
        return rows[0]["value"]

    def _database_specifics(
        self,
        databases: SerializedAsset,
    ) -> SerializedAsset:
        for db in databases:
            assert DETAILS_KEY in db  # this field is expected in database table

            try:
                details = json.loads(db[DETAILS_KEY])
            except json.decoder.JSONDecodeError as err:
                encryption_key = self._credentials.encryption_secret_key
                if not encryption_key:
                    raise EncryptionSecretKeyRequired(
                        credentials_info=self._credentials,
                        error_details=err.args,
                    )
                decrypted = decrypt(db[DETAILS_KEY], encryption_key)
                details = json.loads(decrypted)

            db["dbname"] = get_dbname_from_details(details)

        return databases

    def fetch(self, asset: MetabaseAsset) -> SerializedAsset:
        """fetches the given asset"""
        query = self._load_query(asset.value.lower())
        assets = list(self.execute(query))

        if asset == MetabaseAsset.DATABASE:
            assets = self._database_specifics(assets)

        logger.info(f"Fetching {asset.name} ({len(assets)} results)")

        # keep interesting fields
        return [
            {key: e.get(key) for key in EXPORTED_FIELDS[asset]} for e in assets
        ]
