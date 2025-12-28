import base64
import json
import numpy as np
from io import BytesIO
from decimal import Decimal
from collections import deque
from typing import Any, Callable, Union
from pydantic_core import MultiHostUrl
import pandas as pd
import polars as pl
import pyarrow as pa
from ..types import (
    AnyUrl,
    Base64Str,
    Base64Bytes,
    Datetime,
    Date,
    Time,
    PILImage,
    NDArray,
)


url_types = [
    "AnyUrl",
    "AnyHttpUrl",
    "HttpUrl",
    "FileUrl",
    "PostgresDsn",
    "CockroachDsn",
    "AmqpDsn",
    "RedisDsn",
    "MongoDsn",
    "KafkaDsn",
    "NatsDsn",
    "MySQLDsn",
    "MariaDBDsn",
]

json_value_types = [
    "List",
    "Dict",
    "Str",
    "Base64Str",
    "CountryAlpha2",
    "CountryAlpha3",
    "CountryNumericCode",
    "CountryShortName",
    "EmailStr",
    "Currency",
    "MacAddress",
    "Bool",
    "Int",
    "Float",
    "Null",
]

core_string_types = ["Str", "AnyStr"]

string_types = [
    "Str",
    "Base64Str",
    "CountryAlpha2",
    "CountryAlpha3",
    "CountryNumericCode",
    "CountryShortName",
    "EmailStr",
    "Currency",
    "Json",
    "MacAddress",
]

to_str_types = [
    "Int",
    "Float",
    "Decimal",
    "PositiveInt",
    "NegativeInt",
    "PositiveFloat",
    "NegativeFloat",
    "FiniteFloat",
    "IPvAnyAddress",
    "IPvAnyInterface",
    "IPvAnyNetwork",
    "Path",
    "NewPath",
    "FilePath",
    "DirectoryPath",
]


