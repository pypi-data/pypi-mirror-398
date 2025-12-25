import abc
import csv
import enum
import inspect
import json
import typing

from .run_utils import safe_call

if typing.TYPE_CHECKING:
    from ..bases import BasicModel

__all__ = ["Line", "CSVJSONConverter"]


class Line:
    _line = ""

    def write(self, line: str):
        self._line = line

    def read(self):
        return self._line


class CSVJSONConverter:
    """
    A utility class for converting CSV data to JSON format and vice versa.
    """

    ExportMode = typing.Literal["simplified", "detailed"]

    @classmethod
    def csv_to_json(
        cls,
        csv_data: str | bytes,
        *,
        delimiter=",",
        quotechar: str | None = None,
    ):
        """
        Converts CSV data to JSON format.

        Args:
            csv_data (str, bytes): The CSV data.
            delimiter (str, optional): The delimiter to use in the CSV. Defaults to ",".
            quotechar (str | None, optional): Quote character for the CSV file. If not given, it will not be used. Defaults to None.

        Returns:
            list[dict[str, Any]]: The JSON data as a list of dictionaries.
        """
        if isinstance(csv_data, bytes):
            csv_data = csv_data.decode("utf-8")

        lines = csv_data.splitlines()
        reader = csv.DictReader(lines, delimiter=delimiter, quotechar=quotechar)
        return [
            cls._convert_nested_col_into_dict(
                row, list_delimiter=";" if delimiter != ";" else ","
            )
            for row in reader
        ]

    @classmethod
    def json_to_csv(
        cls,
        data: "dict[str, typing.Any] | list[dict[str, typing.Any]] | BasicModel | list[BasicModel]",
        /,
        *,
        list_columns: list[str],
        label_columns: dict[str, str],
        with_header=True,
        delimiter=",",
        quotechar: str | None = None,
        relation_separator: str = ".",
        export_mode: ExportMode = "simplified",
    ):
        """
        Converts JSON data to CSV format.

        - Data can also be a subclass of `BasicModel` or a list of subclasses of `BasicModel`.

        Args:
            data (dict[str, typing.Any] | list[dict[str, typing.Any]] | BasicModel | list[BasicModel]): The JSON data to be converted. Can also be a subclass of `BasicModel` or a list of subclasses of `BasicModel`.
            list_columns (list[str]): The list of columns to be included in the CSV.
            label_columns (dict[str, str]): The mapping of column names to labels.
            with_header (bool, optional): Whether to include the header in the CSV. Defaults to True.
            delimiter (str, optional): The delimiter to use in the CSV. Defaults to ",".
            quotechar (str | None, optional): Quote character for the CSV file. If not given, it will not be used. Defaults to None.
            relation_separator (str, optional): The separator to use for nested keys. Defaults to ".".
            export_mode (ExportMode, optional): Export mode (simplified or detailed). Defaults to "simplified".

        Returns:
            str: The CSV data as a string.
        """
        csv_data = ""
        line = Line()
        writer = csv.writer(line, delimiter=delimiter, quotechar=quotechar)

        if with_header:
            header = [label_columns[col] for col in list_columns]
            writer.writerow(header)
            csv_data = line.read()

        if not isinstance(data, list):
            data = [data]

        for item in data:
            row = cls.json_to_csv_single(
                item,
                list_columns=list_columns,
                delimiter=delimiter,
                relation_separator=relation_separator,
                export_mode=export_mode,
            )
            writer.writerow(row)
            csv_data += line.read()

        return csv_data.strip()

    @classmethod
    def json_to_csv_single(
        self,
        data: "dict[str, typing.Any] | BasicModel",
        /,
        *,
        list_columns: list[str],
        delimiter=",",
        relation_separator=".",
        export_mode: ExportMode = "simplified",
    ):
        """
        Converts single JSON object to CSV format.

        - Data can also be a subclass of `BasicModel`.

        Args:
            data (dict[str, typing.Any] | BasicModel): The JSON data to be converted. Can also be a subclass of `BasicModel`.
            list_columns (list[str]): The list of columns to be included in the CSV.
            delimiter (str, optional): The delimiter to use in the CSV. Defaults to ",".
            relation_separator (str, optional): The separator to use for nested keys. Defaults to ".".
            export_mode (ExportMode, optional): Export mode (simplified or detailed). Defaults to "simplified".

        Returns:
            str: The CSV data as a string.
        """
        csv_data: list[str] = []
        data_pipeline = DataPipeline()
        data_pipeline.add_processor(ColumnProcessor(relation_separator))
        data_pipeline.add_processor(ModelProcessor())
        data_pipeline.add_processor(
            ListProcessor(delimiter=delimiter, export_mode=export_mode)
        )
        data_pipeline.add_processor(EnumProcessor())
        data_pipeline.add_processor(FallbackProcessor())

        for col in list_columns:
            value = data_pipeline.process(data, col)
            csv_data.append(value)

        return csv_data

    @classmethod
    async def ajson_to_csv_single(
        cls,
        data: "dict[str, typing.Any] | BasicModel",
        /,
        *,
        list_columns: list[str],
        delimiter=",",
        relation_separator=".",
        export_mode: ExportMode = "simplified",
    ):
        """
        Asynchronously converts single JSON object to CSV format.

        - Data can also be a `BasicModel`.

        Args:
            data (dict[str, typing.Any] | BasicModel): The JSON data to be converted. Can also be a `BasicModel`.
            list_columns (list[str]): The list of columns to be included in the CSV.
            delimiter (str, optional): The delimiter to use in the CSV. Defaults to ",".
            relation_separator (str, optional): The separator to use for nested keys. Defaults to ".".
            export_mode (ExportMode, optional): Export mode (simplified or detailed). Defaults to "simplified".

        Returns:
            str: The CSV data as a string.
        """
        csv_data: list[str] = []
        data_pipeline = DataPipeline()
        data_pipeline.add_processor(AsyncColumnProcessor(relation_separator))
        data_pipeline.add_processor(ModelProcessor())
        data_pipeline.add_processor(
            ListProcessor(delimiter=delimiter, export_mode=export_mode)
        )
        data_pipeline.add_processor(EnumProcessor())
        data_pipeline.add_processor(FallbackProcessor())

        for col in list_columns:
            value = await data_pipeline.aprocess(data, col)
            csv_data.append(value)

        return csv_data

    @classmethod
    def _convert_nested_col_into_dict(
        cls,
        data: dict[str, typing.Any],
        /,
        *,
        separator: str = ".",
        list_delimiter: str = ";",
    ):
        """
        Converts nested columns in a dictionary into a nested dictionary.

        Args:
            data (dict[str, Any]): The dictionary to be converted.
            separator (str, optional): Separator used to split the keys into nested dictionaries. Defaults to ".".
            list_delimiter (str, optional): Delimiter used to join list values. Defaults to ";"

        Returns:
            dict[str, Any]: The converted dictionary with nested keys.

        Example:
        ```python
            data = {
                "name": "Alice",
                "age": 30,
                "address.city": "New York",
                "address.state": "NY",
            }
            result = CSVJSONConverter._convert_nested_col_into_dict(data)
            # result = {
            #     "name": "Alice",
            #     "age": 30,
            #     "address": {
            #         "city": "New York",
            #         "state": "NY"
            #     }
            # }
        ```
        """
        result: dict[str, typing.Any] = {}
        for key, value in data.items():
            parts = key.strip().split(separator)
            current = result
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value

            if list_delimiter in value:
                value = value.split(list_delimiter)
                current[parts[-1]] = [item.strip() for item in value if item.strip()]
        return result


