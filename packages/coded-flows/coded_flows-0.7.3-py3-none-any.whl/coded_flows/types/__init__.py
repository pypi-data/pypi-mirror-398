from uuid import UUID
from pathlib import Path
from decimal import Decimal
from datetime import (
    datetime as _datetime,
    date as _date,
    time as _time,
    timedelta as _timedelta,
)
from typing import (
    Iterable,
    Deque,
    Callable,
    Any,
    TypeVar as _TypeVar,
    Dict,
    List,
    Tuple,
    Set,
    FrozenSet,
    AnyStr,
    Union,
)
from typing_extensions import TypeAlias as _TypeAlias
from pydantic import (
    TypeAdapter as _TypeAdapter,
    AnyUrl,
    AnyHttpUrl,
    HttpUrl,
    FileUrl,
    PostgresDsn,
    CockroachDsn,
    AmqpDsn,
    RedisDsn,
    MongoDsn,
    KafkaDsn,
    NatsDsn,
    MySQLDsn,
    MariaDBDsn,
    EmailStr,
    IPvAnyAddress,
    IPvAnyInterface,
    IPvAnyNetwork,
    NewPath,
    FilePath,
    DirectoryPath,
    PositiveInt,
    NegativeInt,
    PositiveFloat,
    NegativeFloat,
    FiniteFloat,
    UUID1,
    UUID3,
    UUID4,
    UUID5,
    Base64Bytes,
    Base64Str,
    JsonValue,
    Json,
    SecretStr,
)
from pydantic_extra_types.color import Color
from pydantic_extra_types.country import (
    CountryAlpha2,
    CountryAlpha3,
    CountryNumericCode,
    CountryShortName,
)
from pydantic_extra_types.currency_code import Currency
from pydantic_extra_types.coordinate import Longitude, Latitude, Coordinate
from pydantic_extra_types.mac_address import MacAddress


from .extra import DataSeries, DataFrame, ArrowTable, NDArray, BytesIOType, PILImage


Null: _TypeAlias = None
Str: _TypeAlias = str
Int: _TypeAlias = int
Float: _TypeAlias = float
Complex: _TypeAlias = complex
Number = _TypeVar("Number", int, float, Decimal)
Bool: _TypeAlias = bool
Datetime: _TypeAlias = _datetime
Date: _TypeAlias = _date
Time: _TypeAlias = _time
Timedelta: _TypeAlias = _timedelta
Bytes: _TypeAlias = bytes
Bytearray: _TypeAlias = bytearray
DataDict = Dict[str, List[Any]]
DataRecords = List[Dict[str, Any]]
MediaData: _TypeAlias = Union[bytes, BytesIOType, NDArray]


def list_of_supported_types():
    return [
        "Any",
        "Null",
        "DataSeries",
        "DataFrame",
        "ArrowTable",
        "NDArray",
        "DataDict",
        "DataRecords",
        "Str",
        "AnyStr",
        "Base64Str",
        "CountryAlpha2",
        "CountryAlpha3",
        "CountryNumericCode",
        "CountryShortName",
        "Currency",
        "Bool",
        "Datetime",
        "Date",
        "Time",
        "Timedelta",
        "Int",
        "Float",
        "Decimal",
        "Complex",
        "Number",
        "PositiveInt",
        "NegativeInt",
        "PositiveFloat",
        "NegativeFloat",
        "FiniteFloat",
        "List",
        "Tuple",
        "Deque",
        "Set",
        "FrozenSet",
        "Iterable",
        "Dict",
        "Callable",
        "IPvAnyAddress",
        "IPvAnyInterface",
        "IPvAnyNetwork",
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
        "MacAddress",
        "EmailStr",
        "Bytes",
        "Bytearray",
        "Base64Bytes",
        "BytesIOType",
        "Path",
        "NewPath",
        "FilePath",
        "DirectoryPath",
        "UUID",
        "UUID1",
        "UUID3",
        "UUID4",
        "UUID5",
        "JsonValue",
        "Json",
        "SecretStr",
        "Color",
        "Longitude",
        "Latitude",
        "Coordinate",
        "PILImage",
        "MediaData",
    ]


