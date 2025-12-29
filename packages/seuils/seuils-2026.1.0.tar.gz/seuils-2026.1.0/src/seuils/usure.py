import json
import os
from datetime import date
from decimal import Decimal
from importlib import resources

import requests
from fr_date import conv

from . import data, pdf

source = (
    "https://seuils-usure-outils-jcp-1feb902fc0837a7803cd3e9a229a5b9fc188f66.gitlab.io/"
)


def local_data():
    with open(resources.files(data) / "seuils.json", "r") as f:
        seuils = json.loads(f.read())
    return seuils


def remote_data():
    try:
        seuils = requests.get(f"{source}seuils.json", timeout=10).json()
    except requests.exceptions.ConnectionError:
        seuils = local_data()
    return seuils


def local_liens():
    with open(resources.files(data) / "avis.json", "r") as f:
        avis = json.loads(f.read())
    return avis


def remote_liens():
    try:
        avis = requests.get(f"{source}avis.json", timeout=10).json()
    except requests.exceptions.ConnectionError:
        avis = local_liens()
    return avis


def local_pdf(jour):
    file = resources.files(pdf) / f"{jour}.pdf"
    if os.path.isfile(file):
        return file
    return False


def remote_pdf(jour):
    try:
        avis = requests.get(f"{source}assets/pdf/{jour}.pdf", timeout=10)
    except requests.exceptions.ConnectionError:
        avis = local_liens()
    return avis


def get_trimestre(jour):
    if type(jour) is date:
        vigueur = jour
    else:
        vigueur = conv(jour, True)
        if type(vigueur) is not date:
            raise ValueError
    if vigueur.year == 2023:
        return vigueur.replace(day=1).isoformat()
    else:
        mois = {}
        for m in range(1, 13):
            mois[m] = m - (m - 1) % 3
        return vigueur.replace(month=mois[vigueur.month], day=1).isoformat()


def get_lien(jour):
    trimestre = get_trimestre(jour)
    avis = local_liens()
    if trimestre in avis:
        lien = avis[trimestre]
    else:
        avis = remote_liens()
        if trimestre in avis:
            lien = avis[trimestre]
        else:
            lien = "lien introuvable"
    return lien


def get_pdf(jour):
    trimestre = get_trimestre(jour)
    avis = local_pdf(trimestre)
    if avis:
        return avis
    else:
        avis = remote_pdf(trimestre)
        if avis:
            return avis
        else:
            return None


def get_taux(jour, montant=None, categorie=None):
    trimestre = get_trimestre(jour)
    data = local_data()
    if trimestre in data:
        seuils = data[trimestre]["seuils"]
    else:
        data = remote_data()
        if trimestre in data:
            seuils = data[trimestre]["seuils"]
        else:
            return None
    if montant:
        for s in seuils:
            if Decimal(s["min"]) < montant <= Decimal(s["max"]):
                if categorie and "categorie" in s:
                    if categorie == s["categorie"]:
                        return Decimal(s["taux"])
                elif "categorie" in s:
                    return seuils
                else:
                    return Decimal(s["taux"])
    return seuils
