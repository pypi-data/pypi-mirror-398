import os

from pyeasyphd.tools import PaperLinksGenerator, generate_from_bibs_and_write
from pyeasyphd.utils.utils import is_last_week_of_month

from ._base import build_base_options, expand_paths


def run_generate_j_weekly(
    options: dict,
    path_weekly_docs: str,
    keywords_category_names: list[str],
    path_spidering_bibs: str,
    path_conf_j_jsons: str,
):
    # Expand and normalize file paths
    path_weekly_docs, path_spidering_bibs = expand_paths(path_weekly_docs, path_spidering_bibs)

    # Update options
    options_ = build_base_options([], [], ["arXiv"], [], path_conf_j_jsons)
    options_.update(options)

    # Generate md and html files
    for gc in ["generate_data", "combine_data"]:
        path_storage = os.path.join(path_spidering_bibs, "spider_j")
        output_basename = os.path.join("data", "Weekly")
        path_output = os.path.expanduser(os.path.join(path_weekly_docs, output_basename, "Journals"))
        # "current_issue", "current_month"
        for flag in ["current_issue", "current_month"]:
            generate_from_bibs_and_write(
                path_storage, path_output, output_basename, "Journals", gc, "current_year", flag, options_
            )

    # Generate links
    for keywords_category_name in keywords_category_names:
        full_json_c, full_json_j, full_json_k = (
            options_["full_json_c"],
            options_["full_json_j"],
            options_["full_json_k"],
        )
        output_basename = os.path.join("data", "Weekly")
        generator = PaperLinksGenerator(full_json_c, full_json_j, full_json_k, path_weekly_docs, keywords_category_name)
        generator.generate_weekly_links(output_basename)
        generator.generate_keywords_links_weekly("Journals", output_basename)


def run_generate_j_e_weekly(
    options: dict,
    path_weekly_docs: str,
    keywords_category_names: list[str],
    path_spidering_bibs: str,
    path_conf_j_jsons: str,
):
    # Expand and normalize file paths
    path_weekly_docs, path_spidering_bibs = expand_paths(path_weekly_docs, path_spidering_bibs)

    # Update options
    options_ = build_base_options([], [], ["arXiv"], [], path_conf_j_jsons)
    options_.update(options)
    options_["early_access"] = True

    # Generate md and html files
    for gc in ["generate_data", "combine_data"]:
        path_storage = os.path.join(path_spidering_bibs, "spider_j_e")
        output_basename = os.path.join("data", "Weekly")
        path_output = os.path.expanduser(os.path.join(path_weekly_docs, output_basename, "Journals"))
        # "current_month"
        for flag in ["current_month"]:
            generate_from_bibs_and_write(
                path_storage, path_output, output_basename, "Journals", gc, "current_year", flag, options_
            )

        # "all_years"
        for year in ["all_years"]:
            generate_from_bibs_and_write(
                path_storage, path_output, output_basename, "Journals", gc, year, "all_months", options_
            )

    # Generate links
    for keywords_category_name in keywords_category_names:
        full_json_c, full_json_j, full_json_k = (
            options_["full_json_c"],
            options_["full_json_j"],
            options_["full_json_k"],
        )
        output_basename = os.path.join("data", "Weekly")
        generator = PaperLinksGenerator(full_json_c, full_json_j, full_json_k, path_weekly_docs, keywords_category_name)
        generator.generate_ieee_early_access_links(output_basename)
        generator.generate_keywords_links_weekly("Journals", output_basename)


