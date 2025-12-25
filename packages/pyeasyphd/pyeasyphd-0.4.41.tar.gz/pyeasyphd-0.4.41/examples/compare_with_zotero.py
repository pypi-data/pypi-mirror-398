from local_config import local_options

from pyeasyphd.scripts import run_compare_bib_with_zotero

if __name__ == "__main__":
    zotero_bib = local_options["zotero_bib"]
    path_output = local_options["path_output"]
    path_conf_j_jsons = local_options["path_conf_j_jsons"]

    options = {}
    need_compare_bib = "/path/to/need_compare.bib"

    run_compare_bib_with_zotero(options, need_compare_bib, zotero_bib, path_output, path_conf_j_jsons)
