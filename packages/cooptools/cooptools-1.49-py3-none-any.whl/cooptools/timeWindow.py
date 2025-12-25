from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class TimeWindow:
    start: float
    end: float

    @property
    def delta_time_s(self):
        return self.end - self.start

    def overlaps(self, other):
        if type(other) == TimeWindow:
            return self.start <= other.start <= self.end or other.start <= self.start <= other.end

    def overlap(self, other):
        if self.overlaps(other):
            return TimeWindow(
                start=max(self.start, other.start),
                end=min(self.end, other.end)
            )

        return None

    def merge(self, other):
        if not self.overlaps(other):
            raise ValueError(f"Time Windows do not overlap, so cannot merge")

        return TimeWindow(
            start=min(self.start, other.start),
            end=max(self.end, other.end)
        )


@dataclass(frozen=True)
class TaggedTimeWindow:
    window: TimeWindow
    tags: List

def time_window_factory(tw: TimeWindow,
                        start: float = None,
                        end: float = None):
    return TimeWindow(
        start=start or tw.start,
        end=end or tw.end
    )

def tagged_time_window_factory(tw: TaggedTimeWindow,
                        window: TimeWindow = None,
                        start: float = None,
                        end: float = None,
                        tags: List = None):

    window = time_window_factory(
        tw=window or tw.window,
        start=start,
        end=end)

    return TaggedTimeWindow(
        window=window,
        tags=tags or tw.tags
    )