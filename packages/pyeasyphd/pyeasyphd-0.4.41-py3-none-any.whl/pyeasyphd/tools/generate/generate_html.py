import os
from typing import Any

from pyadvtools import write_list
from pybibtexer.bib.bibtexparser import Library
from pybibtexer.main import PythonRunBib, PythonWriters

from ...utils.utils import html_head, html_style, html_tail, textarea_header, textarea_tail


def generate_html_content(html_body, abbr_standard):
    """Create complete HTML document from body content.

    Args:
        html_body: list of HTML body content lines.
        abbr_standard (str): Standard abbreviation for the document.

    Returns:
        list[str]: Complete HTML document as list of lines.
    """
    return [html_head.format(abbr_standard), html_style, "\n", *html_body, *html_tail]


def generate_html_from_bib_data(
    abbr_standard: str,
    original_bib_data: list[str] | str | Library,
    path_output: str,
    options: dict[str, Any] | None = None,
) -> list[str]:
    """Generate HTML from bibliography data.

    Args:
        abbr_standard (str): Standard abbreviation for the publication.
        original_bib_data (list[str] | str | Library): Bibliography data in various formats.
        path_output (str): Path to output directory.
        options (dict[str, Any], optional): Additional processing options. Defaults to {}.
        full_json_c (str, optional): Path to conferences JSON file. Defaults to "".
        full_json_j (str, optional): Path to journals JSON file. Defaults to "".

    Returns:
        list[str]: list of HTML body content lines.
    """
    if options is None:
        options = {}

    # Set processing options
    processing_options: dict = {
        # convert_str_to_library
        "is_standardize_bib": False,
        # middlewares_str_to_library.py
        "is_display_implicit_comments": False,
        #
        # convert_library_to_library.py
        # middlewares_library_to_library.py
        "function_common_again": False,
        "function_common_again_for_abbr": False,
        "function_common_again_for_zotero": False,
        "function_common_again_for_save": False,
        "abbr_index_article_for_abbr": 2,
        "abbr_index_inproceedings_for_abbr": 2,
        #
        # convert_library_to_str.py
        "empty_entry_cite_keys": True,
        # middlewares_library_to_str.py
        "is_sort_entry_fields": True,
        "is_sort_blocks": True,
        "sort_entries_by_field_keys_reverse": True,
    }
    # Update with provided options
    processing_options.update(options)

    # Process bibliography data
    _python_bib = PythonRunBib(processing_options)
    _, zotero_library, _ = _python_bib.parse_to_multi_standard_library(original_bib_data)

    _python_writer = PythonWriters(processing_options)

    # Generate HTML content for each entry
    html_body = []
    for entry in zotero_library.entries:
        html_body.append(_format_entry_to_html(entry, abbr_standard, _python_writer.write_to_str([entry])))

    # Create complete HTML document if entries exist
    if len(html_body) > 0:
        html_body = [
            f'<h2 id="{abbr_standard.lower()}">{abbr_standard} - {len(zotero_library.entries)}</h2>\n',
            "<ul>\n",
            *html_body,
            "</ul>\n",
        ]

        html_content = generate_html_content(html_body, abbr_standard)
        output_dir = os.path.join(path_output, abbr_standard)

        # Write output file
        write_list(html_content, f"{abbr_standard}.html", "w", output_dir, False)

    return html_body


def _format_entry_to_html(entry, abbr, data_list):
    """Format a single bibliography entry into HTML.

    Args:
        entry: Bibliography entry dictionary.
        abbr (str): Publication abbreviation.
        data_list: list of formatted bibliography data.

    Returns:
        str: HTML formatted entry string.
    """
    # Extract entry fields
    number = entry["number"] if "number" in entry else ""
    pages = entry["pages"] if "pages" in entry else ""
    title = entry["title"] if "title" in entry else ""
    year = entry["year"] if "year" in entry else ""
    volume = entry["volume"] if "volume" in entry else ""

    # Get URL (DOI preferred, fall back to URL)
    url = ""
    if "doi" in entry:
        doi = entry["doi"]
        url = doi if doi.startswith("http") else f"https://doi.org/{doi}"
    elif "url" in entry:
        url = entry["url"]

    # Format entry in APA style
    line = _format_entry_to_apa_style(title, year, volume, number, pages, url, abbr)

    line = f"<li><details>\n<summary>\n{line.strip()}\n</summary>\n"

    # Create HTML structure with details
    return line + textarea_header + "".join(data_list).rstrip() + textarea_tail + "\n</details></li>\n"


def _format_entry_to_apa_style(title, year, volume, number, pages, url, abbr):
    """Format entry in APA citation style.

    Args:
        title (str): Article title.
        year (str): Publication year.
        volume (str): Journal volume.
        number (str): Issue number.
        pages (str): Page numbers.
        url (str): Article URL.
        abbr (str): Publication abbreviation.

    Returns:
        str: APA formatted citation string.
    """
    line = f"({year}). {title}. <em>{abbr}</em>"

    if volume:
        line += f", <em>{volume}</em>"
        if number:
            line += f"({number})"

    if pages:
        line += f", {pages}"

    line += "."

    if url:
        line += f" (<a href='{url}'>www</a>)"

    return line
