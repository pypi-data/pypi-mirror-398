# import logging
# from typing import Iterable, Dict, Tuple, Protocol
#
# from cooptools.dataStore import dataStoreProtocol as dsp
# from cooptools.protocols import IdentifiableProtocol, UniqueIdentifier
# from cooptools.decor import timeTracker
#
# logger = logging.getLogger(__name__)
#
# class DataFacadeHandlerProtocol(Protocol):
#     def apply_storable_facade(self, item) -> dsp.StorableData:
#         pass
#
#     def remove_storable_facade(self, x: dsp.StorableData):
#         pass
#
# class DataProcessor(dsp.DataStoreProtocol):
#     def __init__(self,
#                  data_store: dsp.DataStoreProtocol,
#                  facade_handler: DataFacadeHandlerProtocol = None
#                  ):
#         self._data_store = data_store
#         self._facade_handler = facade_handler
#
#     def _apply_facade(self, items: Iterable[St]):
#
#     @timeTracker(logger=logger, log_level=logging.DEBUG)
#     def add(self,
#             items: Iterable[dsp.StorableData]) -> Dict[UniqueIdentifier, dsp.StorableData]:
#
#         if self._facade_handler is not None:
#             items = [self._facade_handler.apply_storable_facade(x) for x in items]
#
#         ret = self._data_store.add(items)
#
#         if self._facade_handler is not None:
#             ret = {k: self._facade_handler.remove_storable_facade(v) for k, v in ret.items()}
#
#         return ret
#
#
#     @timeTracker(logger=logger, log_level=logging.DEBUG)
#     def remove(self,
#                items: Iterable[dsp.StorableData] = None,
#                cursor_range: Tuple[int, int] = None,
#                ids: Iterable[UniqueIdentifier] = None) -> Dict[UniqueIdentifier, dsp.StorableData]:
#
#         self._data_store.remove(
#             items=items,
#             cursor_range=cursor_range,
#             ids=ids
#         )