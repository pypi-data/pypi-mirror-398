import json
from datetime import date
from datetime import datetime
import array


class MatlabDataEncoder(json.JSONEncoder):
    def default(self, field):

        if isinstance(field, datetime):
            return field.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(field, date):
            return field.strftime('%Y-%m-%d')
        elif isinstance(field, array.array):
            return field.tolist()
        elif isinstance(field, memoryview):
            return field.tolist()
        else:
            return json.JSONEncoder.default(self, field)


class DateTimeEncode(json.JSONEncoder):
    def default(self, field):
        if isinstance(field, datetime):
            return field.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(field, date):
            return field.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, field)