def types_validation_mapping(main_type=None, is_json=False):
    import json

    mapping = {
        "Any": [
            "Any",
            "Null",
            "DataSeries",
            "DataFrame",
            "ArrowTable",
            "NDArray",
            "DataDict",
            "DataRecords",
            "Str",
            "AnyStr",
            "Base64Str",
            "CountryAlpha2",
            "CountryAlpha3",
            "CountryNumericCode",
            "CountryShortName",
            "Currency",
            "Bool",
            "Datetime",
            "Date",
            "Time",
            "Timedelta",
            "Int",
            "Float",
            "Complex",
            "Decimal",
            "Number",
            "PositiveInt",
            "NegativeInt",
            "PositiveFloat",
            "NegativeFloat",
            "FiniteFloat",
            "List",
            "Tuple",
            "Deque",
            "Set",
            "FrozenSet",
            "Iterable",
            "Dict",
            "Callable",
            "IPvAnyAddress",
            "IPvAnyInterface",
            "IPvAnyNetwork",
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
            "MacAddress",
            "EmailStr",
            "Bytes",
            "Bytearray",
            "Base64Bytes",
            "BytesIOType",
            "Path",
            "NewPath",
            "FilePath",
            "DirectoryPath",
            "UUID",
            "UUID1",
            "UUID3",
            "UUID4",
            "UUID5",
            "JsonValue",
            "Json",
            "SecretStr",
            "Color",
            "Longitude",
            "Latitude",
            "Coordinate",
            "PILImage",
            "MediaData",
        ],
        "Null": ["Null"],
        "DataSeries": ["DataSeries"],
        "DataFrame": ["DataFrame"],
        "ArrowTable": ["ArrowTable"],
        "NDArray": ["NDArray"],
        "DataDict": ["DataDict"],
        "DataRecords": ["DataRecords"],
        "Str": [
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
        ],
        "AnyStr": [
            "AnyStr",
            "Str",
            "Base64Str",
            "CountryAlpha2",
            "CountryAlpha3",
            "CountryNumericCode",
            "CountryShortName",
            "EmailStr",
            "Bytes",
            "Currency",
            "Base64Bytes",
            "Json",
            "MacAddress",
        ],
        "Base64Str": ["Base64Str"],
        "CountryAlpha2": ["CountryAlpha2"],
        "CountryAlpha3": ["CountryAlpha3"],
        "CountryNumericCode": ["CountryNumericCode"],
        "CountryShortName": ["CountryShortName"],
        "Currency": ["Currency"],
        "Bool": ["Bool"],
        "Datetime": ["Datetime"],
        "Date": ["Date", "Datetime"],
        "Time": ["Time"],
        "Timedelta": ["Timedelta"],
        "Int": ["Int", "PositiveInt", "NegativeInt"],
        "Float": [
            "Float",
            "Longitude",
            "Latitude",
            "PositiveFloat",
            "NegativeFloat",
            "FiniteFloat",
            "Int",
            "PositiveInt",
            "NegativeInt",
        ],
        "Complex": [
            "Complex",
            "Int",
            "Float",
            "PositiveFloat",
            "NegativeFloat",
            "FiniteFloat",
            "PositiveInt",
            "NegativeInt",
        ],
        "Decimal": ["Decimal", "Int", "PositiveInt", "NegativeInt"],
        "Number": [
            "Bool",
            "Int",
            "Float",
            "PositiveInt",
            "NegativeInt",
            "Longitude",
            "Latitude",
            "PositiveFloat",
            "NegativeFloat",
            "FiniteFloat",
            "Complex",
        ],
        "PositiveInt": ["PositiveInt"],
        "NegativeInt": ["NegativeInt"],
        "PositiveFloat": ["PositiveFloat"],
        "NegativeFloat": ["NegativeFloat"],
        "FiniteFloat": ["FiniteFloat"],
        "List": ["List", "DataRecords"],
        "Tuple": ["Tuple"],
        "Deque": ["Deque"],
        "Set": ["Set"],
        "FrozenSet": ["FrozenSet"],
        "Iterable": [
            "Iterable",
            "List",
            "Tuple",
            "Deque",
            "Set",
            "FrozenSet",
            "DataSeries",
            "DataFrame",
            "NDArray",
            "DataRecords",
            "Bytes",
            "Base64Bytes",
            "AnyStr",
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
        ],
        "Dict": ["Dict", "DataDict"],
        "Callable": ["Callable"],
        "IPvAnyAddress": ["IPvAnyAddress"],
        "IPvAnyInterface": ["IPvAnyInterface"],
        "IPvAnyNetwork": ["IPvAnyNetwork"],
        "AnyUrl": [
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
        ],
        "AnyHttpUrl": ["AnyHttpUrl", "HttpUrl"],
        "HttpUrl": ["HttpUrl"],
        "FileUrl": ["FileUrl"],
        "PostgresDsn": ["PostgresDsn"],
        "CockroachDsn": ["CockroachDsn"],
        "AmqpDsn": ["AmqpDsn"],
        "RedisDsn": ["RedisDsn"],
        "MongoDsn": ["MongoDsn"],
        "KafkaDsn": ["KafkaDsn"],
        "NatsDsn": ["NatsDsn"],
        "MySQLDsn": ["MySQLDsn"],
        "MariaDBDsn": ["MariaDBDsn"],
        "MacAddress": ["MacAddress"],
        "EmailStr": ["EmailStr"],
        "Bytes": ["Bytes", "Base64Bytes"],
        "Bytearray": ["Bytearray"],
        "Base64Bytes": ["Base64Bytes"],
        "BytesIOType": ["BytesIOType"],
        "Path": ["Path", "NewPath", "FilePath", "DirectoryPath"],
        "NewPath": ["NewPath"],
        "FilePath": ["FilePath"],
        "DirectoryPath": ["DirectoryPath"],
        "UUID": ["UUID", "UUID1", "UUID3", "UUID4", "UUID5"],
        "UUID1": ["UUID1"],
        "UUID3": ["UUID3"],
        "UUID4": ["UUID4"],
        "UUID5": ["UUID5"],
        "JsonValue": [
            "List",
            "DataRecords",
            "Dict",
            "DataDict",
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
            "Bool",
            "Int",
            "PositiveInt",
            "NegativeInt",
            "Float",
            "Longitude",
            "Latitude",
            "PositiveFloat",
            "NegativeFloat",
            "FiniteFloat",
            "Null",
        ],
        "Json": ["Json"],
        "SecretStr": ["SecretStr"],
        "Color": ["Color"],
        "Longitude": ["Longitude"],
        "Latitude": ["Latitude"],
        "Coordinate": ["Coordinate"],
        "PILImage": ["PILImage"],
        "MediaData": ["MediaData", "NDArray", "Bytes", "BytesIOType"],
    }

    if main_type:
        mapping = mapping.get(main_type, [])

    if is_json:
        mapping = json.dumps(mapping)

    return mapping


