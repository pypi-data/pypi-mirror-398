# Module providing functions related to declaration period

from datetime import datetime
from typing import List, Tuple

from ositah.utils.exceptions import ValidationPeriodAmbiguous, ValidationPeriodMissing


class OSITAHDeclarationPeriod:
    def __init__(self, name: str, start_date: str, end_date: str, validation_date: str):
        self._name = name
        self._start_date = start_date
        self._end_date = end_date
        self._validation_date = validation_date

    @property
    def name(self):
        return self._name

    @property
    def dates(self):
        return self.start_date, self.end_date

    @property
    def label(self):
        return f"{self.name} ({' au '.join(self.dates)})"

    @property
    def end_date(self):
        return self._end_date

    @property
    def start_date(self):
        return self._start_date

    @property
    def validation_date(self):
        return self._validation_date


def get_validation_period_data(period_date: str):
    """
    Return the current declaration period object.

    :param period_date: a date that must be inside the declaration period
    :return: declaration period object (OSITAHValidationPeriod)
    """

    from ositah.utils.hito_db_model import OSITAHValidationPeriod

    selection_date = datetime.fromisoformat(period_date)
    period_id = OSITAHValidationPeriod.query.filter(
        OSITAHValidationPeriod.start_date <= selection_date,
        OSITAHValidationPeriod.end_date >= selection_date,
    ).all()
    if len(period_id) == 1:
        return period_id[0]
    elif len(period_id) > 1:
        raise ValidationPeriodAmbiguous(selection_date)
    else:
        raise ValidationPeriodMissing(selection_date)


def get_validation_period_dates(period_date: str) -> Tuple[datetime, datetime]:
    """
    Return the start and end date of the current declaration period.

    :param period_date: a date that must be inside the declaration period
    :return: validation period start and end date as datetime objects
    """

    validation_period = get_validation_period_data(period_date)
    return validation_period.start_date, validation_period.end_date


def get_validation_period_id(period_date: str):
    """
    Return the current declaration period ID.

    :param period_date: a date that must be inside the declaration period
    :return: UUID
    """

    return get_validation_period_data(period_date).id


def get_declaration_periods(descending: bool = True) -> List[OSITAHDeclarationPeriod]:
    """
    Return a list of declaration period name and dates, sorted by start date in descending order.
    Dates are strings, without the time information.

    :param descending: if True, sort in descending order (default), else in ascending order
    :return: list of OSITAHDeclarationPeriod
    """

    from ositah.utils.hito_db_model import OSITAHValidationPeriod

    periods = []

    periods_data = OSITAHValidationPeriod.query.order_by(
        OSITAHValidationPeriod.start_date.desc()
        if descending
        else OSITAHValidationPeriod.start_date.asc()
    ).all()

    for row in periods_data:
        periods.append(
            OSITAHDeclarationPeriod(
                row.name,
                row.start_date.date().isoformat(),
                row.end_date.date().isoformat(),
                row.validation_date.date().isoformat(),
            )
        )

    return periods


def get_default_period_date(periods: List[OSITAHDeclarationPeriod], date: datetime.date):
    """
    Return the start date of the default period. The default period is selected by passing a date
    that must be between period start and end dates (included). If none matches, select the last
    period.

    :param periods: period list
    :param date: date that must be inside the period (string)
    :return: period start date (string) or None if not found
    """

    period_date = date.isoformat()
    last_start_date = None

    for p in periods:
        if period_date >= p.start_date and period_date <= p.end_date:
            return p.start_date
        if last_start_date is None or p.start_date > last_start_date:
            last_start_date = p.start_date

    return last_start_date
