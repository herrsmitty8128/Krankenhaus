
import pandas as pd
import AdtEvents as adt
import abc
import os


class StaffingModel(abc.ABC):

    @abc.abstractmethod
    def initialize(self, census: pd.DataFrame) -> None:
        pass

    @abc.abstractmethod
    def addVariableStaff(self, patientHours: float, census: pd.DataFrame, c: int, stays: pd.DataFrame, s: int) -> None:
        pass

    @abc.abstractmethod
    def addFixedStaff(self, census: pd.DataFrame, index: int) -> None:
        pass

    @abc.abstractmethod
    def finalize(self, census: pd.DataFrame) -> None:
        pass


def build_DataFrame(start_date: pd.Timestamp, end_date: pd.Timestamp, stays: pd.DataFrame, models: list = [], column: str = 'unit') -> pd.DataFrame:

    # binary search function to lookup an entry in the census list
    def __lookup_census_index(date_list: pd.core.series.Series, date: pd.Timestamp) -> int:
        low = 0
        high = len(date_list) - 1
        index = 0
        while low <= high:
            mid = (low + high + 1) // 2
            if date_list[mid] <= date:
                index = mid
                low = mid + 1
            elif date_list[mid] > date:
                high = mid - 1
        return index

    # create and initialize the census table
    census = pd.DataFrame(data=pd.date_range(start=start_date, end=end_date, freq='h', closed='left'), columns=['Timestamp'])
    census['Hour'] = [x.hour for x in census['Timestamp']]
    census['Weekday'] = [x.day_name() for x in census['Timestamp']]
    census['Total Census'] = 0.0
    census.index.name = 'Id'
    for h in set(stays[column]):
        census[h] = 0.0

    # initialize the staffing models
    for model in models:
        model.initialize(census)
    one_hour = pd.Timedelta(hours=1)

    # calculate the census and the variable staffing
    for s in stays.index:
        stay_start = stays.at[s, 'start']
        stay_end = stays.at[s, 'end']
        a = __lookup_census_index(census['Timestamp'], stay_start)
        b = __lookup_census_index(census['Timestamp'], stay_end) + 1
        for c in census.index[a:b]:
            census_start = census.at[c, 'Timestamp']
            y = max(census_start, stay_start)
            z = min(census_start + one_hour, stay_end)
            hours = 0.0 if y > z else ((z - y) / one_hour)
            if hours != 0.0:
                census.at[c, stays.at[s, column]] += hours
                census.at[c, 'Total Census'] += hours
            for model in models:
                model.addVariableStaff(hours, census, c, stays, s)

    # calculate the fixed staffing levels and finalize the staffing
    for model in models:
        for c in census.index:
            model.addFixedStaff(census, c)
        model.finalize(census)

    # return the census to the caller
    return census


# for testing
if __name__ == '__main__':

    print('Building file list...')
    import os
    data_dir = os.path.abspath('..\\..\\data\\2021\\IAH\\Q2')
    adt_file_list = [os.path.join(data_dir, file) for file in os.listdir(data_dir) if file.endswith('.csv')]

    print('Parsing ADT event files and building the ADT EventDataset...')
    events = adt.read_from_csv(adt_file_list)

    print('Building the StayDataset...')
    import PatientStays as ps
    stays = ps.build_dataset(events)

    print('Calculating the census...')
    census = build_DataFrame(pd.Timestamp(events.start_date), pd.Timestamp(events.end_date), stays)

    print('Writing the StayDataset to "./output files/patient_census_test.xlsx"...')
    with pd.ExcelWriter('../output files/patient_census_test.xlsx') as writer:
        census.to_excel(writer, sheet_name='MyFirstSheet')

    print('Done!')