conversion_mapping = {
    "Any": [],
    "Null": ["Json"],
    # Data
    "DataSeries": [
        "DataFrame",
        "List",
        "Tuple",
        "Set",
        "Json",
        "NDArray",
        "ArrowTable",
    ],  # <-- works as a Helper
    "DataFrame": [
        "DataRecords",
        "List",
        "Dict",
        "Json",
        "NDArray",
        "ArrowTable",
        "DataDict",
    ],
    "ArrowTable": [
        "DataFrame",
        "DataRecords",
        "List",
        "Dict",
        "Json",
        "NDArray",
        "DataDict",
    ],
    "NDArray": ["List", "Json"],
    "DataDict": [
        "DataFrame",
        "ArrowTable",
    ],
    "DataRecords": [
        "DataFrame",
        "ArrowTable",
    ],
    # Strings
    "Str": ["Json", "Base64Str", "Base64Bytes", "Bytes"],
    "AnyStr": [],
    "Base64Str": ["Json", "Base64Bytes", "Bytes"],
    # Country - str too
    "CountryAlpha2": [
        "Json",
        "Base64Str",
        "Base64Bytes",
        "Bytes",
    ],  # <-- works as a Helper
    "CountryAlpha3": [
        "Json",
        "Base64Str",
        "Base64Bytes",
        "Bytes",
    ],  # <-- works as a Helper
    "CountryNumericCode": [
        "Json",
        "Base64Str",
        "Base64Bytes",
        "Bytes",
    ],  # <-- works as a Helper
    "CountryShortName": [
        "Json",
        "Base64Str",
        "Base64Bytes",
        "Bytes",
    ],  # <-- works as a Helper
    # Currency - str too
    "Currency": ["Json", "Base64Str", "Base64Bytes", "Bytes"],
    # MacAddress - str too
    "MacAddress": ["Json", "Base64Str", "Base64Bytes", "Bytes"],
    # Email - str too
    "EmailStr": ["Json", "Base64Str", "Base64Bytes", "Bytes"],
    # Boolean
    "Bool": ["Json", "Int", "Float", "Complex", "Decimal"],
    # Datetime
    "Datetime": ["Time"],  # <-- works as a Helper
    "Date": ["Datetime", "Time"],  # <-- works as a Helper
    "Time": [],  # <-- works as a Helper
    "Timedelta": [],  # <-- works as a Helper
    # Numbers
    "Int": ["Json", "Str", "AnyStr"],
    "Float": ["Json", "Str", "AnyStr"],
    "Complex": [],
    "Decimal": ["Str", "AnyStr"],
    "Number": [],
    "PositiveInt": ["Str", "AnyStr"],
    "NegativeInt": ["Str", "AnyStr"],
    "PositiveFloat": ["Str", "AnyStr"],
    "NegativeFloat": ["Str", "AnyStr"],
    "FiniteFloat": ["Str", "AnyStr"],
    # Iterables
    "List": ["Json", "Tuple", "Deque", "Set", "FrozenSet"],
    "Tuple": ["List", "Deque", "Set", "FrozenSet"],
    "Deque": ["Tuple", "List", "Set", "FrozenSet"],
    "Set": ["Tuple", "Deque", "List", "FrozenSet"],
    "FrozenSet": ["Tuple", "Deque", "Set", "List"],
    "Iterable": [],
    # Mapping
    "Dict": ["Json"],
    # Callable
    "Callable": [],
    # IP Address types
    "IPvAnyAddress": ["Str", "AnyStr"],  # <-- works as a Helper
    "IPvAnyInterface": ["Str", "AnyStr"],  # <-- works as a Helper
    "IPvAnyNetwork": ["Str", "AnyStr"],  # <-- works as a Helper
    # network types
    "AnyUrl": ["Str", "AnyStr"],  # <-- works as a Helper
    "AnyHttpUrl": ["Str", "AnyStr"],  # <-- works as a Helper
    "HttpUrl": ["Str", "AnyStr"],  # <-- works as a Helper
    "FileUrl": ["Str", "AnyStr"],  # <-- works as a Helper
    "PostgresDsn": ["Str", "AnyStr"],  # <-- works as a Helper
    "CockroachDsn": ["Str", "AnyStr"],  # <-- works as a Helper
    "AmqpDsn": ["Str", "AnyStr"],  # <-- works as a Helper
    "RedisDsn": ["Str", "AnyStr"],  # <-- works as a Helper
    "MongoDsn": ["Str", "AnyStr"],  # <-- works as a Helper
    "KafkaDsn": ["Str", "AnyStr"],  # <-- works as a Helper
    "NatsDsn": ["Str", "AnyStr"],  # <-- works as a Helper
    "MySQLDsn": ["Str", "AnyStr"],  # <-- works as a Helper
    "MariaDBDsn": ["Str", "AnyStr"],  # <-- works as a Helper
    # bytes
    "Bytes": [],
    "Bytearray": [],
    "Base64Bytes": ["Base64Str"],
    "BytesIOType": [],
    # Paths
    "Path": ["Str", "AnyStr"],  # <-- works as a Helper
    "NewPath": ["Str", "AnyStr"],  # <-- works as a Helper
    "FilePath": ["Str", "AnyStr"],  # <-- works as a Helper
    "DirectoryPath": ["Str", "AnyStr"],  # <-- works as a Helper
    # UUID
    "UUID": [],
    "UUID1": [],
    "UUID3": [],
    "UUID4": [],
    "UUID5": [],
    # Json
    "JsonValue": [],
    "Json": ["Base64Str", "Base64Bytes", "Bytes"],
    # Secret
    "SecretStr": [],  # <-- works as a Helper
    # Color
    "Color": ["Str", "AnyStr"],  # <-- works as a Helper
    # Coordinates
    "Longitude": [],
    "Latitude": [],
    "Coordinate": ["Tuple", "List"],  # <-- works as a Helper
    # Media
    "PILImage": [
        "NDArray",
        "Bytes",
        "Base64Str",
        "Str",
        "AnyStr",
        "MediaData",
    ],
    "MediaData": [],
}


