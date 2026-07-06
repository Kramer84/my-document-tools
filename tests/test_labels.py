import pytest
from doctools.latex.labels import normalize_title, parse_sections_and_labels

@pytest.mark.parametrize("input_title, expected_label", [
    ("Introduction", "introduction"),
    ("Data & Methods / Analysis", "data_and_methods_analysis"),
    ("Cost ($USD$)", "cost_usd"),
    ("A very, VERY long title! @2026", "a_very_very_long_title_2026"),
    ("   Spaces   Everywhere   ", "spaces_everywhere"),
    (r"Math $\alpha$ and $\beta$", "math_alpha_and_beta"),
    ("section_with_underscores", "section_with_underscores"),
    ("Hyphenated-Title", "hyphenated-title"),
    (r"The Deviations Space $D_{g}^{\gls{num}}$", "the_deviations_space_d_gglsnum"),
])
def test_normalize_title_variations(input_title, expected_label):
    assert normalize_title(input_title) == expected_label

def test_parse_sections_and_labels_file_io(temp_workspace):
    tex_file = temp_workspace / "test.tex"
    tex_file.write_text(
        "\\section{Introduction}\n"
        "\\label{sec:intro}\n"
        "\\subsection*{Background}\n"
        "\\subsubsection{Deep Dive}\n"
        "\\label{sssec:deep_dive}\n"
    )

    lines, results = parse_sections_and_labels(tex_file, 'utf-8')
    assert len(results) == 3

    # Section
    assert results[0][1] == 'section'
    assert results[0][2] == 'Introduction'
    assert results[0][3] == 'sec:intro'

    # Subsection (Starred, no label)
    assert results[1][1] == 'subsection'
    assert results[1][2] == 'Background'
    assert results[1][3] is None

    # Subsubsection
    assert results[2][1] == 'subsubsection'
    assert results[2][2] == 'Deep Dive'
    assert results[2][3] == 'sssec:deep_dive'
