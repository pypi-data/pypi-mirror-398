"""Small utility functions.
"""

import datetime

import numpy
import pandas


def date_to_utctimestamp(my_date) -> float:
    """Convert input date to float utc timestamp

    Useful to get things into float form for numba functions.
    """
    if pandas.isnull(my_date):
        return numpy.nan
    return datetime.datetime(my_date.year, my_date.month, my_date.day,
                             tzinfo=datetime.timezone.utc).timestamp()
