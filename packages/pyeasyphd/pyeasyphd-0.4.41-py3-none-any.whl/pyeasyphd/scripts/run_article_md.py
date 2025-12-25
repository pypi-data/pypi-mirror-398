import os

from pyeasyphd.tools import PyRunBibMdTex

from ._base import expand_path


def run_article_md_daily_notes(
    path_input_file: str,
    input_file_names: list[str],
    path_output_file: str,
    bib_path_or_file: str,
    path_conf_j_jsons: str,
    options: dict,
) -> None:
    """Run article markdown daily notes processing pipeline.

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
        "shutil_includegraphics_figs": False,
        "includegraphics_figs_in_relative_path": True,
        "figure_folder_name": "figs",  # "" or "figs" or "main"
        # bib options
        "is_standardize_bib": False,  # default is True
        "function_common_again": False,  # default is True
        "abbr_index_article_for_abbr": 1,  # 0, 1, 2
        "abbr_index_inproceedings_for_abbr": 2,  # 0, 1, 2
        "add_link_to_fields_for_abbr": ["title"],  # None, or ["title", "journal", "booktitle"]
        "maximum_authors_for_abbr": 0,  # 0, 1, 2, ...
        "add_index_to_entries": False,
        "bib_name_for_abbr": "abbr.bib",
        "bib_name_for_zotero": "zotero.bib",
        "bib_name_for_save": "save.bib",
        "bib_folder_name": "bibs",  # "" or "bib" or "bibs" or "main"
        "delete_original_bib_in_output_folder": True,  # default is False
        "bib_path_or_file": expand_path(bib_path_or_file),
        # tex options
        "handly_preamble": False,
        "final_output_main_tex_name": "main.tex",
        "run_latex": False,
        "delete_run_latex_cache": False,
        "input_texs_directory": "",
        "shutil_input_texs": False,  # True or False
        "input_texs_in_relative_path": True,
        "tex_folder_name": "texs",  # "" or "tex" or "texs" or "main"
        "delete_original_tex_in_output_folder": True,  # default is False
        "generate_tex": False,
        # md options
        # ["www", "google", "connected", "scite"]
        "display_www_google_connected_scite": ["google", "connected"],  # python_writers.py
        "join_flag_in_http": " | ",  # default is " | " or " |\n"
        "add_url_for_basic_dict": False,  # default is True
        "add_anchor_for_basic_dict": True,  # default is False
        "add_anchor_for_beauty_dict": False,  # default is False
        "add_anchor_for_complex_dict": False,  # default is False
        "details_to_bib_separator": "\n\n",  # defulat is "\n"
        "final_output_main_md_name": "main.md",
        "delete_temp_generate_md": True,
        "add_reference_in_md": True,
        "add_bib_in_md": False,
        "replace_cite_to_fullcite_in_md": True,
        "replace_by_basic_beauty_complex_in_md": "beauty",  # default is "basic"
        "display_basic_beauty_complex_references_in_md": "basic",  # default is "beauty"
        "add_anchor_in_md": True,  # default is False
        "md_folder_name": "mds",  # "" or "md" or "main"
        "delete_original_md_in_output_folder": True,  # default is False
        # html options
        "generate_html": False,
    }

    # Update with user-provided options
    _options.update(options)

    # Create full file paths from input file names
    file_list = [os.path.join(path_input_file, f) for f in input_file_names]

    # Generate output filenames based on input directory name (platform-independent)
    dir_name = os.path.basename(os.path.dirname(file_list[0]))
    _options.update({"final_output_main_tex_name": f"{dir_name}.tex", "final_output_main_md_name": f"{dir_name}.md"})

    PyRunBibMdTex(path_output_file, ".md", "paper", _options).run_files(file_list, "", "current")

    return None
