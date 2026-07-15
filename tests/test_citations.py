import pytest

from doctools.latex.citations import (
    extract_bib_field,
    extract_citations,
    remove_latex_comments,
    search_author_citations,
)


@pytest.mark.parametrize(
    "input_text, expected",
    [
        ("Citation \\cite{Smith20} % Comment here", "Citation \\cite{Smith20} "),
        ("No comments here \\cite{Jones21}", "No comments here \\cite{Jones21}"),
        ("Escaped \\% symbol \\cite{Alpha}", "Escaped \\% symbol \\cite{Alpha}"),
        ("Multiple % comments % in a row", "Multiple "),
    ],
)
def test_remove_latex_comments_standard(input_text, expected):
    assert remove_latex_comments(input_text) == expected


def test_remove_latex_comments_newline_edge_case():
    text = "End of line \\\\ % comment"

    assert remove_latex_comments(text) == "End of line \\\\ "


@pytest.mark.parametrize(
    "input_text, expected_citations",
    [
        ("Single \\cite{Alpha19}", ["Alpha19"]),
        ("Multiple \\cite{Alpha19, Beta20}", ["Alpha19", "Beta20"]),
        ("Spaced \\cite{ Alpha19 , Beta20 }", ["Alpha19", "Beta20"]),
        ("Optional args \\cite[p. 4]{Gamma21}", ["Gamma21"]),
        ("Footnote cite \\footcite{Delta22}", ["Delta22"]),
    ],
)
def test_extract_citations_variations(input_text, expected_citations):
    assert extract_citations(input_text) == expected_citations


@pytest.mark.parametrize(
    "body, field, expected",
    [
        (
            "author = {Smith, John and Doe, Jane},\nyear = {2020}",
            "author",
            "Smith, John and Doe, Jane",
        ),
        ('author = "Smith, John",\nyear = "2020"', "author", "Smith, John"),
        ("year = 2020,\nmonth = jan", "year", "2020"),
        ("title = {A {Nested} Title},\nyear = 2020", "title", "A {Nested} Title"),
    ],
)
def test_extract_bib_field_standard(body, field, expected):
    assert extract_bib_field(body, field) == expected


@pytest.mark.xfail(reason="Custom parser cannot handle BibTeX string concatenation.")
def test_extract_bib_field_concatenation_failure():
    body = 'author = "Smith, John" # " and " # "Doe, Jane",\nyear = 2020'

    assert extract_bib_field(body, "author") == "Smith, John and Doe, Jane"


def test_search_author_citations_logic():
    bib_data = {
        "Smith2020": {"authors": "Smith, John and Doe, Jane", "body": ""},
        "Jones2021": {"authors": "Jones, Bob", "body": ""},
    }
    csv_data = [
        {"citation_key": "Smith2020", "filename": "chapter1.tex"},
        {"citation_key": "UnknownKey", "filename": "chapter2.tex"},
    ]

    results = search_author_citations("smith", bib_data, csv_data)
    assert "Smith2020" in results
    assert results["Smith2020"]["authors"] == "Smith, John and Doe, Jane"

    assert results["Smith2020"]["locations"] == {}