def run_generate_j_monthly(
    options: dict,
    path_monthly_docs: str,
    keywords_category_names: list[str],
    path_spidering_bibs: str,
    path_conf_j_jsons: str,
):
    # Expand and normalize file paths
    path_monthly_docs, path_spidering_bibs = expand_paths(path_monthly_docs, path_spidering_bibs)

    # Update options
    options_ = build_base_options([], [], ["arXiv"], [], path_conf_j_jsons)
    options_.update(options)

    # Generate md and html files
    for gc in ["generate_data", "combine_data"]:
        path_storage = os.path.join(path_spidering_bibs, "spider_j")
        output_basename = os.path.join("data", "Monthly")
        path_output = os.path.expanduser(os.path.join(path_monthly_docs, output_basename, "Journals"))
        # "all_months"
        for flag in ["all_months"]:
            if flag == "all_months":
                if not is_last_week_of_month():
                    continue

            generate_from_bibs_and_write(
                path_storage, path_output, output_basename, "Journals", gc, "current_year", flag, options_
            )

    # Generate links
    for keywords_category_name in keywords_category_names:
        full_json_c, full_json_j, full_json_k = (
            options_["full_json_c"],
            options_["full_json_j"],
            options_["full_json_k"],
        )
        output_basename = os.path.join("data", "Monthly")
        generator = PaperLinksGenerator(
            full_json_c, full_json_j, full_json_k, path_monthly_docs, keywords_category_name
        )
        generator.generate_monthly_links(output_basename)
        generator.generate_keywords_links_monthly("Journals", output_basename)


def run_generate_j_yearly(
    options: dict,
    path_yearly_docs: str,
    keywords_category_names: list[str],
    path_spidered_bibs: str,
    path_conf_j_jsons: str,
    year_list: list[str],
):
    # Expand and normalize file paths
    path_yearly_docs, path_spidered_bibs = expand_paths(path_yearly_docs, path_spidered_bibs)

    # Update options
    options_ = build_base_options([], [], ["arXiv"], [], path_conf_j_jsons)
    options_.update(options)

    # Generate md and html files
    for gc in ["generate_data", "combine_data"]:
        path_storage = os.path.join(path_spidered_bibs, "Journals")
        output_basename = os.path.join("data", "Yearly")
        path_output = os.path.expanduser(os.path.join(path_yearly_docs, output_basename, "Journals"))
        # "2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016", "2015"
        for year in year_list:
            generate_from_bibs_and_write(
                path_storage, path_output, output_basename, "Journals", gc, [year], "all_months", options_
            )

    # Generate links
    for keywords_category_name in keywords_category_names:
        full_json_c, full_json_j, full_json_k = (
            options_["full_json_c"],
            options_["full_json_j"],
            options_["full_json_k"],
        )
        output_basename = os.path.join("data", "Yearly")
        generator = PaperLinksGenerator(full_json_c, full_json_j, full_json_k, path_yearly_docs, keywords_category_name)
        generator.generate_yearly_links("Journals", output_basename)
        generator.generate_keywords_links_yearly("Journals", output_basename)


def run_generate_c_yearly(
    options: dict,
    path_yearly_docs: str,
    keywords_category_names: list[str],
    path_spidered_bibs: str,
    path_conf_j_jsons: str,
    year_list: list[str],
):
    # Expand and normalize file paths
    path_yearly_docs, path_spidered_bibs = expand_paths(path_yearly_docs, path_spidered_bibs)

    # Update options
    options_ = build_base_options([], [], ["arXiv"], [], path_conf_j_jsons)
    options_.update(options)

    # Generate md and html files
    for gc in ["generate_data", "combine_data"]:
        path_storage = os.path.join(path_spidered_bibs, "Conferences")
        output_basename = os.path.join("data", "Yearly")
        path_output = os.path.expanduser(os.path.join(path_yearly_docs, output_basename, "Conferences"))
        # "2025", "2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016", "2015"
        for year in year_list:
            generate_from_bibs_and_write(
                path_storage, path_output, output_basename, "Conferences", gc, [year], "all_months", options_
            )

    # Generate links
    for keywords_category_name in keywords_category_names:
        full_json_c, full_json_j, full_json_k = (
            options_["full_json_c"],
            options_["full_json_j"],
            options_["full_json_k"],
        )
        output_basename = os.path.join("data", "Yearly")
        generator = PaperLinksGenerator(full_json_c, full_json_j, full_json_k, path_yearly_docs, keywords_category_name)
        generator.generate_yearly_links("Conferences", output_basename)
        generator.generate_keywords_links_yearly("Conferences", output_basename)
