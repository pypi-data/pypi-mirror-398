from local_config import local_options

from pyeasyphd.scripts import run_replace_to_standard_cite_keys

if __name__ == "__main__":
    path_output = local_options["path_output"]
    path_conf_j_jsons = local_options["path_conf_j_jsons"]

    options = {}

    full_md = "/path/to/full.md"
    full_bib = "/path/to/full.bib"
    run_replace_to_standard_cite_keys(full_md, full_bib, path_output, path_conf_j_jsons, options)
