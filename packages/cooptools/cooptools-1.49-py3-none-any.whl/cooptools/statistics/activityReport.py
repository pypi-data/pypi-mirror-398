import datetime
import cooptools.date_utils as du
from typing import Iterable, Callable, Optional
import pandas as pd
from dataclasses import dataclass, field

@dataclass(frozen=True, slots=True)
class ActivityDataQueryArgs:
    start_date: datetime.datetime = None
    end_date: datetime.datetime = None
    activity_whitelist: Iterable[str] = None
    category_whitelist: Iterable[str] = None

EventDataProvider = Callable[[ActivityDataQueryArgs], pd.DataFrame]

def aggregate_activity_data(
        event_data_provider: EventDataProvider,
        data_query_args: ActivityDataQueryArgs,
        date_grouping: du.DateIncrementType,
        date_stamp_column: str = 'date_stamp',
        state_change_type_column: str = 'state_change_type',
        category_type_column: str = 'category',
        state_change_value: str = 'value'

):
    data = event_data_provider(data_query_args)

    bucketed_datestamp_txt = 'date_stamp_bucketed'
    data[bucketed_datestamp_txt] = data.apply(lambda row : du.bucket_datestamp([row[date_stamp_column]],
                                              grouping_method=date_grouping)[0],
                                              axis=1)

    return data


if __name__ == "__main__":
    import cooptools.pandasHelpers as ph

    event_data = pd.DataFrame(
        data=[
            {"date_stamp": "10/1/23 8:00.35", "state_change_type": "A", "category": "1", "state_change_value": "100"},
            {"date_stamp": "10/1/23 8:05.35", "state_change_type": "A", "category": "1", "state_change_value": "200"},
            {"date_stamp": "10/1/23 8:05.47", "state_change_type": "A", "category": "1", "state_change_value": "201"},
            {"date_stamp": "10/1/23 8:05.55", "state_change_type": "A", "category": "1", "state_change_value": "202"},
            {"date_stamp": "10/1/23 8:05.57", "state_change_type": "A", "category": "1", "state_change_value": "203"},
            {"date_stamp": "10/1/23 8:10.35", "state_change_type": "A", "category": "1", "state_change_value": "300"},
            {"date_stamp": "10/1/23 8:11.35", "state_change_type": "A", "category": "1", "state_change_value": "400"},
            {"date_stamp": "10/1/23 8:15.35", "state_change_type": "A", "category": "1", "state_change_value": "500"},
            {"date_stamp": "10/1/23 8:00.35", "state_change_type": "A", "category": "2", "state_change_value": "100"},
            {"date_stamp": "10/1/23 8:01.35", "state_change_type": "A", "category": "2", "state_change_value": "200"},
            {"date_stamp": "10/1/23 8:07.35", "state_change_type": "A", "category": "2", "state_change_value": "300"},
            {"date_stamp": "10/1/23 8:09.35", "state_change_type": "A", "category": "2", "state_change_value": "400"},
            {"date_stamp": "10/1/23 8:12.35", "state_change_type": "A", "category": "2", "state_change_value": "500"},
        ]
    )

    agg_data = aggregate_activity_data(
        event_data_provider=lambda x: event_data,
        data_query_args=ActivityDataQueryArgs(
            start_date=du.datestamp_tryParse("10/1/23 8:00.35"),
            end_date=du.datestamp_tryParse("10/2/23 8:00.35"),
        ),
        date_grouping=du.DateIncrementType.MINUTE
    )

    ph.pretty_print_dataframe(agg_data, display_width=500)