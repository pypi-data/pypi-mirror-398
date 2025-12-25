from pybibtexer.tools import compare_bibs_with_local, compare_bibs_with_zotero

from ._base import build_base_options, expand_paths


def run_compare_bib_with_local(
    options: dict,
    need_compare_bib: str,
    path_output: str,
    path_spidered_bibs: str,
    path_spidering_bibs: str,
    path_conf_j_jsons: str,
) -> None:
    """Compare a target bibliography file with local bibliography collections and generate comparison results.

    This function performs a comprehensive comparison between a specified bibliography file and
    existing local bibliography collections. Results are saved to the specified output directory.

    Args:
        options: Configuration dictionary for comparison behavior settings
            compare_each_entry_with_all_local_bibs: Whether to compare each entry with all local bib files
        need_compare_bib: Path to the target bibliography file that needs to be compared
        path_output: Output directory path where comparison results will be saved
        path_spidered_bibs: Directory path containing pre-collected/spidered bibliography files
        path_spidering_bibs: Directory path containing actively spidered bibliography files
        path_conf_j_jsons: Path to conference/journal configuration JSON files

    Returns:
        None: Results are written to files in the specified output directory
    """
    # Expand and normalize file paths
    need_compare_bib, path_output, path_spidered_bibs, path_spidering_bibs = expand_paths(
        need_compare_bib, path_output, path_spidered_bibs, path_spidering_bibs
    )

    # Update options
    options_ = build_base_options([], [], ["arXiv"], [], path_conf_j_jsons)
    options_["include_early_access"] = True
    options_.update(options)

    # Compare
    compare_bibs_with_local(need_compare_bib, path_spidered_bibs, path_spidering_bibs, path_output, options_)


def run_compare_bib_with_zotero(
    options: dict, need_compare_bib: str, zotero_bib: str, path_output: str, path_conf_j_jsons: str
) -> None:
    """Compare a target bibliography file with Zotero bibliography data and generate comparison results.

    This function performs comparison between a specified bibliography file and Zotero bibliography data,
    identifying matches, differences, and potential conflicts between the two sources.

    Args:
        options: Configuration dictionary for comparison behavior settings
        need_compare_bib: Path to the target bibliography file that needs to be compared
        zotero_bib: Path to the Zotero bibliography file or export data
        path_output: Output directory path where comparison results will be saved
        path_conf_j_jsons: Path to conference/journal configuration JSON files

    Returns:
        None: Results are written to files in the specified output directory
    """
    # Expand and normalize file paths
    need_compare_bib, zotero_bib, path_output = expand_paths(need_compare_bib, zotero_bib, path_output)

    # Update options
    options_ = build_base_options([], [], ["arXiv"], [], path_conf_j_jsons)
    options_.update(options)

    # Compare
    compare_bibs_with_zotero(zotero_bib, need_compare_bib, path_output, options_)
