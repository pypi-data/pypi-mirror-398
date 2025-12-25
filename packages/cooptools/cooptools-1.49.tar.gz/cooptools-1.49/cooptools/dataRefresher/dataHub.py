import time

from .dataRefresher import DataRefresher
from typing import List, Optional, Dict, Any
import logging
import cooptools.os_manip as osm

logger = logging.getLogger('data_hub')

class DataHub:
    def __init__(self,
                 dataRefreshers: List[DataRefresher],
                 watchdog_refresh_interval_ms: int = 500):
        self._refreshers: Dict[str, DataRefresher] = {}
        self._watchdog = DataRefresher('_INTERNAL_',
                                       refresh_callback=self.go_get_latests,
                                       refresh_interval_ms=watchdog_refresh_interval_ms,
                                       as_async=True)

        self.add_refreshers(dataRefreshers)

    def add_refreshers(self, dataRefreshers: List[DataRefresher]):
        for refr in dataRefreshers:
            self._refreshers[refr.name] = refr
        logger.info(f"Loggers registered in data hub: [{[x.name for x in dataRefreshers]}]")

    def go_get_latests(self) -> Dict[str, Any]:
        stag_asyncs = self.stag_asyncs
        ret = {name: x.go_get_latest for name, x in self._refreshers.items()}
        ret.update({'stagnant_refreshers': [(name, (x.s_since_last_refresh)) for name, x in stag_asyncs.items()]})
        return ret

    def persist(self, file_path):
        osm.save_jsonable_data(self.data, file_path)

    @property
    def stag_asyncs(self) -> Dict[str, DataRefresher]:
        return {name: x for name, x in self._refreshers.items() if x.is_async and x.stagnant}

    @property
    def data(self) -> Dict[str, Any]:
        return self._watchdog.last_cached

if __name__ == "__main__":
    from cooptools.decor import debug

    @debug
    def take_time(sec):
        time.sleep(sec)
        return time.perf_counter()


    logging.basicConfig(level=logging.DEBUG)

    dr1 = DataRefresher('a', lambda: take_time(4), 1000, as_async=True, set_cache_on_init=False)
    dr2 = DataRefresher('b', lambda: take_time(.5), 1000, as_async=False)
    dr3 = DataRefresher('c', lambda: take_time(1), 5000, as_async=True, stagnation_timeout_ms=3000)

    dh = DataHub(dataRefreshers=[
        dr1,
        dr2,
        dr3
    ])

    while True:
        print(dh.data)
        time.sleep(1)