class DataPipeline:
    def __init__(self):
        self.processors = list[DataProcessor]()

    def add_processor(self, processor: "DataProcessor"):
        """
        Adds a data processor to the pipeline.

        Args:
            processor (DataProcessor): The data processor to add.
        """
        self.processors.append(processor)

    def process(self, data: typing.Any, col: str):
        """
        Processes the data through the pipeline.

        Args:
            data (typing.Any): The data to process.
            col (str): The column to process.

        Returns:
            typing.Any: The processed data.
        """
        for processor in self.processors:
            data, col, should_continue = processor.process(data, col)
            if not should_continue:
                break
        return data

    async def aprocess(self, data: typing.Any, col: str):
        """
        Asynchronously processes the data through the pipeline.

        Args:
            data (typing.Any): The data to process.
            col (str): The column to process.

        Returns:
            typing.Any: The processed data.
        """
        for processor in self.processors:
            data, col, should_continue = await safe_call(processor.process(data, col))
            if not should_continue:
                break
        return data


class DataProcessor(abc.ABC):
    @abc.abstractmethod
    def process(self, data: typing.Any, col: str) -> tuple[typing.Any, str, bool]:
        """
        Processes the data for a specific column.

        Args:
            data (typing.Any): The data to process.
            col (str): The column to process.

        Returns:
            tuple[typing.Any, str, bool]: The processed data, the column name, and a boolean indicating whether to continue processing.
        """
        raise NotImplementedError()


