import pandas as pd
import plotly.express as px
from fr_date import conv

from . import usure

dates = sorted([conv(x, True) for x in usure.local_liens().keys()])


def df(*montants):
    a, b, c = [], [], []
    for montant in montants:
        a += dates
        b += [
            usure.get_taux(jour=x, montant=montant, categorie="classique")
            for x in dates
        ]
        c += [montant for x in dates]

    data = {"Entrée en vigueur": a, "Taux d'usure (en %)": b, "Montant": c}
    dataframe = pd.DataFrame(data)
    return dataframe


def graphique(data):
    fig = px.line(data, x="Entrée en vigueur", y="Taux d'usure (en %)", color="Montant")
    return fig
