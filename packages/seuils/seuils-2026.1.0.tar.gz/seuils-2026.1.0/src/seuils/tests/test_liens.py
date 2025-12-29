from datetime import date

import pytest
import requests
from fr_date import conv

from seuils.usure import local_liens, source

data = local_liens()
param_list = [(x, data[x]) for x in data]


def test_remote():
    response = requests.get(f"{source}seuils.json")
    assert response.status_code == 200
    response = requests.get(f"{source}avis.json")
    assert response.status_code == 200


@pytest.mark.parametrize(
    "a, b",
    param_list,
)
def test_lien_fonctionnel(a, b):
    assert type(conv(a, True)) is date


#    response = requests.get(b)
#    assert response.status_code == 200


def test_lien_unique():
    data = local_liens()
    liste = [data[x] for x in data]
    assert len(liste) == len(set(liste))
