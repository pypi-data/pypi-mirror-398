import io
import base64
import pandas as pd
import pyarrow as pa
import polars as pl
from numpy import ndarray
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema
from typing import Any, Type, Union, List
from PIL import Image


class DataSeriesMeta(type):

    def __instancecheck__(cls, instance):
        return isinstance(instance, (pd.Series, pl.Series))


def serialize_series(series: Union[pd.Series, pl.Series]) -> List[Any]:
    return series.to_list()


class DataSeries(metaclass=DataSeriesMeta):
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source: Type[Any],
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        pandas_schema = core_schema.is_instance_schema(pd.Series)
        polars_schema = core_schema.is_instance_schema(pl.Series)

        union_schema = core_schema.union_schema([pandas_schema, polars_schema])

        serialization = core_schema.plain_serializer_function_ser_schema(
            serialize_series, when_used="json"
        )

        return core_schema.json_or_python_schema(
            json_schema=union_schema,
            python_schema=union_schema,
            serialization=serialization,
        )


class DataFrameMeta(type):
    def __instancecheck__(cls, instance):
        return isinstance(instance, (pd.DataFrame, pl.DataFrame, pl.LazyFrame))


def serialize_dataframe(
    df: Union[pd.DataFrame, pl.DataFrame, pl.LazyFrame],
) -> list[dict[str, Any]]:
    if isinstance(df, pd.DataFrame):
        return df.to_dict(orient="records")
    if isinstance(df, pl.DataFrame):
        return df.to_dicts()
    if isinstance(df, pl.LazyFrame):
        return df.collect().to_dicts()
    raise TypeError(f"Unsupported dataframe type: {type(df)}")


class DataFrame(metaclass=DataFrameMeta):
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source: Type[Any],
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        pandas_schema = core_schema.is_instance_schema(pd.DataFrame)
        polars_eager_schema = core_schema.is_instance_schema(pl.DataFrame)
        polars_lazy_schema = core_schema.is_instance_schema(pl.LazyFrame)
        union_schema = core_schema.union_schema(
            [pandas_schema, polars_eager_schema, polars_lazy_schema]
        )

        serialization = core_schema.plain_serializer_function_ser_schema(
            serialize_dataframe, when_used="json"
        )

        return core_schema.json_or_python_schema(
            json_schema=union_schema,
            python_schema=union_schema,
            serialization=serialization,
        )


class ArrowTable:

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: Type[Any], _handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:

        return core_schema.is_instance_schema(
            pa.Table,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: instance.to_pylist()
            ),
        )


class NDArray:

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: Type[Any], _handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:

        return core_schema.is_instance_schema(
            ndarray,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: instance.tolist()
            ),
        )


class BytesIOType:

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: Type[Any], _handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:

        return core_schema.is_instance_schema(
            io.BytesIO,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: base64.b64encode(instance.getvalue()).decode("utf-8")
            ),
        )


class PILImage:

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: Type[Any], _handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:

        def image_to_base64(image):
            img_byte_io = io.BytesIO()

            image.save(img_byte_io, format=image.format)

            return base64.b64encode(img_byte_io.getvalue()).decode("utf-8")

        return core_schema.is_instance_schema(
            Image.Image,
            serialization=core_schema.plain_serializer_function_ser_schema(
                image_to_base64
            ),
        )
