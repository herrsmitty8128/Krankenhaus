
from datetime import datetime
from Encounter import Encounter


class Event:

    # A list of all possible event types
    evt_types = frozenset(['Admission',
                           'Discharge',
                           'Transfer',
                           'Update'
                           ])

    # These are the field names and descriptors that are required to exist
    # in the csv_row argment that is passed to __init__()
    fieldnames = {'Event ID': (8, '--------', 'ID'),
                  'Event Type': (10, '----------', 'evt_type'),
                  'Eff Date': (20, '--------', 'eff_date'),
                  'Eff Time': (0, '--------------', 'eff_date'),
                  'From Unit': (16, '---------', 'from_unit'),
                  'To Unit': (16, '-------', 'to_unit'),
                  'User': (16, '----', 'user'),
                  'From Class': (16, '----------', 'from_class'),
                  'To Class': (16, '--------', 'to_class'),
                  'Location': (16, '--------', 'location')
                  }

    def __init__(self, csv_row: dict, dept_synonyms: dict):

        for name, desc in Event.fieldnames.items():

            attr = desc[2]

            # every event must have a unique id number
            if name == 'Event ID':
                self.__dict__[attr] = int(csv_row[name])

            # every event must have an effective date and time
            elif name == 'Eff Date':
                x = csv_row[name].strip()
                y = csv_row['Eff Time'].strip()
                x += ' ' + y
                try:
                    y = datetime.strptime(x, '%m/%d/%Y %I:%M:%S %p')
                except BaseException:
                    y = datetime.strptime(x, '%m/%d/%Y %I:%M %p')
                self.__dict__[attr] = y

            # skip the effective time, which is already handled above
            elif name == 'Eff Time':
                pass

            # every event must have a type
            # every event type must exist in Event.evt_types
            elif name == 'Event Type':
                x = None
                y = csv_row[name].strip().casefold()
                for t in Event.evt_types:
                    if t.casefold() in y:
                        x = t
                        break
                if x:
                    self.__dict__[attr] = x
                else:
                    raise ValueError('Invalid event type detected.')

            elif name == 'From Unit' or name == 'To Unit':
                x = csv_row[name].strip()

                # dept_synonyms is a dict object used to replace deparment names with
                # a standard name. This is useful in situations where there are multiple
                # names for a department but a single standard name is needed for processing.
                y = dept_synonyms.get(x, x)
                try:
                    self.__dict__[attr] = y
                except BaseException:
                    raise KeyError('dict object passed to Event.__init__() does not contain all required fields.')

            # all other required fields are simple strings
            else:
                try:
                    self.__dict__[attr] = csv_row[name].strip()
                except BaseException:
                    raise KeyError('dict object passed to Event.__init__() does not contain all required fields.')

    def __eq__(self, other):
        return self.ID == other.ID

    def __ge__(self, other):
        return self.ID >= other.ID

    def __gt__(self, other):
        return self.ID > other.ID

    def __le__(self, other):
        return self.ID <= other.ID

    def __lt__(self, other):
        return self.ID < other.ID

    def __ne__(self, other):
        return self.ID != other.ID

    def __hash__(self):
        return self.ID

    def __str__(self):
        s = ''
        for name, desc in Event.fieldnames.items():
            if name != 'Eff Time':
                s += Event.__build_column__(self.__getattribute__(desc[2]), desc[0]) + ' '
        return s

    def __repr__(self):
        return self.__str__()

    def __setattr__(self, key, value):
        if key == 'ID':
            raise AttributeError('Attribute "ID" is immutable.')
        self.__dict__[key] = value

    def get_csv_row(self) -> dict:
        row = {}
        for name, desc in Event.fieldnames.items():
            attr = self.__getattribute__(desc[2])
            if name == 'Eff Date':
                row[name] = datetime.strftime(attr, '%m/%d/%Y')
            elif name == 'Eff Time':
                row[name] = datetime.strftime(attr, '%I:%M %p')
            else:
                row[name] = attr
        return row

    @staticmethod
    def __build_column__(value, width):
        value = datetime.strftime(value, '%m/%d/%Y %I:%M %p') if isinstance(value, datetime) else str(value)
        length = len(value)
        value = value[0:min(width, length)]
        for i in range(0, width - length):
            value += ' '
        return value

    @classmethod
    def build_event_table_str(cls, events: list, encounter: Encounter = None) -> str:
        s1 = ''
        s2 = ''
        for name, desc in cls.fieldnames.items():
            if name != 'Eff Time':
                s1 += cls.__build_column__(name, desc[0]) + ' '
                s2 += cls.__build_column__(desc[1], desc[0]) + ' '
        s3 = str(encounter) + '\n' + s1 + '\n' + s2 + '\n'
        for event in events:
            s3 += str(event) + '\n'
        return s3
