from local_config import local_options

from pyeasyphd.scripts import (
    run_generate_j_e_weekly,
    run_generate_j_monthly,
    run_generate_j_weekly,
    run_generate_j_yearly,
)

if __name__ == "__main__":
    options = {
        "include_publisher_list": [],
        "include_abbr_list": [],
        "exclude_publisher_list": ["arXiv"],
        "exclude_abbr_list": [],
    }

    path_weekly_docs = local_options["path_weekly_docs"]
    path_monthly_docs = local_options["path_monthly_docs"]
    path_yearly_docs = local_options["path_yearly_docs"]
    keywords_category_names = ["", "S", "Y"]
    path_spidered_bibs = local_options["path_spidered_bibs"]
    path_spidering_bibs = local_options["path_spidering_bibs"]
    path_conf_j_jsons = local_options["path_conf_j_jsons"]

    # for IEEE Early Access
    run_generate_j_e_weekly(options, path_weekly_docs, keywords_category_names, path_spidering_bibs, path_conf_j_jsons)

    # for weekly papers
    run_generate_j_weekly(options, path_weekly_docs, keywords_category_names, path_spidering_bibs, path_conf_j_jsons)

    # for monthly papers
    run_generate_j_monthly(options, path_monthly_docs, keywords_category_names, path_spidering_bibs, path_conf_j_jsons)

    # for yearly papers
    year_list = []
    run_generate_j_yearly(
        options, path_yearly_docs, keywords_category_names, path_spidered_bibs, path_conf_j_jsons, year_list
    )
