import os

import sublime
import sublime_plugin
from pyadvtools import IterateUpdateDict

from pyeasyphd.tools.py_run_bib_md_tex import PyRunBibMdTex


def delete_files(path_storage: str, extensions) -> None:
    """Delete files with specified extensions from storage path.

    Args:
        path_storage (str): Path to the storage directory.
        extensions: list of file extensions to delete.
    """
    for name in os.listdir(path_storage):
        for ext in extensions:
            if name.endswith(ext) and os.path.isfile(os.path.join(path_storage, name)):
                os.remove(os.path.join(path_storage, name))


class PypapersCommand(sublime_plugin.WindowCommand):
    """Sublime Text command for processing papers with various templates."""

    def run(self, template="Paper", output_level="next", delete_cache=False):
        """Run the paper processing command.

        Args:
            template (str, optional): Template type to use. Defaults to "Paper".
            output_level (str, optional): Output level for processing. Defaults to "next".
            delete_cache (bool, optional): Whether to delete cache files. Defaults to False.
        """
        vars_dict = self.window.extract_variables()

        packages_path = vars_dict["packages"]

        # settings
        options, default_settings, user_settings, project_settings = {}, {}, {}, {}
        file_default_settings = os.path.join(packages_path, "pypapers", "pypapers.sublime-settings")
        if os.path.exists(file_default_settings):
            default_settings = sublime.decode_value(open(file_default_settings).read())

        file_user_settings = os.path.join(packages_path, "User", "PyPapers.sublime-settings")
        if os.path.exists(file_user_settings):
            user_settings = sublime.decode_value(open(file_user_settings).read())

        project_settings = self.window.project_data().get("settings", {})

        iter_update_dict = IterateUpdateDict()
        options = iter_update_dict.dict_update(options, default_settings)
        options = iter_update_dict.dict_update(options, user_settings)
        options = iter_update_dict.dict_update(options, project_settings)

        # update
        for key in vars_dict:
            if isinstance(vars_dict[key], str):
                os.environ[key] = vars_dict[key]

        for key in options:
            if isinstance(options[key], str):
                options[key] = os.path.expandvars(os.path.expanduser(options[key]))

        if delete_cache:
            file_path = vars_dict["file_path"]

            if latex_clean_file_types := options.get("latex_clean_file_types", []):
                postfix = latex_clean_file_types
            else:
                postfix = [".aux", ".bbl", ".bcf", ".blg", ".fdb_latexmk", ".fls", ".log", ".out", ".run.xml"]
                postfix.extend([".synctex.gz", ".gz", ".nav", ".snm", ".toc", ".xdv"])

            delete_files(file_path, postfix)
            delete_files(os.path.dirname(file_path), postfix)

        else:
            # main
            path_output = options.get("path_output", "")
            if len(path_output.strip()) == 0:
                path_output = vars_dict["file_path"]

            p_r_l_m = PyRunBibMdTex(path_output, vars_dict["file_extension"], template, options)
            p_r_l_m.run_files([vars_dict["file"]], vars_dict["file_base_name"], output_level)

        # display
        self.window.status_message("Successful.")
