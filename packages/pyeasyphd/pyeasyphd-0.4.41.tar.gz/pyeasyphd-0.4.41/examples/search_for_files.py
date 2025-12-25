import os

from local_config import local_options

from pyeasyphd.scripts import run_compare_after_search, run_format_bib_to_abbr_zotero_save, run_search_for_files

if __name__ == "__main__":
    path_main_output = local_options["path_output"]
    path_spidered_bibs = local_options["path_spidered_bibs"]
    path_spidering_bibs = local_options["path_spidering_bibs"]
    path_conf_j_jsons = local_options["path_conf_j_jsons"]
    zotero_bib = local_options["zotero_bib"]

    _h_ = "(?:| |-)"  # hyphen

    keywords_type = "Landscape Analysis"
    keywords_list_list = [
        [r"landscape(?:|s) analysis"],
        [r"fitness landscape(?:|s)"],
        [[r"landscape(?:|s)", "analysis"], [r"landscape(?:|s) analysis"]],
        [["fitness", r"landscape(?:|s)"], [r"fitness landscape(?:|s)"]],
        [[r"landscape(?:|s)"], ["analysis", "fitness"]],
    ]

    keywords_type = "DMOO"
    keywords_list_list = [
        [f"dynamic evolutionary multi{_h_}objective"],
        [f"dynamic multi{_h_}objective"],
        [f"dynamic evolutionary many{_h_}objective"],
        [f"dynamic many{_h_}objective"],
        [f"dynamic evolutionary constrained multi{_h_}objective"],
        [f"dynamic constrained multi{_h_}objective"],
        [f"dynamic evolutionary constrained many{_h_}objective"],
        [f"dynamic constrained many{_h_}objective"],
    ]

    keywords_type = "PS"
    keywords_list_list = [["reversible jump markov chain monte carlo"], ["reversible jump MCMC"]]

    # Configurations
    search_in_spidered_bibs = False
    search_in_spidering_bibs = True
    options = {
        "include_publisher_list": [],
        "include_abbr_list": [],
        "exclude_publisher_list": ["arXiv"],
        "exclude_abbr_list": [],
    }

    # search
    run_search_for_files(
        keywords_type,
        keywords_list_list,
        path_main_output,
        path_spidered_bibs,
        path_spidering_bibs,
        path_conf_j_jsons,
        search_in_spidered_bibs,
        search_in_spidered_bibs,
        options,
    )

    # compare
    run_compare_after_search(zotero_bib, keywords_type, path_main_output, path_conf_j_jsons)

    # format
    need_format_bib = os.path.join(path_main_output, "Compared", "only_in_download.bib")
    path_output = os.path.join(path_main_output, "Formatted")
    run_format_bib_to_abbr_zotero_save(options, need_format_bib, path_output, path_conf_j_jsons)
