from datetime import timedelta

from ..utils.date import EDate, EDateTime, to_edate


def resolve_date(date_or_days_ago: EDate | str | int, default=None):
    if isinstance(date_or_days_ago, EDate):
        return date_or_days_ago
    elif isinstance(date_or_days_ago, int):
        return to_edate(EDateTime.now().first_second_of_day() - timedelta(days=abs(date_or_days_ago)))
    elif isinstance(date_or_days_ago, str):
        return EDate.strptime(date_or_days_ago)
    else:
        return default or EDate.today().yesterday()


def resolve_month(date_or_months_ago: EDate | str | int, default=None):
    if isinstance(date_or_months_ago, EDate):
        return date_or_months_ago
    elif isinstance(date_or_months_ago, int):
        date = EDate.today().first_day_of_month()
        for _ in range(abs(date_or_months_ago)):
            date = date.first_day_of_last_month()
        return date
    elif isinstance(date_or_months_ago, str):
        return EDate.strptime(date_or_months_ago)
    else:
        return default or EDate.today().first_day_of_month()
