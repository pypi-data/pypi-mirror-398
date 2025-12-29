from datetime import date, timedelta

from seuils.usure import get_trimestre, local_liens


def daterange(start_date: date, end_date: date):
    days = int((end_date - start_date).days)
    for n in range(days):
        yield start_date + timedelta(n)


def test_historique():
    start_date = date(2005, 1, 1)
    end_date = date.today()
    avis = local_liens()
    for single_date in daterange(start_date, end_date):
        assert type(avis[get_trimestre(single_date)]) is str
