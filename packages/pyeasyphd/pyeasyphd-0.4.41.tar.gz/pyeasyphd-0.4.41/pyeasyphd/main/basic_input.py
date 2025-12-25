import os
from typing import Any

from pyadvtools import read_list
from pybibtexer.main import BasicInput as BasicInputInPyBibtexer


class BasicInput(BasicInputInPyBibtexer):
    """Basic input class for handling bibliography and template configurations.

    Args:
        options (dict[str, Any]): Configuration options.

    Attributes:
        full_csl_style_pandoc (str): Full path to CSL style for pandoc.
        full_tex_article_template_pandoc (str): Full path to tex article template for pandoc.
        full_tex_beamer_template_pandoc (str): Full path to tex beamer template for pandoc.
        article_template_tex (list[str]): Article template for LaTeX.
        article_template_header_tex (list[str]): Article template header for LaTeX.
        article_template_tail_tex (list[str]): Article template tail for LaTeX.
        beamer_template_header_tex (list[str]): Beamer template header for LaTeX.
        beamer_template_tail_tex (list[str]): Beamer template tail for LaTeX.
        math_commands_tex (list[str]): LaTeX math commands.
        usepackages_tex (list[str]): LaTeX usepackages.
        handly_preamble (bool): Whether to handle preamble manually.
        options (dict[str, Any]): Configuration options.
    """

    def __init__(self, options: dict[str, Any]) -> None:
        """Initialize BasicInput with configuration options.

        Args:
            options (dict[str, Any]): Configuration options dictionary.
        """
        super().__init__(options)

        current_dir = os.path.dirname(os.path.abspath(__file__))
        self._path_templates = os.path.join(os.path.dirname(current_dir), "data", "templates")

        # main
        self._initialize_pandoc_md_to(options)
        self._initialize_python_run_tex(options)

        self.options = options

    def _initialize_pandoc_md_to(self, options: dict[str, Any]) -> None:
        """Initialize pandoc markdown to other formats configuration.

        Args:
            options (dict[str, Any]): Configuration options.
        """
        csl_name = options.get("csl_name", "apa-no-ampersand")
        if not isinstance(csl_name, str):
            csl_name = "apa-no-ampersand"
        self.full_csl_style_pandoc = os.path.join(self._path_templates, "csl", f"{csl_name}.csl")
        if not os.path.exists(self.full_csl_style_pandoc):
            self.full_csl_style_pandoc = os.path.join(self._path_templates, "csl", "apa-no-ampersand.csl")

        self.full_tex_article_template_pandoc = os.path.join(self._path_templates, "tex", "eisvogel.latex")
        self.full_tex_beamer_template_pandoc = os.path.join(self._path_templates, "tex", "eisvogel.beamer")

        self.article_template_tex = self._try_read_list("tex", "Article.tex")

    def _initialize_python_run_tex(self, options: dict[str, Any]) -> None:
        """Initialize Python LaTeX processing configuration.

        Args:
            options (dict[str, Any]): Configuration options.
        """
        self.article_template_header_tex = self._try_read_list("tex", "Article_Header.tex")
        self.article_template_tail_tex = self._try_read_list("tex", "Article_Tail.tex")
        self.beamer_template_header_tex = self._try_read_list("tex", "Beamer_Header.tex")
        self.beamer_template_tail_tex = self._try_read_list("tex", "Beamer_Tail.tex")
        self.math_commands_tex = self._try_read_list("tex", "math_commands.tex")
        self.usepackages_tex = self._try_read_list("tex", "Style.tex")

        # handly preamble
        self.handly_preamble = options.get("handly_preamble", False)
        if self.handly_preamble:
            self.article_template_header_tex, self.article_template_tail_tex = [], []
            self.beamer_template_header_tex, self.beamer_template_tail_tex = [], []
            self.math_commands_tex, self.usepackages_tex = [], []

    def _try_read_list(self, folder_name: str, file_name: str):
        """Try to read a list from a file in the templates directory.

        Args:
            folder_name (str): Name of the folder in templates directory.
            file_name (str): Name of the file to read.

        Returns:
            list[str]: list of lines from the file, or empty list if file cannot be read.
        """
        path_file = os.path.join(self._path_templates, folder_name, file_name)

        try:
            data_list = read_list(path_file)
        except Exception as e:
            print(e)
            data_list = []
        return data_list
