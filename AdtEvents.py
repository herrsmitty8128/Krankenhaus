
from datetime import datetime, timedelta
from collections import namedtuple
from Encounter import Encounter
from Event import Event
import csv

EventDataset = namedtuple('EventDataset', ['start_date', 'end_date', 'data'])


def read_from_csv(filenames: list) -> EventDataset:
    '''
    Loads all events from each download file in adt_file_list and returns an initial
    dataset for futher review and analysis. The dataset is a dict object whose keys
    are HAR numbers and values are patients.
    '''
    max_eff_date = None
    min_eff_date = None
    dataset = {}
    for file in filenames:
        with open(file, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                encounter = Encounter(row)
                event = Event(row)
                event_set = dataset.get(encounter, None)
                if event_set:
                    event_set.add(event)
                else:
                    dataset[encounter] = {event}
                min_eff_date = event.eff_date if min_eff_date is None else min(event.eff_date, min_eff_date)
                max_eff_date = event.eff_date if max_eff_date is None else max(event.eff_date, max_eff_date)
    min_eff_date = datetime(min_eff_date.year, min_eff_date.month, min_eff_date.day)
    max_eff_date = datetime(max_eff_date.year, max_eff_date.month, max_eff_date.day) + timedelta(days=1)
    return EventDataset(min_eff_date, max_eff_date, dataset)


def write_to_csv(dataset: EventDataset, filename: str) -> None:
    if len(dataset.data) == 0:
        return
    with open(filename, 'w', newline='') as csvfile:
        headers = [k for k in Encounter.fieldnames.keys()]
        headers.extend(Event.fieldnames.keys())
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for encounter, event_set in dataset.data.items():
            for row in encounter.csv_rows(event_set):
                writer.writerow(row)


# for testing
if __name__ == '__main__':
    import os

    print('Building file list...')
    data_dir = os.path.abspath('..\\data\\2021\\IAH\\with_disch_date')
    adt_file_list = [os.path.join(data_dir, file) for file in os.listdir(data_dir) if file.endswith('.csv')]

    print('Parsing files and building the dataset...')
    dataset = read_from_csv(adt_file_list)

    print('Writing the dataset to "./output files/events.csv"...')
    write_to_csv(dataset, './output files/events.csv')

    print('Reading "./output files/events.csv"...')
    dataset = read_from_csv(['./output files/events.csv'])

    print('Done!')
