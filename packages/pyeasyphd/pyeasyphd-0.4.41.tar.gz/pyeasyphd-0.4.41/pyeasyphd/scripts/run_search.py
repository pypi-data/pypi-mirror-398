import os
from typing import Any

from pyadvtools import transform_to_data_list
from pybibtexer.tools import compare_bibs_with_zotero

from pyeasyphd.tools import Searchkeywords

from ._base import build_base_options, build_search_options, expand_path, expand_paths


def run_search_for_screen(
    acronym: str, year: int, title: str, path_spidered_bibs: str, path_spidering_bibs: str, path_conf_j_jsons: str
) -> None:
    """Run search for screen display with specific conference/journal parameters.

    Args:
        acronym: Conference/journal acronym to search for
        year: Publication year to filter by (0 means all years)
        title: Paper title used as search keyword
        path_spidered_bibs: Path to spidered bibliography files
        path_spidering_bibs: Path to spidering bibliography files
        path_conf_j_jsons: Path to conferences/journals JSON files
    """
    # Handle year filtering: if year is 0, search all years (empty list)
    search_year_list = [str(year)]
    if year == 0:
        search_year_list = []  # Empty list means no year filtering

    # Expand and normalize file paths
    path_spidered_bibs, path_spidering_bibs, path_conf_j_jsons = expand_paths(
        path_spidered_bibs, path_spidering_bibs, path_conf_j_jsons
    )

    # Configure search options
    options = {
        **build_base_options(
            include_publisher_list=[],
            include_abbr_list=[acronym],
            exclude_publisher_list=["arXiv"],
            exclude_abbr_list=[],
            path_conf_j_jsons=path_conf_j_jsons,
        ),
        **build_search_options(
            print_on_screen=True,
            search_year_list=search_year_list,  # Empty list for all years, otherwise specific year
            keywords_type="Temp",
            keywords_list_list=[[title]],  # Use title as search keyword
        ),
    }

    # Execute searches across different bibliography sources
    _execute_searches(options, "", path_spidered_bibs, path_spidering_bibs, True, True)

    return None


def run_search_for_files(
    keywords_type: str,
    keywords_list_list: list[list[str]],
    path_main_output: str,
    path_spidered_bibs: str,
    path_spidering_bibs: str,
    path_conf_j_jsons: str,
    search_in_spidered_bibs: bool = False,
    search_in_spidering_bibs: bool = True,
    options: dict | None = None,
) -> None:
    """Run search and save results to files with custom keywords.

    Args:
        keywords_type: Category name for the search keywords (used for organizing results)
        keywords_list_list: Nested list of keywords to search for (each inner list represents a search group)
        path_main_output: Main output directory for search results
        path_spidered_bibs: Path to spidered bibliography files
        path_spidering_bibs: Path to spidering bibliography files
        path_conf_j_jsons: Path to conferences/journals JSON files
        search_in_spidered_bibs: Whether to search in spidered bibliography files
        search_in_spidering_bibs: Whether to search in spidering bibliography files
        options: Additional search options to override defaults
    """
    # Initialize options dictionary if not provided
    if options is None:
        options = {}

    # Expand and normalize file paths to ensure consistent path formatting
    path_main_output = expand_path(path_main_output)
    path_spidered_bibs, path_spidering_bibs, path_conf_j_jsons = expand_paths(
        path_spidered_bibs, path_spidering_bibs, path_conf_j_jsons
    )

    # Configure search options by combining base options and search-specific options
    options_ = {
        **build_base_options(
            include_publisher_list=[],  # No specific publishers to include
            include_abbr_list=[],  # No specific conference/journal abbreviations to include
            exclude_publisher_list=["arXiv"],  # Exclude arXiv publications from search
            exclude_abbr_list=[],  # No specific conference/journal abbreviations to exclude
            path_conf_j_jsons=path_conf_j_jsons,  # Path to conference/journal metadata
        ),
        **build_search_options(
            print_on_screen=False,  # Disable screen output (results go to files only)
            search_year_list=[],  # Empty list means search all years (no year filtering)
            keywords_type=keywords_type,  # Use provided keyword category for result organization
            keywords_list_list=keywords_list_list,  # Use provided nested keyword lists for searching
        ),
    }
    # Update with any additional options provided by caller (overrides defaults)
    options_.update(options)

    # Execute searches across different bibliography sources with configured options
    _execute_searches(
        options_,
        path_main_output,
        path_spidered_bibs,
        path_spidering_bibs,
        search_in_spidered_bibs,  # Flag to control spidered bibliography search
        search_in_spidering_bibs,  # Flag to control spidering bibliography search
    )

    return None


