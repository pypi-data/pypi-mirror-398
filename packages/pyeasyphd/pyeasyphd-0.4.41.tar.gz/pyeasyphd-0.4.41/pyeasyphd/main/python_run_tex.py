import os
import re
import shutil
import subprocess
from typing import Any

from pyadvtools import delete_files, insert_list_in_list, read_list, write_list

from .basic_input import BasicInput


class PythonRunTex(BasicInput):
    """Python LaTeX document processing and compilation class.

    This class extends BasicInput to handle LaTeX-specific operations including
    document compilation, output management, and temporary file cleanup.
    It supports multiple LaTeX engines and provides configurable cleanup options.

    Args:
        options (dict[str, Any]): Configuration options for LaTeX processing.

    Attributes:
        final_output_main_tex_name (str): Name of the main output LaTeX file.
            Defaults to empty string.
        run_latex (bool): Flag indicating whether to execute LaTeX compilation.
            When True, the system will compile the LaTeX document. Defaults to False.
        pdflatex_xelatex (str): LaTeX engine selection. Valid options are
            'pdflatex' for standard PDF compilation or 'xelatex' for extended
            Unicode and font support. Defaults to "xelatex".
        delete_run_latex_cache (bool): Flag controlling cleanup of temporary
            LaTeX files after compilation. When True, auxiliary files are removed.
            Defaults to True.
        latex_clean_file_types (list[str] | None): List of file extensions to
            remove during cleanup. If None, a default set is used. Defaults to None.
        replace_duplicate_output_tex_file (bool): Flag indicating whether to
            overwrite existing output files with the same name. When True,
            duplicates are replaced; when False, new names may be generated.
            Defaults to False.
    """

    def __init__(self, options: dict[str, Any]) -> None:
        """Initialize PythonRunTex with configuration options.

        Args:
            options (dict[str, Any]): Configuration options.
        """
        super().__init__(options)

        # for tex
        self.final_output_main_tex_name: str = options.get("final_output_main_tex_name", "")
        self.run_latex: bool = options.get("run_latex", False)
        self.pdflatex_xelatex: str = options.get("pdflatex_xelatex", "xelatex")  # pdflatex, xelatex
        self.delete_run_latex_cache: bool = options.get("delete_run_latex_cache", True)
        self.latex_clean_file_types: list[str] | None = options.get("latex_clean_file_types", None)
        self.replace_duplicate_output_tex_file: bool = options.get("replace_duplicate_output_tex_file", False)

    def generate_standard_tex_data_list(
        self,
        data_list_body: list[str],
        output_tex_name: str,
        path_output: str,
        figure_folder_name: str = "figs",
        tex_folder_name: str = "tex",
        bib_folder_name: str = "bib",
        bib_name: str = "abbr.bib",
        template_name: str = "article",
    ) -> list[str]:
        """Generate standard LaTeX data list with proper formatting.

        Args:
            data_list_body (list[str]): list of body content strings.
            output_tex_name (str): Name of output LaTeX file.
            path_output (str): Path to output directory.
            figure_folder_name (str): Name of figures folder. Defaults to "figs".
            tex_folder_name (str): Name of LaTeX folder. Defaults to "tex".
            bib_folder_name (str): Name of bibliography folder. Defaults to "bib".
            bib_name (str): Name of bibliography file. Defaults to "abbr.bib".
            template_name (str): Name of template to use. Defaults to "article".

        Returns:
            list[str]: list of processed LaTeX content strings.
        """
        # for figures
        for i in range(len(data_list_body)):
            if re.search(r"\\includegraphics", data_list_body[i]):
                data_list_body[i] = data_list_body[i].replace(
                    f".{os.sep}Figures{os.sep}", f".{os.sep}{figure_folder_name}{os.sep}"
                )
                data_list_body[i] = data_list_body[i].replace(f"Figures{os.sep}", f"{figure_folder_name}{os.sep}")
        write_list(data_list_body, output_tex_name, "w", os.path.join(path_output, tex_folder_name), False)

        self._special_operate_tex(
            data_list_body, template_name, output_tex_name, path_output, tex_folder_name, bib_folder_name, bib_name
        )
        return data_list_body

    def _special_operate_tex(
        self,
        data_list_body: list[str],
        template_name: str,
        output_tex_name: str,
        path_output: str,
        tex_folder_name: str,
        bib_folder_name: str,
        bib_name: str,
    ) -> None:
        """Perform special operations on LaTeX files.

        Args:
            data_list_body (list[str]): list of body content strings.
            template_name (str): Name of template to use.
            output_tex_name (str): Name of output LaTeX file.
            path_output (str): Path to output directory.
            tex_folder_name (str): Name of LaTeX folder.
            bib_folder_name (str): Name of bibliography folder.
            bib_name (str): Name of bibliography file.
        """
        # read template data
        template_h, template_t = [], []
        if template_name.lower() == "paper":
            template_h, template_t = self.article_template_header_tex, self.article_template_tail_tex
        elif template_name.lower() == "beamer":
            template_h, template_t = self.beamer_template_header_tex, self.beamer_template_tail_tex

        # style
        if usepackages := self.usepackages_tex:
            usepackages.insert(0, "\n")

        # command
        if math_commands := self.math_commands_tex:
            math_commands.insert(0, "\n")

        # main name
        main_name = self.final_output_main_tex_name
        if len(main_name) == 0:
            main_name = output_tex_name.split(".text")[0] + "_main.tex"
        if (not self.replace_duplicate_output_tex_file) and (main_name.lower() == output_tex_name.lower()):
            main_name = main_name.split(".tex")[0] + "_.tex"
        if main_name[-4:] != ".tex":
            main_name = main_name + ".tex"

        data_list = []
        if (len(template_h) != 0) and (len(template_t) != 0):
            # header
            data_list = insert_list_in_list(template_h, usepackages, r"\\documentclass", "after")
            data_list = insert_list_in_list(data_list, math_commands, r"\\documentclass", "after")

            if template_name.lower() == "beamer":
                data_list = insert_list_in_list(data_list, ["\n\\def\\allfiles{}\n"], r"\\documentclass", "after")

            if self.pdflatex_xelatex == "xelatex":
                data_list = insert_list_in_list(data_list, ["\n\\def\\cn{}\n"], r"\\documentclass", "after")

            # for bib
            expected = r'\addbibresource{./bibs/abbr.bib}'
            for i in range(len(data_list)):
                mch = expected == data_list[i].rstrip()
                if not mch:
                    continue
                if bib_folder_name:
                    data_list[i] = "\\addbibresource{" + f"./{bib_folder_name}/{bib_name}" + "}\n"
                else:
                    data_list[i] = "\\addbibresource{" + f"./{bib_name}" + "}\n"

            # body
            if len(data_list_body) != 0:
                data_list.append("\n")
                data_list.extend(data_list_body)
                data_list.append("\n")

            # tail
            data_list.extend(template_t)

            # save file
            write_list(data_list, main_name, "w", path_output, False)
        else:
            data_list = read_list(output_tex_name, "r", os.path.join(path_output, tex_folder_name))
            write_list(data_list, main_name, "w", path_output, False)

        # run latex
        if self.run_latex:
            if shutil.which("latexmk"):
                os.chdir(path_output)
                cmd = f"latexmk -{self.pdflatex_xelatex} {main_name}"
                try:
                    subprocess.run(cmd.split(), check=True, capture_output=True, text=True)
                except subprocess.CalledProcessError as e:
                    print("Error in Run LaTex:", e.stderr)
            else:
                print("latexmk not found. Please install Texlive.")

        # delete cache
        if self.delete_run_latex_cache:
            if self.latex_clean_file_types is not None:
                postfix = self.latex_clean_file_types
            else:
                postfix = [".aux", ".bbl", ".bcf", ".blg", ".fdb_latexmk", ".fls", ".log", ".out", ".run.xml"]
                postfix.extend([".synctex.gz", ".gz", ".nav", ".snm", ".toc", ".xdv"])
            delete_files(path_output, postfix)
        return None
