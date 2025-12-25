import os


def update_path(path_input: str):
    return os.path.expandvars(os.path.expanduser(path_input))


local_options = {
    "path_spidered_bibs": update_path(""),
    "path_spidering_bibs": update_path(""),
    "path_conf_j_jsons": update_path(""),
    "path_output": update_path(""),
    "zotero_bib": update_path(""),  # "BibTex.bib" exported from Zotero
    "path_weekly_docs": update_path(""),
    "path_monthly_docs": update_path(""),
    "path_yearly_docs": update_path(""),
}
