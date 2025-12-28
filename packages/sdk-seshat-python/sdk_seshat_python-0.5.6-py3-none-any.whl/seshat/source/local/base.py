from seshat.data_class import SFrame
from seshat.general import configs
from seshat.source import Source
from seshat.transformer.merger import Merger


class LocalSource(Source):
    """
    LocalSource is a data source that can read from a local file or an in-memory source.
    """

    def __init__(
        self,
        data_source,
        schema=None,
        mode=configs.DEFAULT_MODE,
        group_keys=None,
        merge_result=False,
        merger: Merger = Merger,
        *args,
        **kwargs
    ):
        super().__init__(
            schema=schema,
            mode=mode,
            group_keys=group_keys,
            merge_result=merge_result,
            merger=merger,
            *args,
            **kwargs
        )
        self.data_source = data_source

    def convert_data_type(self, data) -> SFrame:
        return self.data_class.from_raw(data)

    def fetch(self, *args, **kwargs) -> SFrame:
        d = (
            self.data_class.read_csv(path=self.data_source)
            if isinstance(self.data_source, str)
            else self.data_source
        )

        return self.convert_data_type(d)

    def calculate_complexity(self):
        return 10
