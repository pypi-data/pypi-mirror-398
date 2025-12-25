from pyeasyphd.scripts.run_article_md import run_article_md_daily_notes

if __name__ == "__main__":
    path_json = ""
    zotero_bib = ""
    path_input_file = ""
    path_output_file = ""
    options = {}

    mcmc_filenames = ["MCMC/Introduction.md", "MCMC/Algorithms.md", "MCMC/Metrics.md", "MCMC/Applications.md"]

    for filenames in [mcmc_filenames]:
        run_article_md_daily_notes(path_input_file, filenames, path_output_file, zotero_bib, path_json, options)
