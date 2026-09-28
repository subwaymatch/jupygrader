"""Tests for how AIGrader shrinks notebook outputs before sending them to the model."""

import copy
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook, new_output

from jupygrader.grading.ai_grader import AIGrader

TEST_NOTEBOOKS_DIR = Path(__file__).resolve().parent / "test-files"

DATAFRAME_HTML = "<table><thead><tr><th>a</th></tr></thead><tbody><tr><td>1</td></tr></tbody></table>"
DATAFRAME_TEXT = "   a\n0  1"
BASE64_PAYLOAD = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="


def _markdown_for_outputs(*outputs):
    cell = new_code_cell("x = 1", outputs=list(outputs))
    return AIGrader.notebook_to_markdown(new_notebook(cells=[cell]))


def test_images_are_removed_but_text_label_is_kept():
    md = _markdown_for_outputs(
        new_output(
            "display_data",
            data={
                "image/png": BASE64_PAYLOAD,
                "text/plain": "<Figure size 640x480 with 1 Axes>",
            },
        )
    )

    assert BASE64_PAYLOAD not in md
    assert "<Figure size 640x480 with 1 Axes>" in md


def test_plain_text_version_is_preferred_over_html():
    md = _markdown_for_outputs(
        new_output(
            "execute_result",
            data={"text/html": DATAFRAME_HTML, "text/plain": DATAFRAME_TEXT},
            execution_count=1,
        )
    )

    assert "<table>" not in md
    assert DATAFRAME_TEXT.splitlines()[1] in md


def test_html_is_kept_when_plain_text_is_only_an_object_repr():
    md = _markdown_for_outputs(
        new_output(
            "display_data",
            data={
                "text/html": "<b>Styled summary</b>",
                "text/plain": "<IPython.core.display.HTML object>",
            },
        ),
        new_output(
            "display_data",
            data={
                "text/html": "<i>Styler table</i>",
                "text/plain": "<pandas.io.formats.style.Styler at 0x7f3a2c1d9e50>",
            },
        ),
    )

    assert "<b>Styled summary</b>" in md
    assert "<i>Styler table</i>" in md


def test_plotly_figures_are_replaced_with_a_placeholder():
    md = _markdown_for_outputs(
        # plotly_mimetype renderer (Jupyter, VS Code)
        new_output(
            "display_data",
            data={"application/vnd.plotly.v1+json": {"data": [], "layout": {}}},
        ),
        # colab / notebook_connected renderers (HTML only)
        new_output(
            "display_data",
            data={
                "text/html": '<div id="abc" class="plotly-graph-div"></div>'
                '<script>Plotly.newPlot("abc", [{"y": [1, 2, 3]}])</script>'
            },
        ),
    )

    assert md.count(AIGrader.PLOTLY_FIGURE_PLACEHOLDER) == 2
    assert "plotly-graph-div" not in md
    assert "Plotly.newPlot" not in md


def test_plotly_loader_script_is_removed():
    loader_html = (
        "<script>window.PlotlyConfig = {MathJaxConfig: 'local'};</script>"
        + "<script>/* plotly.js */"
        + "x" * 50_000
        + "</script>"
    )
    md = _markdown_for_outputs(
        new_output("display_data", data={"text/html": loader_html}),
        new_output(
            "display_data",
            data={
                "text/html": '<div class="plotly-graph-div"></div>',
                "application/vnd.plotly.v1+json": {"data": []},
            },
        ),
    )

    assert "PlotlyConfig" not in md
    assert "xxxxx" not in md
    assert md.count(AIGrader.PLOTLY_FIGURE_PLACEHOLDER) == 1


def test_base64_data_uris_are_removed_from_html_and_markdown():
    html_output = new_output(
        "display_data",
        data={
            "text/html": f'<img src="data:image/png;base64,{BASE64_PAYLOAD}"> caption'
        },
    )
    nb = new_notebook(
        cells=[
            new_markdown_cell(
                f"![chart](data:image/jpeg;base64,{BASE64_PAYLOAD}) text"
            ),
            new_code_cell("x = 1", outputs=[html_output]),
        ]
    )

    md = AIGrader.notebook_to_markdown(nb)

    assert BASE64_PAYLOAD not in md
    assert "data:image/png;base64,[omitted]" in md
    assert "data:image/jpeg;base64,[omitted]" in md
    assert "caption" in md
    assert "text" in md


def test_long_stream_output_is_truncated_keeping_start_and_end():
    lines = [f"line {i}" for i in range(5_000)]
    md = _markdown_for_outputs(
        new_output("stream", name="stdout", text="\n".join(lines))
    )

    assert "line 0" in md
    assert "line 4999" in md
    assert "line 2500" not in md
    assert "characters omitted" in md
    assert len(md) < AIGrader.MAX_OUTPUT_CHARS * 1.5


def test_long_traceback_is_truncated_and_keeps_the_error():
    traceback = [f"\x1b[0;31mframe {i}\x1b[0m" for i in range(3_000)]
    traceback.append("\x1b[0;31mKeyError\x1b[0m: 'missing_column'")
    md = _markdown_for_outputs(
        new_output(
            "error", ename="KeyError", evalue="'missing_column'", traceback=traceback
        )
    )

    assert "KeyError: 'missing_column'" in md
    assert "characters omitted" in md
    assert "\x1b[" not in md
    assert len(md) < AIGrader.MAX_OUTPUT_CHARS * 1.5


def test_short_outputs_are_unchanged():
    md = _markdown_for_outputs(
        new_output("stream", name="stdout", text="hello world\n")
    )

    assert "hello world" in md
    assert "omitted" not in md


def test_input_notebook_is_not_modified():
    nb = new_notebook(
        cells=[
            new_code_cell(
                "x = 1",
                outputs=[
                    new_output(
                        "execute_result",
                        data={
                            "text/html": DATAFRAME_HTML,
                            "text/plain": DATAFRAME_TEXT,
                        },
                        execution_count=1,
                    ),
                    new_output("stream", name="stdout", text="y" * 50_000),
                ],
            )
        ]
    )
    original = copy.deepcopy(nb)

    AIGrader.notebook_to_markdown(nb)

    assert nb == original


def test_saved_plotly_notebook_renderer_output_stays_small():
    # common.ipynb has a Plotly figure saved with the plotly.js library embedded
    # (~3.7 MB of HTML). Sent as-is, it exceeds a 1M-token context window.
    nb = nbformat.read(
        TEST_NOTEBOOKS_DIR / "basic-workflow" / "common.ipynb", as_version=4
    )

    md = AIGrader.notebook_to_markdown(nb)

    assert len(md) < 50_000
    assert AIGrader.PLOTLY_FIGURE_PLACEHOLDER in md