def dataseries_to_type(output_type: str) -> Callable:
    if output_type == "DataFrame":
        return lambda x: x.to_frame()
    elif output_type == "List":
        return lambda x: x.to_list()
    elif output_type == "Tuple":
        return lambda x: tuple(x.to_list())
    elif output_type == "Set":
        return lambda x: set(x.to_list())
    elif output_type == "Json":
        return lambda x: (
            json.dumps(x.to_list())
            if isinstance(x, pl.Series)
            else x.to_json(orient="records")
        )
    elif output_type == "NDArray":
        return lambda x: x.to_numpy()
    elif output_type == "ArrowTable":
        return lambda x: (
            pa.Table.from_arrays([x.to_arrow()], names=[x.name if x.name else "value"])
            if isinstance(x, pl.Series)
            else pa.Table.from_pandas(x.to_frame())
        )


def _collect_if_lazy(df: pl.DataFrame | pl.LazyFrame | pd.DataFrame) -> pl.DataFrame:
    return df.collect() if isinstance(df, pl.LazyFrame) else df


def dataframe_to_type(output_type: str) -> Callable:

    if output_type == "DataRecords":
        return lambda x: (
            _collect_if_lazy(x).to_dicts()
            if isinstance(_collect_if_lazy(x), pl.DataFrame)
            else x.to_dict("records")
        )
    elif output_type == "List":
        return lambda x: (
            _collect_if_lazy(x).to_dicts()
            if isinstance(_collect_if_lazy(x), pl.DataFrame)
            else x.to_dict("records")
        )
    elif output_type == "Dict":
        return lambda x: (
            _collect_if_lazy(x).to_dict(as_series=False)
            if isinstance(_collect_if_lazy(x), pl.DataFrame)
            else x.to_dict("list")
        )
    elif output_type == "DataDict":
        return lambda x: (
            _collect_if_lazy(x).to_dict(as_series=False)
            if isinstance(_collect_if_lazy(x), pl.DataFrame)
            else x.to_dict("list")
        )
    elif output_type == "Json":
        return lambda x: (
            _collect_if_lazy(x).write_json()
            if isinstance(_collect_if_lazy(x), pl.DataFrame)
            else x.to_json(orient="records")
        )
    elif output_type == "NDArray":
        return lambda x: _collect_if_lazy(x).to_numpy()
    elif output_type == "ArrowTable":
        return lambda x: (
            _collect_if_lazy(x).to_arrow()
            if isinstance(_collect_if_lazy(x), pl.DataFrame)
            else pa.Table.from_pandas(x)
        )


def arrow_to_type(output_type: str) -> Callable:
    if output_type == "DataRecords":
        return lambda x: x.to_pylist()
    elif output_type == "List":
        return lambda x: x.to_pylist()
    elif output_type == "Dict":
        return lambda x: x.to_pydict()
    elif output_type == "DataDict":
        return lambda x: x.to_pydict()
    elif output_type == "Json":
        return lambda x: json.dumps(x.to_pylist())
    elif output_type == "NDArray":
        return lambda x: x.to_pandas().to_numpy()
    elif output_type == "DataFrame":
        return lambda x: x.to_pandas()


def numpy_to_type(output_type: str) -> Callable:
    if output_type == "List":
        return lambda x: x.tolist()
    elif output_type == "Json":
        return lambda x: json.dumps(x.tolist())


def datadict_to_type(output_type: str) -> Callable:
    if output_type == "DataFrame":
        return lambda x: pd.DataFrame(x)
    elif output_type == "ArrowTable":
        return lambda x: pa.Table.from_pydict(x)


def datarecords_to_type(output_type: str) -> Callable:
    if output_type == "DataFrame":
        return lambda x: pd.DataFrame(x)
    elif output_type == "ArrowTable":
        return lambda x: pa.Table.from_pylist(x)


def bool_to_type(output_type: str) -> Callable:
    if output_type == "Int":
        return lambda x: int(x)
    elif output_type == "Float":
        return lambda x: float(x)
    elif output_type == "Complex":
        return lambda x: complex(x)
    elif output_type == "Decimal":
        return lambda x: Decimal(x)


