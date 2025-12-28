from dataclasses import dataclass
from typing import List, Literal

from sqlalchemy import make_url

from seshat.data_class import SFrame
from seshat.general.exceptions import DataBaseNotSupportedError
from seshat.transformer import Transformer
from seshat.transformer.schema import Schema

POSTGRES = "psql"


@dataclass
class SaveConfig:
    sf_key: str
    table: str
    schema: Schema
    clear_table: bool = False
    strategy: Literal["insert", "update", "copy"] = "insert"
    indexes: List[List[str] | str] = ()


class Saver(Transformer):
    def __init__(self, url: str, save_configs: List[SaveConfig], *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Check for update configs id columns have been specified
        self.url = url
        db_type = self.db_type
        for config in save_configs:
            if config.strategy == "copy" and db_type != POSTGRES:
                raise DataBaseNotSupportedError(
                    "`copy` command only available in postgresql database"
                )
            elif config.strategy == "update":
                config.schema.get_id()
        self.save_configs = save_configs

    def __call__(self, sf_input: SFrame, *args, **kwargs):
        self.save(sf_input)
        return sf_input

    def calculate_complexity(self):
        return NotImplementedError()

    def save(self, sf: SFrame, *args, **kwargs):
        raise NotImplementedError()

    @property
    def db_type(self):
        url_obj = make_url(self.url)
        if url_obj.drivername in ["postgresql", "postgresql+psycopg2"]:
            return POSTGRES
