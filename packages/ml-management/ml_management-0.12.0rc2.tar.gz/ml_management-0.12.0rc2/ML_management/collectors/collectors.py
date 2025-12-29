"""Collectors."""
from typing import Callable, Dict, Generic, ItemsView, Type, TypeVar

from ML_management.collectors.collector_pattern import CollectorPattern

_Value = TypeVar("_Value")


class ModelTypeFactory(Dict[str, _Value], Generic[_Value]):
    """Class for wrap call."""

    def __init__(self, items: Dict[str, Callable[[], _Value]]) -> None:
        """Init."""
        super().__init__(items)

    def __getitem__(self, k: str) -> _Value:
        """Get item."""
        return super().__getitem__(k)()

    def items(self) -> ItemsView[str, Callable[[], _Value]]:
        """Items."""
        return super().items()

    @staticmethod
    def get_name(aggr_id: int):
        return id2name[aggr_id]

    @staticmethod
    def get_id(name: str):
        return name2id[name]


def _get_s3() -> Type[CollectorPattern]:
    """Get s3."""
    from ML_management.collectors.s3.s3collector import S3Collector

    return S3Collector


def _get_dummy() -> Type[CollectorPattern]:
    """Get dummy."""
    from ML_management.collectors.dummy.dummy_collector import DummyCollector

    return DummyCollector


def _get_local() -> Type[CollectorPattern]:
    """Get local."""
    from ML_management.collectors.local.local_collector import LocalCollector

    return LocalCollector


name2id = {
    "s3": 1,
    "dummy": 2,
    "local": 3,
}

id2name = {
    1: "s3",
    2: "dummy",
    3: "local",
}


DATA_COLLECTORS = ModelTypeFactory(
    {
        "s3": _get_s3,
        "dummy": _get_dummy,
        "local": _get_local,
    }
)

DATA_REMOTE_COLLECTORS = ModelTypeFactory(
    {
        "s3": _get_s3,
        "dummy": _get_dummy,
    }
)
