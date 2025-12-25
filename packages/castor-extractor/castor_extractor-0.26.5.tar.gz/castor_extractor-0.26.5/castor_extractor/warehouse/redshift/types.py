from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


@dataclass
class QueryPart:
    """Query fragment from Redshift"""

    query_id: str
    text: str
    sequence: int
    sequence_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.query_id, str):
            self.query_id = str(self.query_id)


@dataclass
class QueryBuffer:
    """Buffer to hold query parts that have yet to be reassembled"""

    expected: int
    parts: dict[int, str] = field(default_factory=dict)


@dataclass
class AssembledQuery:
    """Reassembled redshift query"""

    query_id: str
    text: str


@dataclass
class QueryMetadata:
    """Query/ddl metadata"""

    aborted: int
    database_id: int
    database_name: str
    end_time: datetime
    label: str
    process_id: str
    query_id: str
    start_time: datetime
    user_id: int
    user_name: str


class LongQuery(Enum):
    METADATA = "metadata"
    PARTS = "parts"
