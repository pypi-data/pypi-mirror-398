from calendar import monthrange
from datetime import date, datetime, timedelta

DEFAULT_DATE_FORMAT = '%Y-%m-%d'
DEFAULT_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def to_edate(date: date | datetime):
    return EDate(date.year, date.month, date.day)


def to_edatetime(dt: datetime):
    return EDateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)


class EDate(date):
    def datetime(self):
        return datetime(self.year, self.month, self.day)

    def tomorrow(self):
        return to_edate(self.datetime() + timedelta(days=1))

    def yesterday(self):
        return to_edate(self.datetime() - timedelta(days=1))

    def first_day_of_month(self):
        return self.replace(day=1)

    def first_day_of_year(self):
        return self.replace(day=1, month=1)

    def last_day_of_month(self):
        _, ndays = monthrange(self.year, self.month)
        return self.replace(day=ndays)

    def last_day_of_year(self):
        return self.replace(day=31, month=12)

    def first_day_of_last_month(self):
        return self.replace(day=1).yesterday().replace(day=1)

    def first_day_of_last_year(self):
        return self.replace(day=1, month=1, year=self.year - 1)

    def last_day_of_last_month(self):
        return self.replace(day=1).yesterday()

    def last_day_of_last_year(self):
        return self.replace(day=31, month=12, year=self.year - 1)

    def strftime(self, __format=DEFAULT_DATE_FORMAT):
        return super().strftime(__format)

    @staticmethod
    def strptime(__date_string: str, __format=DEFAULT_DATE_FORMAT):
        return to_edate(datetime.strptime(__date_string, __format))

    def __str__(self):
        return self.strftime()


class EDateTime(datetime):
    def first_second_of_minute(self):
        return self.replace(second=0, microsecond=0)

    def last_second_of_minute(self):
        return self.replace(second=59)

    def first_second_of_hour(self):
        return self.first_second_of_minute().replace(minute=0)

    def last_second_of_hour(self):
        return self.last_second_of_minute().replace(minute=59)

    def first_second_of_day(self):
        return self.first_second_of_hour().replace(hour=0)

    def last_second_of_day(self):
        return self.last_second_of_hour().replace(hour=23)

    def one_hour_later(self):
        return self + timedelta(hours=1)

    def hour_ago(self):
        return self - timedelta(hours=1)

    def tomorrow(self):
        return self + timedelta(days=1)

    def yesterday(self):
        return self - timedelta(days=1)

    def first_day_of_month(self):
        return self.replace(day=1)

    def last_day_of_month(self):
        _, ndays = monthrange(self.year, self.month)
        return self.replace(day=ndays)

    def first_day_of_year(self):
        return self.replace(day=1, month=1)

    def last_day_of_year(self):
        return self.replace(day=31, month=12)

    def first_day_of_last_month(self):
        return self.replace(day=1).yesterday().replace(day=1)

    def last_day_of_last_month(self):
        return self.replace(day=1).yesterday()

    def first_day_of_last_year(self):
        return self.replace(day=1, month=1, year=self.year - 1)

    def last_day_of_last_year(self):
        return self.replace(day=31, month=12, year=self.year - 1)

    def strftime(self, __format=DEFAULT_DATETIME_FORMAT):
        return super().strftime(__format)

    @staticmethod
    def strptime(__date_string: str, __format=DEFAULT_DATETIME_FORMAT):
        return to_edatetime(datetime.strptime(__date_string, __format))

    def __str__(self):
        return self.strftime()


def generate_months():
    for month_number in range(1, 13):
        yield month_number
