import os

from pyadvtools import GitAutoCommitter

from pyeasyphd.tools import PyRunBibMdTex

from ._base import expand_path


def run_article_tex_submit(
    path_input_file: str,
    input_file_names: list[str],
    path_output_file: str,
    bib_path_or_file: str,
    path_conf_j_jsons: str,
    options: dict,
    auto_git: bool = False,
    remote: str = "origin",
    branch: str = "master",
) -> None:
    """Process academic article files (TeX, and bibliography) with automated Git version control.

    This function handles the conversion and processing of academic article files including TeX documents, and
    bibliography management with automatic Git commit and push capabilities.

    Note: The raw figures and TeX source files must be located in the data/raw subdirectory of the input path.

    Args:
        path_input_file (str): Path to input files directory
        input_file_names (list[str]): list of input file names
        path_output_file (str): Path to output directory
        bib_path_or_file (str): Path to bibliography file or directory
        path_conf_j_jsons (str): Path to conferences and journals JSON files directory
        options (dict): Additional options to override default settings

    Returns:
        None
    """
    path_input_file = expand_path(path_input_file)
    path_output_file = expand_path(path_output_file)

    # Initialize default options with detailed descriptions
    _options = {
        "full_json_c": expand_path(os.path.join(path_conf_j_jsons, "conferences.json")),
        "full_json_j": expand_path(os.path.join(path_conf_j_jsons, "journals.json")),
        # figure options
        "includegraphics_figs_directory": "",
        "shutil_includegraphics_figs": True,
        "includegraphics_figs_in_relative_path": False,  # default is True
        "figure_folder_name": "figs",  # "" or "figs" or "main"
        # bib options
        "is_standardize_bib": False,  # default is True
        "function_common_again": False,  # default is True
        "abbr_index_article_for_abbr": 1,  # 0, 1, 2
        "abbr_index_inproceedings_for_abbr": 0,  # 0, 1, 2
        "add_link_to_fields_for_abbr": None,  # None, or ["title", "journal", "booktitle"]
        "maximum_authors_for_abbr": 0,  # 0, 1, 2, ...
        "add_index_to_entries": False,
        "bib_name_for_abbr": "abbr.bib",
        "bib_name_for_zotero": "zotero.bib",
        "bib_name_for_save": "save.bib",
        "bib_folder_name": "bibs",  # "" or "bib" or "bibs" or "main"
        "delete_original_bib_in_output_folder": False,
        "bib_path_or_file": expand_path(bib_path_or_file),
        # tex options
        "handly_preamble": True,
        "final_output_main_tex_name": "main.tex",
        "run_latex": False,
        "delete_run_latex_cache": False,
        "replace_duplicate_output_tex_file": True,  # default is False
        "input_texs_directory": "",
        "shutil_input_texs": True,
        "input_texs_in_relative_path": False,  # default is True
        "tex_folder_name": "texs",  # "" or "tex" or "texs" or "main"
        "delete_original_tex_in_output_folder": True,
        "generate_tex": True,
        # html options
        "generate_html": False,
    }

    # Update with user-provided options
    _options.update(options)

    # Create full file paths from input file names
    file_list = [os.path.join(path_input_file, f) for f in input_file_names]

    PyRunBibMdTex(path_output_file, ".tex", "paper", _options).run_files(file_list, "", "current")

    if auto_git:
        committer = GitAutoCommitter(path_output_file)
        committer.auto_commit()
        committer.auto_push(remote=remote, branch=branch)

    return None
