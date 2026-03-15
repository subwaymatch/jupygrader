import re

from bs4 import BeautifulSoup
from nbconvert import HTMLExporter
from nbformat import NotebookNode

from .models.results import GradedResult
from .notebook_operations import extract_test_case_metadata_from_code


def save_graded_notebook_to_html(
    nb: NotebookNode,
    graded_result: GradedResult,
    html_title: str,
    html_path: str,
) -> None:
    """Save a graded notebook as HTML with enhanced navigation.

    Converts the notebook to HTML and adds a sidebar with links to test case results
    and back-to-top functionality. Also adds styling for the graded results.

    Args:
        nb: The notebook to convert
        graded_result: Grading results to use for the sidebar links
        html_title: Title for the HTML document
        html_path: Path where the HTML file will be saved
    """
    html_exporter = HTMLExporter()
    r = html_exporter.from_notebook_node(
        nb, resources={"metadata": {"name": html_title}}
    )

    # add in-page anchors for test case code cells
    soup = BeautifulSoup(r[0], "html.parser")
    elements = soup.find_all("div", class_="jp-CodeCell")

    tc_counts = {}

    for el in elements:
        cell_code = el.find("div", class_="jp-Editor").getText().strip()
        tc = extract_test_case_metadata_from_code(cell_code)
        if tc:
            tc_name_cleaned = re.sub(r"[^a-zA-Z0-9_-]", "", tc.test_case_name)
            if tc_name_cleaned not in tc_counts:
                tc_counts[tc_name_cleaned] = 0
            tc_counts[tc_name_cleaned] += 1

            anchor_id = f"{tc_name_cleaned}_id{tc_counts[tc_name_cleaned]}"

            # set div's ID so that we can create internal anchors
            el["id"] = anchor_id

    jupygrader_sidebar_container_el = soup.new_tag("div")
    jupygrader_sidebar_container_el["class"] = "jupygrader-sidebar-container"
    soup.body.append(jupygrader_sidebar_container_el)

    back_to_top_el = BeautifulSoup(
        "<a class='graded-item-link back-to-top' data-text='Scroll to Test Case Results Summary' href='#_graded_result'>•</a>",
        "html.parser",
    ).find("a")
    jupygrader_sidebar_container_el.append(back_to_top_el)

    tc_counts = {}

    for o in graded_result.test_case_results:
        tc_name_cleaned = re.sub(r"[^a-zA-Z0-9_-]", "", o.test_case_name)
        if tc_name_cleaned not in tc_counts:
            tc_counts[tc_name_cleaned] = 0
        tc_counts[tc_name_cleaned] += 1

        anchor_id = f"{tc_name_cleaned}_id{tc_counts[tc_name_cleaned]}"
        item_status_classname = (
            "manual-grading-required"
            if o.grade_manually
            else "pass"
            if o.did_pass
            else "fail"
        )

        item_el = soup.new_tag("a")
        item_el.string = ""
        item_el["class"] = f"graded-item-link {item_status_classname}"
        item_el["href"] = f"#{anchor_id}"
        item_el["data-text"] = (
            ("Passed " if o.did_pass else "" if o.grade_manually else "Failed ")
            + o.test_case_name
            + (
                " (manual grading required)"
                if o.grade_manually
                else f" ({o.points} out of {o.available_points})"
            )
        )
        jupygrader_sidebar_container_el.append(item_el)

    # insert css
    head = soup.head

    jupygrader_sidebar_css = """
   html {
    scroll-behavior: smooth;
    }
    .jupygrader-sidebar-container {
    font-family: var(--jp-content-font-family);
    position: fixed;
    top: 0;
    left: 0;
    width: 24px;
    height: calc(100% - 8px);
    display: flex;
    flex-direction: column;
    gap: 3px;
    z-index: 999;
    padding: 4px 0;
    }
    .graded-item-link {
    flex: 1;
    position: relative;
    color: white;
    background-color: #000;
    display: flex;
    flex-direction: column;
    justify-content: center;
    text-align: center;
    font-size: 12px;
    border-radius: 3px;
    margin: 0 4px 0 2px;
    }
    .graded-item-link:hover {
    position: relative;
    z-index: 1;
    }
    .graded-item-link.back-to-top {
    flex-grow: 0;
    padding: 2px 0;
    }
    .graded-item-link.back-to-top:hover {
    color: #ddd;
    background-color: #222;
    }
    .graded-item-link.pass {
    background-color: #4caf50;
    }
    .graded-item-link.pass:hover {
    background-color: #388e3c;
    }
    .graded-item-link.fail {
    background-color: #f44336;
    }
    .graded-item-link.fail:hover {
    background-color: #d32f2f;
    }
    .graded-item-link.manual-grading-required {
    background-color: #ffeb3b;
    }
    .graded-item-link.manual-grading-required:hover {
    background-color: #fdd835;
    }
    /* tooltip */
    .graded-item-link:before {
    content: attr(data-text);
    /* here's the magic */
    position: absolute;
    /* vertically center */
    top: 50%;
    transform: translateY(-50%);
    /* move to right */
    left: 100%;
    /* basic styles */
    width: 300px;
    padding: 8px 10px 10px 10px;
    background: #fff;
    color: #000;
    border: 4px solid #000;
    text-align: left;
    display: none;
    /* hide by default */
    }
    .graded-item-link.back-to-top:before {
    border-color: #000000;
    }
    .graded-item-link.pass:before {
    color: #4caf50;
    border-color: #4caf50;
    }
    .graded-item-link.fail:before {
    color: #f44336;
    border-color: #f44336;
    }
    .graded-item-link.manual-grading-required:before {
    color: #777;
    border-color: #ffeb3b;
    }
    .graded-item-link:hover:before {
    display: block;
    }
    """

    new_style = soup.new_tag("style", type="text/css")
    new_style.append(jupygrader_sidebar_css)

    head.append(new_style)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(soup.prettify())
