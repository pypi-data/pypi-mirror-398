import os

from local_config import local_options

from pyeasyphd.scripts import run_compare_bib_with_local, run_format_bib_to_abbr_zotero_save

if __name__ == "__main__":
    path_output = local_options["path_output"]
    path_spidered_bibs = local_options["path_spidered_bibs"]
    path_spidering_bibs = local_options["path_spidering_bibs"]
    path_conf_j_jsons = local_options["path_conf_j_jsons"]

    options = {
        "include_publisher_list": [],
        "include_abbr_list": [],
        "exclude_publisher_list": ["arXiv"],
        "exclude_abbr_list": [],
        "compare_each_entry_with_all_local_bibs": False,
    }
    need_compare_bib = "/path/to/need_compare.bib"

    run_compare_bib_with_local(
        options, need_compare_bib, path_output, path_spidered_bibs, path_spidering_bibs, path_conf_j_jsons
    )

    name = "in_local_entries"
    options.update(
        {
            "bib_name_for_abbr": f"{name}_abbr.bib",
            "bib_name_for_zotero": f"{name}_zotero.bib",
            "bib_name_for_save": f"{name}_save.bib",
        }
    )
    run_format_bib_to_abbr_zotero_save(
        options, os.path.join(path_output, f"{name}.bib"), path_output, path_conf_j_jsons
    )
