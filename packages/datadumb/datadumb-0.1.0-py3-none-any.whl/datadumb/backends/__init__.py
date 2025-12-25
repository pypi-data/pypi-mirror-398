"""Backend adapters for different DataFrame libraries."""

from .base import BackendAdapter
from .pandas_adapter import PandasAdapter
from .polars_adapter import PolarsAdapter

__all__ = ["BackendAdapter", "PandasAdapter", "PolarsAdapter"]