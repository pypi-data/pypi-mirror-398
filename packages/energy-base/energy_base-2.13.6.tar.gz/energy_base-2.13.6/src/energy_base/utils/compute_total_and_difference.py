def compute_percent(fact, plan, is_abs=True):
    if not plan or fact is None:
        return None
    percent = round((100 * (fact - plan) / plan), 2)
    if is_abs:
        return abs(percent)
    return percent

def compute_difference_percent(a, b):
    return 100 * (a or 0) / (b or 1)

def compute_total_and_difference(total_given_date, total_given_date_prev):
    total_given_date = total_given_date or 0
    total_given_date_prev = total_given_date_prev or 0
    return {
        'total': total_given_date,
        'difference': total_given_date - total_given_date_prev,
        'difference_percent': 0 if not total_given_date and not total_given_date_prev else 100 * total_given_date / (
            total_given_date_prev or 1) - 100
    }
