from pathlib import Path

from pybibtexer.tools import format_bib_to_abbr_zotero_save_modes, format_bib_to_save_mode_by_entry_type

from ._base import build_base_options, expand_paths


def run_format_bib_to_save_by_entry_type(
    options: dict, need_format_bib: str, path_output: str, path_conf_j_jsons: str
) -> None:
    """Format a bibliography file by organizing entries according to their entry types and save the results.

    This function processes a bibliography file and reorganizes the entries based on their
    bibliographic entry types (e.g., article, conference, book, etc.), creating separate
    organized output files for better management and categorization.

    Args:
        options: Configuration dictionary for formatting behavior settings
        need_format_bib: Path to the bibliography file that needs to be formatted
        path_output: Output directory path where formatted bibliography files will be saved
        path_conf_j_jsons: Path to conference/journal configuration JSON files

    Returns:
        None: Formatted bibliography files are saved to the specified output directory
    """
    # Expand and normalize file paths
    need_format_bib, path_output = expand_paths(need_format_bib, path_output)

    # Update options
    options_ = build_base_options([], [], [], [], path_conf_j_jsons)
    options_.update(options)

    format_bib_to_save_mode_by_entry_type(Path(need_format_bib).stem, path_output, need_format_bib, options=options_)


def run_format_bib_to_abbr_zotero_save(
    options: dict, need_format_bib: str, path_output: str, path_conf_j_jsons: str
) -> None:
    """Format a bibliography file into three different modes: abbreviated, Zotero-compatible, and cleaned source.

    This function processes a bibliography file and generates three formatted versions:
    1. Abbreviated version: Journal/conference names are abbreviated according to standard rules
    2. Zotero-compatible version: Formatted specifically for Zotero reference management software
    3. Source preservation version: Maintains original content with consistent formatting and organization

    Args:
        options: Configuration dictionary for formatting behavior settings
        need_format_bib: Path to the bibliography file that needs to be formatted
        path_output: Output directory path where the three formatted bibliography files will be saved
        path_conf_j_jsons: Path to conference/journal configuration JSON files for abbreviation rules

    Returns:
        None: Three formatted bibliography files are saved to the specified output directory
    """
    # Expand and normalize file paths
    need_format_bib, path_output = expand_paths(need_format_bib, path_output)

    # Update options
    options_ = build_base_options([], [], [], [], path_conf_j_jsons)
    options_.update(options)

    format_bib_to_abbr_zotero_save_modes(need_format_bib, path_output, options=options_)
