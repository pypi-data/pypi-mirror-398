from local_config import local_options

from pyeasyphd.scripts import run_format_bib_to_abbr_zotero_save

if __name__ == "__main__":
    path_output = local_options["path_output"]
    path_conf_j_jsons = local_options["path_conf_j_jsons"]

    options = {"generate_entry_cite_keys": True, "default_additional_field_list": []}
    need_format_bib = "/path/to/need_format.bib"

    run_format_bib_to_abbr_zotero_save(options, need_format_bib, path_output, path_conf_j_jsons)