def _execute_searches(
    options: dict[str, Any],
    path_main_output: str,
    path_spidered_bibs: str,
    path_spidering_bibs: str,
    search_in_spidered_bibs: bool = False,
    search_in_spidering_bibs: bool = True,
) -> None:
    """Execute searches across different bibliography sources.

    Args:
        options: Search configuration options
        path_main_output: Base path for search results output
        path_spidered_bibs: Path to spidered bibliography files
        path_spidering_bibs: Path to spidering bibliography files
        search_in_spidered_bibs: Whether to search in spidered bibliography files
        search_in_spidering_bibs: Whether to search in spidering bibliography files
    """
    # Search in spidered bibliographies (Conferences and Journals)
    # If enabled, search through completed/conference and journal bibliographies
    if search_in_spidered_bibs:
        for cj in ["Conferences", "Journals"]:
            # Construct path to stored bibliography files for conferences/journals
            path_storage = os.path.join(path_spidered_bibs, cj)
            # Construct output path for search results
            path_output = os.path.join(path_main_output, "Search_spidered_bib", cj)
            # Execute search with given options and paths
            Searchkeywords(path_storage, path_output, options).run()

    # Search in spidering bibliographies (Journals and Journals Early Access)
    # If enabled, search through actively spidering/in-progress journal bibliographies
    if search_in_spidering_bibs:
        for je in ["spider_j", "spider_j_e"]:
            # Construct path to spidering bibliography files (journals and early access)
            path_storage = os.path.join(path_spidering_bibs, je)
            # Construct output path for search results
            path_output = os.path.join(path_main_output, "Search_spidering_bib", je)
            # Execute search with given options and paths
            Searchkeywords(path_storage, path_output, options).run()

    return None


def run_compare_after_search(zotero_bib: str, keywords_type: str, path_main_output: str, path_conf_j_jsons: str):
    """Compare search results with Zotero bibliography and generate comparison report.

    Args:
        zotero_bib: Path to Zotero bibliography file
        keywords_type: Category name for the search keywords used
        path_main_output: Main output directory for search results and comparison
        path_conf_j_jsons: Path to conferences/journals JSON files
    """
    # Expand and normalize file paths
    zotero_bib = expand_path(zotero_bib)
    path_main_output = expand_path(path_main_output)
    path_conf_j_jsons = expand_path(path_conf_j_jsons)

    # Configure search options
    options = {
        **build_base_options(
            include_publisher_list=[],
            include_abbr_list=[],
            exclude_publisher_list=["arXiv"],
            exclude_abbr_list=[],
            path_conf_j_jsons=path_conf_j_jsons,
        ),
        **build_search_options(
            print_on_screen=False, search_year_list=[], keywords_type=keywords_type, keywords_list_list=[]
        ),
    }

    # Download bibliography files from local search results
    download_bib = _download_bib_from_local(path_main_output, keywords_type)

    # Generate comparison output path and run comparison
    path_output = os.path.join(path_main_output, "Compared")
    compare_bibs_with_zotero(zotero_bib, download_bib, path_output, options)

    return None


def _generate_data_list(path_output: str, folder_name: str, keywords_type: str) -> list[str]:
    """Extract bibliography data content from files in specified folder structure.

    Args:
        path_output: Base output path for search results
        folder_name: Specific folder name within the output structure
        keywords_type: Category name for the search keywords used

    Returns:
        List of bibliography data content extracted from .bib files in the specified folders
    """
    data_list = []

    # Extract data from both title and abstract bibliography folders
    for bib_type in ["title-bib-zotero", "abstract-bib-zotero"]:
        folder_path = os.path.join(path_output, f"{folder_name}-Separate", "article", keywords_type, bib_type)

        # Extract bibliography data content if folder exists
        if os.path.exists(folder_path):
            data_list.extend(transform_to_data_list(folder_path, ".bib"))

    return data_list


def _download_bib_from_local(path_output: str, keywords_type: str) -> list[str]:
    """Collect bibliography data content from all local search result directories.

    Args:
        path_output: Base output path containing search results
        keywords_type: Category name for the search keywords used

    Returns:
        Combined list of bibliography data content from all .bib files in search results
    """
    data_list = []

    # Collect data from spidered bibliographies (Conferences and Journals)
    for cj in ["Conferences", "Journals"]:
        folder_name = os.path.join("Search_spidered_bib", cj)
        data_list.extend(_generate_data_list(path_output, folder_name, keywords_type))

    # Collect data from spidering bibliographies (journal sources)
    for je in ["spider_j", "spider_j_e"]:
        folder_name = os.path.join("Search_spidering_bib", je)
        data_list.extend(_generate_data_list(path_output, folder_name, keywords_type))

    return data_list