def is_valid_value_type(value, value_type):
    ta = _TypeAdapter(value_type)
    ta.validate_python(value)


def is_supported_type(element_type):
    supported_types = list_of_supported_types()
    return element_type in supported_types


__all__ = [
    "list_of_supported_types",
    "types_validation_mapping",
    "is_valid_value_type",
    "is_supported_type",
    "Any",
    "Null",
    # Data
    "DataSeries",
    "DataFrame",
    "ArrowTable",
    "NDArray",
    "DataDict",
    "DataRecords",
    # Strings
    "Str",
    "AnyStr",
    "Base64Str",
    # Country - str too
    "CountryAlpha2",  # <-- works as a Helper
    "CountryAlpha3",  # <-- works as a Helper
    "CountryNumericCode",  # <-- works as a Helper
    "CountryShortName",  # <-- works as a Helper
    # Currency - str too
    "Currency",
    # Boolean
    "Bool",
    # Datetime
    "Datetime",  # <-- works as a Helper
    "Date",  # <-- works as a Helper
    "Time",  # <-- works as a Helper
    "Timedelta",  # <-- works as a Helper
    # Numbers
    "Int",
    "Float",
    "Complex",
    "Decimal",
    "Number",
    "PositiveInt",
    "NegativeInt",
    "PositiveFloat",
    "NegativeFloat",
    "FiniteFloat",
    # Iterables
    "List",
    "Tuple",
    "Deque",
    "Set",
    "FrozenSet",
    "Iterable",
    # Mapping
    "Dict",
    # Callable
    "Callable",
    # IP Address types
    "IPvAnyAddress",  # <-- works as a Helper
    "IPvAnyInterface",  # <-- works as a Helper
    "IPvAnyNetwork",  # <-- works as a Helper
    # network types
    "AnyUrl",  # <-- works as a Helper
    "AnyHttpUrl",  # <-- works as a Helper
    "HttpUrl",  # <-- works as a Helper
    "FileUrl",  # <-- works as a Helper
    "PostgresDsn",  # <-- works as a Helper
    "CockroachDsn",  # <-- works as a Helper
    "AmqpDsn",  # <-- works as a Helper
    "RedisDsn",  # <-- works as a Helper
    "MongoDsn",  # <-- works as a Helper
    "KafkaDsn",  # <-- works as a Helper
    "NatsDsn",  # <-- works as a Helper
    "MySQLDsn",  # <-- works as a Helper
    "MariaDBDsn",  # <-- works as a Helper
    "MacAddress",
    # Email
    "EmailStr",
    # bytes
    "Bytes",
    "Bytearray",
    "Base64Bytes",
    "BytesIOType",
    # Paths
    "Path",  # <-- works as a Helper
    "NewPath",  # <-- works as a Helper
    "FilePath",  # <-- works as a Helper
    "DirectoryPath",  # <-- works as a Helper
    # UUID
    "UUID",
    "UUID1",
    "UUID3",
    "UUID4",
    "UUID5",
    # Json
    "JsonValue",
    "Json",
    # Secret
    "SecretStr",  # <-- works as a Helper
    # Color
    "Color",  # <-- works as a Helper
    # Coordinates
    "Longitude",
    "Latitude",
    "Coordinate",  # <-- works as a Helper
    # Media
    "PILImage",
    "MediaData",
]
