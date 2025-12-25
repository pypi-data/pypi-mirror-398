import os
import re
from typing import Any

from pyadvtools import standard_path, write_list
from pybibtexer.tools.experiments_base import generate_standard_publisher_abbr_options_dict

from ...main import PandocMdTo
from .generate_html import generate_html_content, generate_html_from_bib_data
from .generate_library import generate_library_by_filters


def preparation(
    path_storage: str,
    path_output: str,
    output_basename: str,
    pub_type: str,
    issue_or_month_flag: str | list[str] = "current_issue",
    year_flag: str | list[str] = "current_year",
    options: dict[str, Any] | None = None,
):
    """Prepare paths and flags for data generation.

    Args:
        path_storage (str): Path to storage directory.
        path_output (str): Path to output directory.
        output_basename (str): Base name for output files.
        pub_type (str): Type of publication.
        issue_or_month_flag (str | list[str], optional): Issue or month flag. Defaults to "current_issue".
        year_flag (str | list[str], optional): Year flag. Defaults to "current_year".
        options (dict[str, Any], optional): Additional options. Defaults to {}.

    Examples:
        |              | current_issue | current_month | all_months |
        |--------------|---------------|---------------|------------|
        | current_year | YES           | YES           | YES        |
        | all_years    | NO            | NO            | YES        |
        | given_years  | NO            | NO            | YES        |

        given_years = ["2020", "2025"]

    Returns:
        tuple[str, str, bool]: Returns (path_root, path_output, combine_flag).
    """
    if options is None:
        options = {}

    # default settings
    path_storage = standard_path(path_storage)
    path_output = standard_path(path_output)

    # "absolute_path" or "relative_path"
    absolute_or_relative_path = options.get("absolute_or_relative_path", "absolute_path")

    # Create path components
    yy = "-".join(year_flag) if isinstance(year_flag, list) else year_flag
    im = "-".join(issue_or_month_flag) if isinstance(issue_or_month_flag, list) else issue_or_month_flag

    if options.get("early_access", False):
        base_path = os.path.join(output_basename, f"{pub_type.title()}_Early_Access", f"{yy}_{im}")
        path_output = os.path.join(path_output + "_Early_Access", f"{yy}_{im}")
    else:
        base_path = os.path.join(output_basename, f"{pub_type.title()}", f"{yy}_{im}")
        path_output = os.path.join(path_output, f"{yy}_{im}")

    path_root = base_path if absolute_or_relative_path == "absolute_path" else ""

    # Determine combine flag
    b = options.get("early_access", False) and (year_flag != "all_years")
    c = year_flag == "current_year"
    c = c and (not isinstance(issue_or_month_flag, list)) and (issue_or_month_flag != "all_months")
    combine_flag = b or c

    return path_root, path_output, combine_flag


def generate_from_bibs_and_write(
    path_storage: str,
    path_output: str,
    output_basename: str,
    pub_type: str,
    generate_or_combine: str,
    year_flag: str | list[str] = "current_year",
    issue_or_month_flag: str | list[str] = "current_issue",
    options: dict[str, Any] | None = None,
) -> None:
    """Generate or combine data from bibliographies.

    Args:
        path_storage (str): Path to storage directory.
        path_output (str): Path to output directory.
        output_basename (str): Base name for output files.
        pub_type (str): Type of publication.
        generate_or_combine (str): Either "generate_data" or "combine_data".
        year_flag (str | list[str], optional): Flag for year selection. Defaults to "current_year".
        issue_or_month_flag (str | list[str], optional): Flag for issue/month selection. Defaults to "current_issue".
        options (dict[str, Any], optional): Additional options. Defaults to {}.
    """
    if options is None:
        options = {}

    path_root, path_output, combine_flag = preparation(
        path_storage, path_output, output_basename, pub_type, issue_or_month_flag, year_flag, options
    )

    if generate_or_combine == "generate_data":
        publisher_abbr_dict = generate_standard_publisher_abbr_options_dict(path_storage, options)
        for publisher in publisher_abbr_dict:
            pp = os.path.join(path_output, publisher.lower())

            publisher_html_body = []
            # Separate for abbr
            for abbr in publisher_abbr_dict[publisher]:
                print(f"*** Processing {publisher.upper()}: {abbr} ***")
                new_options = publisher_abbr_dict[publisher][abbr]

                # Get bibliography path
                path_abbr = os.path.join(path_storage, publisher.lower(), abbr)
                if isinstance(year_flag, str) and year_flag.isdigit():
                    for root, _, files in os.walk(path_abbr, topdown=True):
                        files = [f for f in files if f.endswith(".bib")]
                        if files := [f for f in files if re.search(f"_{year_flag}.bib", f)]:
                            path_abbr = os.path.join(root, files[0])

                # Generate and process library
                library = generate_library_by_filters(path_abbr, issue_or_month_flag, year_flag, new_options)

                # Generate md, tex, pdf, html
                html_body = generate_html_from_bib_data(abbr, library, pp, new_options)
                if combine_flag and html_body:
                    publisher_html_body.extend([*html_body, "\n"])

            # Combine for publisher
            if publisher_html_body:
                html_content = generate_html_content(publisher_html_body[:-1], publisher)
                write_list(html_content, f"{publisher}_all.html", "w", pp, False)

    elif generate_or_combine == "combine_data":
        _combine_data(path_storage, path_root, path_output, combine_flag, options)

    return None


def _combine_data(path_storage, path_root, path_output, combine_flag, options):
    """Combine data from multiple sources.

    Args:
        path_storage: Path to storage directory.
        path_root: Root path for output.
        path_output: Path to output directory.
        combine_flag: Flag indicating whether to combine data.
        options: Configuration options.
    """
    # Compulsory
    options["include_abbr_list"] = []
    options["exclude_abbr_list"] = []
    publisher_abbr_dict = generate_standard_publisher_abbr_options_dict(path_storage, options)
    for publisher in publisher_abbr_dict:
        print(f"*** Combining papers for {publisher.upper()} ***")
        pp = os.path.join(path_output, publisher.lower())
        absolute_path = os.path.join(path_root, publisher) if len(path_root) > 0 else ""

        link = [f"# {publisher.upper()}\n\n"]
        for abbr in publisher_abbr_dict[publisher]:
            if os.path.exists(os.path.join(pp, abbr, f"{abbr}.html")):
                ll = os.path.join(absolute_path, abbr, f"{abbr}.html")
                link.append(f"- [{abbr}]({ll})\n")

        if combine_flag:
            ll = os.path.join(absolute_path, f"{publisher}_all.html")
            link.insert(1, f"- [All Journals]({ll})\n")

        # Process combined content
        if len(link) > 1:
            write_list(link, f"{publisher}_link.md", "w", pp, False)
            PandocMdTo({}).pandoc_md_to_html(pp, pp, f"{publisher}_link.md", f"{publisher}_link.html", True)

        # Clean up
        for name in ["_link"]:
            if os.path.exists(file := os.path.join(pp, f"{publisher}{name}.md")):
                os.remove(file)
