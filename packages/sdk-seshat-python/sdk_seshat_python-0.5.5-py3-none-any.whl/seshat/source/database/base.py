from typing import Optional

from sqlalchemy import Engine, text

from seshat.data_class import SFrame, DFrame
from seshat.general.exceptions import InvalidArgumentsError
from seshat.source import Source
from seshat.source.mixins import SQLMixin
from seshat.transformer.schema import Schema


class SQLDBSource(SQLMixin, Source):
    """
    This class is responsible for fetching data from sql database using filters and query.
    """

    _engine: Engine = None
    filters: Optional[dict]
    table_name: str
    schema: Optional[Schema]
    limit: int
    query: str

    def __init__(
        self,
        url,
        filters=None,
        table_name=None,
        limit=None,
        query=None,
        query_fn=None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        if not any([table_name, query, query_fn]):
            raise InvalidArgumentsError(
                "At least one of the query, table_name and query_fn must be specified"
            )

        self.url = url
        self.table_name = table_name
        self.filters = filters or {}
        self.limit = limit
        self.query = query
        self.query_fn = query_fn

    def fetch(self, *args, **kwargs) -> SFrame:
        query_result = self.get_from_db(
            text(self.get_query(self.filters, *args, **kwargs))
        )
        return self.convert_data_type(query_result)

    def convert_data_type(self, data) -> SFrame:
        return super().convert_data_type(DFrame.from_raw(data).to_raw())

    def calculate_complexity(self):
        return 30