class ColumnProcessor(DataProcessor):
    def __init__(self, relation_separator: str = "."):
        super().__init__()
        self.relation_separator = relation_separator

    def process(self, data, col):
        sub_col = []
        if self.relation_separator in col:
            col, *sub_col = col.split(self.relation_separator)
        data = data.get(col, "") if isinstance(data, dict) else getattr(data, col, "")
        for sub in sub_col:
            data = (
                data.get(sub, "") if isinstance(data, dict) else getattr(data, sub, "")
            )
        return data, col, True


class AsyncColumnProcessor(ColumnProcessor):
    async def process(self, data, col):
        data, col, continue_processing = super().process(data, col)
        if inspect.iscoroutine(data):
            data = await data
        return data, col, continue_processing


class ModelProcessor(DataProcessor):
    def __init__(self, attr="name_"):
        super().__init__()
        self.attr = attr

    def process(self, data, col):
        from ..bases import BasicModel

        continue_processing = True

        if isinstance(data, BasicModel):
            data = getattr(data, self.attr, "")
            continue_processing = False
        return data, col, continue_processing


class DictProcessor(ModelProcessor):
    def process(self, data, col):
        continue_processing = True

        if isinstance(data, dict):
            data = data.get(self.attr, json.dumps(data))
            continue_processing = False
        return data, col, continue_processing


class ListProcessor(DataProcessor):
    def __init__(
        self,
        delimiter=",",
        export_mode: CSVJSONConverter.ExportMode = "simplified",
        attr_detailed="id_",
        attr_simplified="name_",
    ):
        super().__init__()
        self.separator = "," if delimiter == ";" else ";"
        self.export_mode = export_mode
        self.model_processor = ModelProcessor(
            attr_detailed if export_mode == "detailed" else attr_simplified
        )
        self.dict_processor = DictProcessor(
            attr_detailed if export_mode == "detailed" else attr_simplified
        )

    def process(self, data, col):
        from ..bases import BasicModel

        continue_processing = True

        if isinstance(data, list):
            processed_list = []
            for item in data:
                if isinstance(item, dict):
                    item_processed, _, _ = self.dict_processor.process(item, col)
                elif isinstance(item, BasicModel):
                    item_processed, _, _ = self.model_processor.process(item, col)
                else:
                    item_processed = str(item)
                processed_list.append(item_processed)
            data = self.separator.join(processed_list)
            continue_processing = False
        return data, col, continue_processing


class EnumProcessor(DataProcessor):
    def process(self, data, col):
        continue_processing = True

        if isinstance(data, enum.Enum):
            data = data.value
            continue_processing = False
        return data, col, continue_processing


class FallbackProcessor(DataProcessor):
    def process(self, data, col):
        if data is None:
            data = ""
        else:
            data = str(data)
        return data, col, False