def list_to_type(output_type: str) -> Callable:
    if output_type == "Tuple":
        return lambda x: tuple(x)
    elif output_type == "Deque":
        return lambda x: deque(x)
    elif output_type == "Set":
        return lambda x: set(x)
    elif output_type == "FrozenSet":
        return lambda x: frozenset(x)


def tuple_to_type(output_type: str) -> Callable:
    if output_type == "List":
        return lambda x: list(x)
    elif output_type == "Deque":
        return lambda x: deque(x)
    elif output_type == "Set":
        return lambda x: set(x)
    elif output_type == "FrozenSet":
        return lambda x: frozenset(x)


def deque_to_type(output_type: str) -> Callable:
    if output_type == "Tuple":
        return lambda x: tuple(x)
    elif output_type == "List":
        return lambda x: list(x)
    elif output_type == "Set":
        return lambda x: set(x)
    elif output_type == "FrozenSet":
        return lambda x: frozenset(x)


def set_to_type(output_type: str) -> Callable:
    if output_type == "Tuple":
        return lambda x: tuple(x)
    elif output_type == "Deque":
        return lambda x: deque(x)
    elif output_type == "List":
        return lambda x: list(x)
    elif output_type == "FrozenSet":
        return lambda x: frozenset(x)


def frozenset_to_type(output_type: str) -> Callable:
    if output_type == "Tuple":
        return lambda x: tuple(x)
    elif output_type == "Deque":
        return lambda x: deque(x)
    elif output_type == "Set":
        return lambda x: set(x)
    elif output_type == "List":
        return lambda x: list(x)


def coordinate_to_type(output_type: str) -> Callable:
    if output_type == "Tuple":
        return lambda x: (x.latitude, x.longitude)
    elif output_type == "List":
        return lambda x: [x.latitude, x.longitude]


def jsonify(value: Any) -> str:
    return json.dumps(value, skipkeys=True)


def str_to_bytes(input_string: str) -> bytes:
    return input_string.encode("utf-8")


def base64str_to_base64bytes(base64_string: str) -> bytes:
    return str_to_bytes(base64_string)


def url_to_str(value: Union[AnyUrl, MultiHostUrl, str]) -> str:
    if isinstance(value, str):
        return value
    return value.unicode_string()


def url_to_bytes(input_string: str) -> bytes:
    url_txt = url_to_str(input_string)
    return str_to_bytes(url_txt)


def url_to_base64str(value: Union[AnyUrl, MultiHostUrl, str]) -> Base64Str:
    url_txt = url_to_str(value)
    url_txt_bytes = url_txt.encode("utf-8")
    base64_bytes = base64.b64encode(url_txt_bytes)
    base64_string = base64_bytes.decode("utf-8")
    return base64_string


def base64bytes_to_base64str(value: Base64Bytes) -> Base64Str:
    base64_string = value.decode("utf-8")
    return base64_string


def url_to_base64bytes(value: Union[AnyUrl, MultiHostUrl, str]) -> Base64Bytes:
    url_txt = url_to_str(value)
    url_txt_bytes = url_txt.encode("utf-8")
    base64_bytes = base64.b64encode(url_txt_bytes)
    return base64_bytes


def str_to_base64str(value: str) -> Base64Str:
    value_bytes = value.encode("utf-8")
    base64_bytes = base64.b64encode(value_bytes)
    base64_string = base64_bytes.decode("utf-8")
    return base64_string


def str_to_base64bytes(value: str) -> Base64Str:
    value_bytes = value.encode("utf-8")
    base64_bytes = base64.b64encode(value_bytes)
    return base64_bytes


def datetime_to_time(value: Datetime) -> Time:
    return value.time()


def date_to_time(value: Date) -> Time:
    return Time(0, 0, 0)


def date_to_datetime(value: Date) -> Datetime:
    return Datetime.combine(value, Datetime.min.time())


