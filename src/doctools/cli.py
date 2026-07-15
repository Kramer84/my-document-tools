import typer

from doctools.latex.citations import analyze_citations, search_author
from doctools.latex.labels import normalize_labels
from doctools.latex.titles import normalize_titles
from doctools.python.clean import clean_python
from doctools.python.dependency_graph import generate_pydeps
from doctools.python.sweep import sweep_python_project
from doctools.search_string import search_strings

app = typer.Typer(
    name="doctools",
    help="A suite of tools for document processing and analysis.",
    no_args_is_help=True,
)
latex_app = typer.Typer(
    name="latex",
    help="Tools for manipulating and analyzing LaTeX files.",
    no_args_is_help=True,
)
latex_app.command(name="normalize-labels")(normalize_labels)
latex_app.command(name="normalize-titles")(normalize_titles)
latex_app.command(name="analyze-citations")(analyze_citations)
latex_app.command(name="search-author")(search_author)
python_app = typer.Typer(
    name="python",
    help="Tools for manipulating Python source code.",
    no_args_is_help=True,
)
python_app.command(name="clean")(clean_python)
python_app.command(name="sweep")(sweep_python_project)
python_app.command(name="graph")(generate_pydeps)
app.add_typer(latex_app)
app.add_typer(python_app)
app.command(name="search")(search_strings)


if __name__ == "__main__":
    app()
