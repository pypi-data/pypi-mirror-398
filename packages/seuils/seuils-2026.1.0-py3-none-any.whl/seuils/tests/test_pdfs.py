import requests

from seuils.usure import local_liens, local_pdf, source

dates = sorted(local_liens().keys())


def test_remote():
    online = dates[:-1]
    for x in online:
        response = requests.get(f"{source}/assets/pdf/{x}.pdf")
        assert response.status_code == 200


def test_local():
    for x in dates:
        assert local_pdf(x) is not False