def image_to_numpy(image: PILImage) -> NDArray:
    return np.array(image)


def image_to_bytes(image: PILImage) -> bytes:
    byte_io = BytesIO()
    image.save(byte_io, format=image.format if image.format else "PNG")
    image_bytes = byte_io.getvalue()
    byte_io.close()
    return image_bytes


def image_to_base64str(image: PILImage) -> Base64Str:
    image_bytes = image_to_bytes(image)
    return base64.b64encode(image_bytes).decode("utf-8")


def get_conversion_function(input_type: str, output_type: str) -> Callable:
    if input_type in json_value_types and output_type == "Json":
        return jsonify
    elif input_type == "DataSeries" and output_type in conversion_mapping["DataSeries"]:
        return dataseries_to_type(output_type)
    elif input_type == "DataFrame" and output_type in conversion_mapping["DataFrame"]:
        return dataframe_to_type(output_type)
    elif input_type == "ArrowTable" and output_type in conversion_mapping["ArrowTable"]:
        return arrow_to_type(output_type)
    elif input_type == "NDArray" and output_type in conversion_mapping["NDArray"]:
        return numpy_to_type(output_type)
    elif input_type == "DataDict" and output_type in conversion_mapping["DataDict"]:
        return datadict_to_type(output_type)
    elif (
        input_type == "DataRecords" and output_type in conversion_mapping["DataRecords"]
    ):
        return datarecords_to_type(output_type)
    elif (
        input_type in [t for t in string_types if t != "Base64Str"]
        and output_type == "Base64Str"
    ):
        return str_to_base64str
    elif input_type in string_types and output_type == "Bytes":
        return str_to_bytes
    elif (
        input_type in [t for t in string_types if t != "Base64Str"]
        and output_type == "Base64Bytes"
    ):
        return str_to_base64bytes
    elif input_type == "Base64Str" and output_type == "Base64Bytes":
        return base64str_to_base64bytes
    elif input_type == "Base64Bytes" and output_type == "Base64Str":
        return base64bytes_to_base64str
    elif input_type == "Bool" and output_type in ["Int", "Float", "Complex", "Decimal"]:
        return bool_to_type(output_type)
    elif input_type == "Datetime" and output_type == "Time":
        return datetime_to_time
    elif input_type == "Date" and output_type == "Time":
        return date_to_time
    elif input_type == "Date" and output_type == "Datetime":
        return date_to_datetime
    elif input_type in to_str_types and output_type in core_string_types:
        return str
    elif input_type == "List" and output_type in [
        t for t in conversion_mapping["List"] if t != "Json"
    ]:
        return list_to_type(output_type)
    elif input_type == "Tuple" and output_type in conversion_mapping["Tuple"]:
        return tuple_to_type(output_type)
    elif input_type == "Deque" and output_type in conversion_mapping["Deque"]:
        return deque_to_type(output_type)
    elif input_type == "Set" and output_type in conversion_mapping["Set"]:
        return set_to_type(output_type)
    elif input_type == "FrozenSet" and output_type in conversion_mapping["FrozenSet"]:
        return frozenset_to_type(output_type)
    elif input_type in url_types and output_type in core_string_types:
        return url_to_str
    elif input_type == "Color" and output_type in core_string_types:
        return lambda x: x.as_hex()
    elif input_type == "Coordinate" and output_type in ["Tuple", "List"]:
        return coordinate_to_type(output_type)
    elif input_type == "PILImage" and output_type in ["NDArray", "MediaData"]:
        return image_to_numpy
    elif input_type == "PILImage" and output_type == "Bytes":
        return image_to_bytes
    elif input_type == "PILImage" and output_type in [
        "Base64Str",
        "Str",
        "AnyStr",
    ]:
        return image_to_base64str
    return None


def convert_type(value: any, input_type: str, output_type: str) -> any:
    conversion_function = get_conversion_function(input_type, output_type)

    if conversion_function:
        return conversion_function(value)

    return value
