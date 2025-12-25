from pybibtexer.tools import replace_to_standard_cite_keys

from ._base import build_base_options, expand_paths


def run_replace_to_standard_cite_keys(
    full_tex_md: str, full_bib: str, path_output: str, path_conf_j_jsons: str, options: dict | None = None
) -> None:
    """Replace citation keys in LaTeX documents with standardized versions.

    Processes LaTeX and BibTeX files to normalize citation keys according to
    configuration standards, then outputs the results to the specified location.

    Args:
        options: dictionary of configuration options for citation processing
        full_tex_md: Path to TeX or Markdown file containing citations
        full_bib: Path to the BibTeX bibliography file
        path_output: Output directory path for processed files
        path_conf_j_jsons: Path to journal configuration JSON files

    Returns:
        None: Results are written to the output directory
    """
    if options is None:
        options = {}

    # Expand and normalize file paths
    full_tex_md, full_bib, path_output = expand_paths(full_tex_md, full_bib, path_output)

    # Update options
    options_ = build_base_options([], [], [], [], path_conf_j_jsons)
    options_.update(options)

    replace_to_standard_cite_keys(full_tex_md, full_bib, path_output, options=options_)
