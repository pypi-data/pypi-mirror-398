import sys
from datetime import date
from importlib import resources

from jinja2 import Template

from . import assets
from .figures import df, graphique


def pages(filepath):
    fig = graphique(df(1500, 5000, 10000))
    output_html_path = filepath
    input_html_path = resources.files(assets) / "gitlab_page_template.html"
    plotly_jinja_data = {
        "fig": fig.to_html(full_html=False),
        "maj": date.today().isoformat(),
    }
    with open(output_html_path, "w", encoding="utf-8") as output_file:
        with open(input_html_path) as template_file:
            j2_template = Template(template_file.read())
            output_file.write(j2_template.render(plotly_jinja_data))


if __name__ == "__main__":
    pages(sys.argv[1])
