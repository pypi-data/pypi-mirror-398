from typing import Callable, Iterable
import logging
import datetime
import pytz
import pandas as pd
import cooptools.date_utils as du
from cooptools.protocols import UniqueIdentifier

logger = logging.getLogger(__name__)

StringProvider = str | Callable[[], str]
StringByIndexProvider = str | Callable[[int], str]
StringChoiceProvider = str | Callable[[Iterable[str]], str]
IntChoiceProvider = int | Callable[[Iterable[int]], int]
StringListProvider = Iterable[str] | Callable[[], Iterable[str]]
IntProvider = int | Callable[[], int]
FloatProvider = float | Callable[[], float]
DictProvider = dict | Callable[[], dict]
FilePathProvider = StringProvider
DateTimeProvider = datetime.datetime | Callable[[], datetime.datetime]
BoolProvider = bool | Callable[[], bool]
DataFrameProvider = pd.DataFrame | Callable[[], pd.DataFrame]
UniqueIdProvider = Callable[[], UniqueIdentifier] | UniqueIdentifier

TypeProvider = StringProvider | StringByIndexProvider | StringChoiceProvider | StringListProvider | IntProvider | FloatProvider | DictProvider | \
    FilePathProvider | DataFrameProvider | BoolProvider | DateTimeProvider | UniqueIdProvider | IntChoiceProvider

TYPE_MAPPING = {
    StringProvider: str,
    StringChoiceProvider: str,
    StringByIndexProvider: str,
    IntChoiceProvider: int,
    StringListProvider: Iterable[str],
    IntProvider: int,
    FloatProvider: float,
    DictProvider: dict,
    FilePathProvider: str,
    DateTimeProvider: du.datestamp_tryParse,
    DataFrameProvider: pd.DataFrame,
    BoolProvider: bool,
    UniqueIdProvider: UniqueIdentifier
}


def resolve(
    provider,
    cast_factory: Callable = None,
    **kwargs
):
    if provider is None:
        return None

    if callable(provider):
        ret = provider(**kwargs)

    else:
        ret = provider

    if cast_factory is not None:
        ret = cast_factory(ret)

    return ret

def try_resolve(
        provider,
        *args):
    try:
        return resolve(provider, *args)
    except:
        logger.error(f"Unable to resolve provider: {provider}")
        return None

def resolve_string_provider(
        string_provider: StringProvider
) -> str:
    return resolve(string_provider)


def resolve_string_by_index_provider(
        string_by_index_provider: StringByIndexProvider,
        index: int
) -> str:
    return resolve(string_by_index_provider,
                   index)

def resolve_string_by_choice_provider(
        string_choice_provider: StringChoiceProvider,
        choices: Iterable[str]
) -> str:
    return resolve(string_choice_provider,
                   choices)

def resolve_int_choice_provider(
        int_choice_provider: IntChoiceProvider,
        choices: Iterable[int]
) -> int:
    return resolve(int_choice_provider,
                   choices)


def resolve_dict_provider(
        dict: DictProvider
) -> dict:
    return resolve(dict)


def resolve_int_provider(
        int_provider: IntProvider
) -> int:
    return resolve(int_provider)

def resolve_float_provider(
        float_provider: FloatProvider
) -> float:
    return resolve(float_provider)

def resolve_datetime_provider(
    datetime_provider: DateTimeProvider,
    default_now: bool = False,
    as_utc: bool = False
) -> datetime.datetime:
    ret = resolve(datetime_provider)

    if ret is None and default_now:
        ret = datetime.datetime.now()

    if ret is None:
        return None

    if as_utc:
        ret = ret.astimezone(pytz.utc)

    return ret

class ResolveFilepathException(Exception):
    def __init__(self):
        logger.warning(f'Unable to load data from filepath as it was None')
        super().__init__()


def resolve_filepath(
        file_path_provider: FilePathProvider) -> str:
    fp = resolve(file_path_provider)

    if fp is None:
        raise ResolveFilepathException()

    return fp

def resolve_bool(
        bool_provider: BoolProvider) -> bool:
    ret = resolve(bool_provider)
    return bool(ret)

if __name__ == "__main__":
    def test_StringProvider():
        val = "x"
        sp = lambda: val
        assert resolve(sp, cast_factory=str) == val

    def test_StringByIndexProvider():
        vals = ["a", "b", "c"]
        sp = lambda x: x[1]
        assert resolve(sp, cast_factory=str, x=vals) == vals[1]

    def test_IntProvider1():
        val = "1"
        sp = lambda: val
        assert resolve(sp, cast_factory=int) == int(val)

    def test_IntProvider2():
        val = 1
        sp = lambda: val
        assert resolve(sp, cast_factory=int) == int(val)


    def test_DateTime():
        val = "1/1/24"
        sp = lambda: val
        assert resolve(sp, cast_factory=du.datestamp_tryParse) == du.datestamp_tryParse(val)

    def test_DataFrame():
        val = pd.DataFrame({'col': [1, 2, 3]})
        sp = lambda: val
        assert resolve(sp, cast_factory=pd.DataFrame).equals(val)

    test_StringProvider()
    test_StringByIndexProvider()
    test_IntProvider1()
    test_IntProvider2()
    test_DateTime()
    test_DataFrame()