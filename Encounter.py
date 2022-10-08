
from datetime import datetime


class Encounter:
    fieldnames = {'HAR': (11, '---', 'har'),
                  'Admit Date': (19, '----------', 'admit_datetime'),
                  'Admit Time': (0, '----------', 'admit_datetime'),
                  'Arr Date': (19, '--------', 'arrival_datetime'),
                  'Arr Time': (0, '--------', 'arrival_datetime'),
                  'Disch Date': (19, '----------', 'disch_datetime'),
                  'Disch Time': (0, '----------', 'disch_datetime'),
                  'Disch Disp': (10, '----------', 'disch_disp'),
                  'Pt Class': (10, '--------', 'disch_class'),
                  'Admit Dx': (10, '--------', 'admit_dx'),
                  'Primary Dx': (10, '----------', 'primary_dx'),
                  'Diagnosis': (10, '---------', 'ed_dx')
                  }

    def __init__(self, csv_row: dict):

        for name, desc in Encounter.fieldnames.items():

            attr = desc[2]

            # every encounter must have a HAR
            if name == 'HAR':
                self.__dict__[attr] = int(csv_row[name])

            # A patient should always have an admission date and time
            elif name == 'Admit Date':
                x = csv_row[name].strip()
                y = csv_row['Admit Time'].strip()
                x = x + ' ' + y
                try:
                    y = datetime.strptime(x, '%m/%d/%Y %I:%M:%S %p')
                except BaseException:
                    y = datetime.strptime(x, '%m/%d/%Y %I:%M %p')
                self.__dict__[attr] = y

            # the arrival date and time only applies if the patient entered through the ED
            elif name == 'Arr Date':
                x = csv_row[name].strip()
                y = csv_row['Arr Time'].strip()
                if x == '<NA>' or y == '<NA>':
                    self.__dict__[attr] = None
                else:
                    x += ' ' + y
                    try:
                        y = datetime.strptime(x, '%m/%d/%Y %I:%M:%S %p')
                    except BaseException:
                        y = datetime.strptime(x, '%m/%d/%Y %I:%M %p')
                    self.__dict__[attr] = y

            # the patient may not have left yet
            elif name == 'Disch Date':
                x = csv_row[name].strip()
                y = csv_row['Disch Time'].strip()
                if x == '<NA>' or y == '<NA>':
                    self.__dict__[attr] = None
                else:
                    x += ' ' + y
                    try:
                        y = datetime.strptime(x, '%m/%d/%Y %I:%M:%S %p')
                    except BaseException:
                        y = datetime.strptime(x, '%m/%d/%Y %I:%M %p')
                    self.__dict__[attr] = y

            # skip the time values already handled above
            elif name == 'Admit Time' or name == 'Arr Time' or name == 'Disch Time':
                pass

            # all other required fields are simple strings
            else:
                try:
                    self.__dict__[attr] = csv_row[name].strip()
                except BaseException:
                    raise KeyError('dict object passed to Encounter.__init__() does not contain all required fields.')

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __ne__(self, other):
        return hash(self) != hash(other)

    def __ge__(self, other):
        return hash(self) >= hash(other)

    def __gt__(self, other):
        return hash(self) > hash(other)

    def __le__(self, other):
        return hash(self) <= hash(other)

    def __lt__(self, other):
        return hash(self) < hash(other)

    def __hash__(self):
        return hash(str(self.har) + str(self.admit_datetime))

    @staticmethod
    def __build_column__(value, width):
        value = datetime.strftime(value, '%m/%d/%Y %I:%M %p') if isinstance(value, datetime) else str(value)
        length = len(value)
        value = value[0:min(width, length)]
        for i in range(0, width - length):
            value += ' '
        return value

    def __str__(self):
        s1 = ''
        s2 = ''
        for name, desc in Encounter.fieldnames.items():
            if name != 'Eff Time':
                s1 += Encounter.__build_column__(name, desc[0]) + ' '
                s2 += Encounter.__build_column__(desc[1], desc[0]) + ' '
        s3 = '\n' + s1 + '\n' + s2 + '\n'
        for name, desc in Encounter.fieldnames.items():
            if name != 'Admit Time' and name != 'Arr Time' and name != 'Disch Time':
                s3 += Encounter.__build_column__(self.__getattribute__(desc[2]), desc[0]) + ' '
        return s3

    def __repr__(self):
        return self.__str__()

    def __setattr__(self, key, value):
        if key == 'har' or key == 'admit_datetime':
            raise AttributeError('Attributes "har" and "admit_datetime" are immutable.')
        self.__dict__[key] = value

    def csv_rows(self, events) -> dict:
        row = {}
        for name, desc in Encounter.fieldnames.items():
            attr = self.__getattribute__(desc[2])
            if name == 'Admit Date' or name == 'Arr Date' or name == 'Disch Date':
                row[name] = '<NA>' if attr is None else datetime.strftime(attr, '%m/%d/%Y')
            elif name == 'Admit Time' or name == 'Arr Time' or name == 'Disch Time':
                row[name] = '<NA>' if attr is None else datetime.strftime(attr, '%I:%M %p')
            else:
                row[name] = attr
        for event in events:
            r = event.get_csv_row()
            r.update(row)
            yield r
