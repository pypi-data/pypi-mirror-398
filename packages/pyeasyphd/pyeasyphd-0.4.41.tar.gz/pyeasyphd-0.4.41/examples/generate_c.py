from local_config import local_options

from pyeasyphd.scripts import run_generate_c_yearly

if __name__ == "__main__":
    options = {
        "include_publisher_list": [],
        "include_abbr_list": [],
        "exclude_publisher_list": ["arXiv"],
        "exclude_abbr_list": [],
    }

    path_yearly_docs = local_options["path_yearly_docs"]
    keywords_category_names = ["", "S", "Y"]
    path_spidered_bibs = local_options["path_spidered_bibs"]
    path_conf_j_jsons = local_options["path_conf_j_jsons"]
    year_list = []

    run_generate_c_yearly(
        options, path_yearly_docs, keywords_category_names, path_spidered_bibs, path_conf_j_jsons, year_list
    )
