from local_config import local_options

from pyeasyphd.scripts import run_search_for_screen

if __name__ == "__main__":
    path_spidered_bibs = local_options["path_spidered_bibs"]
    path_spidering_bibs = local_options["path_spidering_bibs"]
    path_conf_j_jsons = local_options["path_conf_j_jsons"]

    acronym = "NeurIPS"
    year = 2017  # 0 means all years
    title = "Attention is all you need"

    run_search_for_screen(acronym, year, title, path_spidered_bibs, path_spidering_bibs, path_conf_j_jsons)
