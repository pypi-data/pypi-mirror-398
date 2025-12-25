import time
import uuid
from typing import List, Protocol, Callable
from dataclasses import dataclass, field
from cooptools.common import insert_sorted_list
from cooptools.pandasHelpers import pretty_print_dataframe
import pandas as pd

@dataclass(frozen=True)
class DiscreteEvent:
    name: str
    t_ms: int
    stop_condition: int = 0
    id: uuid.UUID = field(default_factory=uuid.uuid4, init=False)

    def __lt__(self, other):
        if type(other) != DiscreteEvent:
            raise TypeError(f"Type {other} not comparable")
        return self.t_ms < other.t_ms


event_handler = Callable[[DiscreteEvent], List[DiscreteEvent]]

class DESComponentProtocol(Protocol):
    def initial_events(self) -> List[DiscreteEvent]:
        pass

    def handle_event(self, event: DiscreteEvent) -> List[DiscreteEvent]:
        pass


class DiscreteEventSimulator:
    def __init__(self):
        self._event_queue: List[DiscreteEvent] = []
        self._event_handlers: List[event_handler] = []

    def insert_events(self, events: List[DiscreteEvent]):
        for event in events:
            self._event_queue = insert_sorted_list(self._event_queue, event)

    def register_event_handlers(self, event_handlers: List[event_handler]):
        self._event_handlers += event_handlers

    def register_components(self, components: List[DESComponentProtocol]):
        self.register_event_handlers([x.handle_event for x in components])
        for component in components:
            init_events = component.initial_events()
            self.insert_events(init_events)

    def handle_event(self, event: DiscreteEvent):
        print(f"{time.perf_counter()}: Handled event {event}")
        for handler in self._event_handlers:
            new_events = handler(event)
            if not all([x.t_ms > event.t_ms for x in new_events]):
                raise Exception(f"Cannot insert an event in the past")
            self.insert_events(events=new_events)

    def run(self, time_limit_ms: int = None, sim_time_limit_ms:int = None):
        if sim_time_limit_ms is not None:
            self.insert_events([DiscreteEvent("SimTimeLimitReached", t_ms=sim_time_limit_ms, stop_condition=1)])

        idx = 0
        start = time.perf_counter()

        while idx < len(self._event_queue):
            # break on time limit reached
            if time_limit_ms and time.perf_counter() - start > time_limit_ms / 1000:
                self.handle_event(DiscreteEvent("TimeLimitReached", t_ms=time_limit_ms, stop_condition=1))
                break

            # get next event
            current_event = self._event_queue[idx]

            # handle event
            self.handle_event(current_event)
            if self._event_queue[idx].stop_condition == 1:
                break
            idx += 1

        self.handle_event(DiscreteEvent("STOP", t_ms=self.MaxPerf, stop_condition=1))

    @property
    def MaxPerf(self):
        return self._event_queue[-1].t_ms

    def metrics(self, event_name: str):
        relevant_events = [x for x in self._event_queue if x.name == event_name]
        intervals = [relevant_events[ii].t_ms - relevant_events[ii - 1].t_ms for ii in range(len(relevant_events)) if ii > 0]

        df = pd.DataFrame.from_dict(
            data={
                'count': len(relevant_events),
                'avg_interval': sum(intervals) / len(intervals),
                'max_interval': max(intervals),
                'min_interval': min(intervals)
            },
            orient='index'
        )

        pretty_print_dataframe(df)






interval_provider = Callable[[], int]

class Creator(DESComponentProtocol):
    def __init__(self, name:str, delay_ms_calculator: interval_provider, inter_arrival_ms_calculator: interval_provider):
        self.name = name
        self.inter_arrival_ms_calculator = inter_arrival_ms_calculator
        self.delay_ms_calculator = delay_ms_calculator

    def next(self, t_now: int, interval_ms: int):
        return int(t_now + interval_ms)

    def initial_events(self) -> List[DiscreteEvent]:
        ret = [DiscreteEvent(name=self.name, t_ms=self.next(t_now=0, interval_ms=self.delay_ms_calculator()))]
        return ret

    def handle_event(self, event: DiscreteEvent) -> List[DiscreteEvent]:
        ret = []
        if event.name == self.name:
            ret.append(DiscreteEvent(name=self.name, t_ms=self.next(t_now=event.t_ms, interval_ms=self.inter_arrival_ms_calculator())))

        return ret

if __name__ == "__main__":
    from numpy import random as nprnd

    des = DiscreteEventSimulator()
    c1 = Creator(name="CreateItem",
                 delay_ms_calculator=lambda: nprnd.exponential(1000),
                 inter_arrival_ms_calculator=lambda: nprnd.exponential(5000))


    def create_tacos_on_cheese(event: DiscreteEvent) -> List[DiscreteEvent]:
        ret = []
        if event.name == 'Cheese':
            ret.append(DiscreteEvent("Tacos", t_ms=event.t_ms + 200))
        return ret


    def create_hotsauce_from_hotsauce(event: DiscreteEvent) -> List[DiscreteEvent]:
        ret = []
        if event.name == 'HotSauce':
            ret.append(DiscreteEvent("HotSauce", t_ms=event.t_ms + 200))
        return ret

    # des.insert_events(events=[
    #     DiscreteEvent("Cheese", t_ms=1000),
    #     DiscreteEvent("Pickles", t_ms=2000),
    #     DiscreteEvent("HotSauce", t_ms=0)
    # ])
    #
    # des.register_event_handlers([create_tacos_on_cheese, create_hotsauce_from_hotsauce])

    des.register_components([c1])

    des.run(time_limit_ms=5000, sim_time_limit_ms=100_000)
    des.metrics("CreateItem")
