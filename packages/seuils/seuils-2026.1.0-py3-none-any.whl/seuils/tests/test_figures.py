import pandas as pd
import plotly

from seuils.figures import df, graphique


def test_dataframe():
    data = [df(1000), df(4000), df(10000)]
    for d in data:
        assert type(d) is pd.DataFrame
        assert len(d) >= 87


def test_fig():
    g = graphique(df(3000))
    assert type(g) is plotly.graph_objs._figure.Figure
