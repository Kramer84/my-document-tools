import pytest
from doctools.latex.titles import process_content

@pytest.mark.parametrize("input_tex, expected", [
    (r'\section{a tale of two cities}', r'\section{A Tale of Two Cities}'),
    (r'\subsection*{the quick and the dead}', r'\subsection*{The Quick and the Dead}'),
    (r'\subsubsection{an apple a day}', r'\subsubsection{An Apple a Day}'),
    (r'\section{  spaced   out   title  }', r'\section{Spaced Out Title}'),
    (r'\section{UPPERCASE TITLE}', r'\section{Uppercase Title}'),
    (r'\section{mixed CAse TiTle}', r'\section{Mixed Case Title}'),
    (r'\section{word-with-hyphen}', r'\section{Word-with-hyphen}'),
    (r'\section{the}', r'\section{The}'),
    (r'\section{the deviations space $D_{g}^{\gls{num}}$}', r'\section{The Deviations Space $D_{g}^{\gls{num}}$}')
])
def test_to_title_case_standard(input_tex, expected):
    assert process_content(input_tex) == expected

@pytest.mark.parametrize("input_tex, expected", [
    (r'\section{\textit{italic} and normal}', r'\section{\textit{italic} and Normal}'),
    (r'\section{calculating $E=mc^2$ and more}', r'\section{Calculating $E=mc^2$ and More}'),
    # The brace-counting architecture resolves the nested brace failure:
    (r'\section{the \textbf{great} filter}', r'\section{The \textbf{great} Filter}'),
])
def test_to_title_case_macro_safeguards(input_tex, expected):
    assert process_content(input_tex) == expected

@pytest.mark.xfail(reason="Safeguard fails if math is attached mid-word or ends without space.")
def test_math_mid_word_failure():
    input_tex = r'\section{Equation($E=mc^2$)}'
    # Asserts the ideal outcome, which will fail and correctly log an 'x' (xfail)
    assert process_content(input_tex) == r'\section{Equation($E=mc^2$)}'
