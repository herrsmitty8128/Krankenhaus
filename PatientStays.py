
from pandas import DataFrame, ExcelWriter
from datetime import datetime
from collections import namedtuple
import AdtEvents as adt
from xlsxutil import one_hour, list_csv_files_in
from Encounter import Encounter
from Event import Event


def build_dataset(dataset: adt.EventDataset) -> DataFrame:

    Stay = namedtuple('Stay', ['HAR', 'disch_class', 'unit', 'start', 'end', 'hours', 'status', 'came_from', 'went_to', 'arrived_as', 'left_as'])

    # helper function used exclusively here
    # Iterates over a list of events and raises a ValueError if the list is invalid.
    # A list of events is considered invalid if any of any of the following are true:
    #    1.) event.evt_type == 'Update' for any event in the list
    #    2.) event.from_unit == event.to_unit for any event in the list
    #    3.) any event in the list is type 'Admission' and that event is not the first event in the list
    #    4.) any event in the list is type 'Discharge' and that event is not the last event in the list
    #    5.) the list is not in chronological order by effective date
    #    6.) if the 'to_unit' for any event is not equal to the 'from_unit' for the next event in the list
    def __validate_events(encounter: Encounter, events: list) -> None:
        i = 0
        while i < len(events):
            if events[i].evt_type == 'Update':
                raise ValueError('Event type cannot be "Update"\n' + Event.build_event_table_str(events, encounter))
            if events[i].from_unit == events[i].to_unit and events[i].from_class == events[i].to_class:
                raise ValueError('"From Unit" == "To Unit" and "From Class" == "To Class"\n' + Event.build_event_table_str(events, encounter))
            if events[i].evt_type == 'Admission' and i != 0:
                raise ValueError('Admission is not the first event.\n' + Event.build_event_table_str(events, encounter))
            if events[i].evt_type == 'Discharge' and i != len(events) - 1:
                raise ValueError('Discharge is not the last event.\n' + Event.build_event_table_str(events, encounter))
            if i + 1 < len(events):
                if events[i].eff_date > events[i + 1].eff_date:
                    raise ValueError('Effective dates are not in chronological order\n' + Event.build_event_table_str(events, encounter))
                if events[i].to_unit != events[i + 1].from_unit:
                    raise ValueError('There appears to be a missing event\n' + Event.build_event_table_str(events, encounter))
            i += 1

    # nested helper function
    def __latest_existing_date(a: datetime, b: datetime) -> datetime:
        x = isinstance(a, datetime)
        y = isinstance(b, datetime)
        if x and not y:
            return a
        if y and not x:
            return b
        if not x and not y:
            raise ValueError('__latest_existing_date() requires at least one valid datetime object')
        return max(a, b)

    # nested helper function
    def __get_eff_date(encounter: Encounter, event: Event) -> datetime:
        return min(encounter.arrival_datetime, event.eff_date) if event.evt_type == 'Admission' and encounter.arrival_datetime is not None else event.eff_date

    # nested helper function
    def __delete_duplicates(events: list) -> None:
        def duplicates(a: Event, b: Event) -> bool:
            return (a.eff_date == b.eff_date and
                    a.evt_type == b.evt_type and
                    a.from_unit == b.from_unit and
                    a.to_unit == b.to_unit)
        i = 0
        while i < len(events):
            j = i + 1
            while j < len(events):
                if duplicates(events[i], events[j]):
                    del events[j]
                    continue
                j += 1
            i += 1

    # nested helper function
    def __sort_out_of_order(events: list) -> None:
        def out_of_order(a: Event, b: Event) -> bool:
            return (a.eff_date == b.eff_date and
                    a.from_unit == b.to_unit and
                    a.to_unit != b.from_unit)
        i = 0
        while i < len(events):
            j = i + 1
            while j < len(events):
                if out_of_order(events[i], events[j]):
                    temp = events.pop(j)
                    events.insert(i, temp)
                    j = i
                j += 1
            i += 1

    # nested helper function
    def __delete_cancellations(events: list) -> None:
        def cancels(a: Event, b: Event) -> bool:
            return (a.eff_date == b.eff_date and
                    a.evt_type == b.evt_type and
                    a.from_unit == b.to_unit and
                    a.to_unit == b.from_unit)
        i = 0
        while i < len(events):
            j = i + 1
            while j < len(events):
                if cancels(events[i], events[j]):
                    del events[j]
                    del events[i]
                    j = i
                j += 1
            i += 1

    # The real work begins here...
    data = []
    for encounter, event_set in dataset.data.items():
        events = [e for e in sorted(event_set, key=lambda x: x.eff_date) if e.evt_type != 'Update' and e.from_unit != e.to_unit]
        if len(events) == 0:
            continue
        __delete_duplicates(events)
        __delete_cancellations(events)
        __sort_out_of_order(events)
        __validate_events(encounter, events)
        first_event = events[0]
        effective_date = __get_eff_date(encounter, first_event)
        if first_event.evt_type != 'Admission' and dataset.start_date < effective_date:
            unit = first_event.from_unit
            arrival = dataset.start_date
            departure = effective_date
            hours = (departure - arrival) / one_hour
            status = 'In-house as of start date'
            came_from = 'Unknown'
            went_to = encounter.disch_disp if first_event.evt_type == 'Discharge' else first_event.to_unit
            arrived_as = 'Unknown'
            left_as = first_event.from_class
            data.append(Stay(encounter.har, encounter.disch_class, unit, arrival, departure, hours, status, came_from, went_to, arrived_as, left_as))
        for i in range(len(events) - 1):
            curr_event = events[i]
            next_event = events[i + 1]
            unit = curr_event.to_unit
            arrival = max(__get_eff_date(encounter, curr_event), dataset.start_date)
            departure = next_event.eff_date
            hours = (departure - arrival) / one_hour
            status = 'Patient stay is complete'
            came_from = 'Home or Self Care' if curr_event.evt_type == 'Admission' else curr_event.from_unit
            went_to = encounter.disch_disp if next_event.evt_type == 'Discharge' else next_event.to_unit
            arrived_as = curr_event.to_class
            left_as = next_event.from_class
            data.append(Stay(encounter.har, encounter.disch_class, unit, arrival, departure, hours, status, came_from, went_to, arrived_as, left_as))
        last_event = events[-1]
        effective_date = __get_eff_date(encounter, last_event)
        if last_event.evt_type != 'Discharge' and effective_date < dataset.end_date:
            unit = last_event.to_unit
            arrival = effective_date
            departure = dataset.end_date
            hours = (departure - arrival) / one_hour
            status = 'In-house as of end date'
            came_from = 'Home or Self Care' if curr_event.evt_type == 'Admission' else last_event.from_unit
            went_to = 'Unknown'
            arrived_as = last_event.to_class
            left_as = 'Unknown'
            data.append(Stay(encounter.har, encounter.disch_class, unit, arrival, departure, hours, status, came_from, went_to, arrived_as, left_as))
    return DataFrame(data)


# for testing
if __name__ == '__main__':

    print('Building file list...')
    adt_file_list = list_csv_files_in('..\\data\\2021\\IAH\\Q2')

    print('Parsing ADT event files and building the ADT EventDataset...')
    events = adt.read_from_csv(adt_file_list)

    print('Building the StayDataset...')
    stays = build_dataset(events)

    print('Writing the StayDataset to "./output files/patient_stays_test.xlsx"...')
    with ExcelWriter('./output files/patient_stays_test.xlsx') as writer:
        stays.to_excel(writer, sheet_name='MyFirstSheet')

    print('Done!')
