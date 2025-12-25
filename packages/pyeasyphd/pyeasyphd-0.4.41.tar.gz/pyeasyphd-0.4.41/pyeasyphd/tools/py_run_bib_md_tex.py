import os
import re
import shutil
from typing import Any

from pyadvtools import combine_content_in_list, read_list, standard_path, write_list
from pybibtexer.bib.bibtexparser import Library
from pybibtexer.main import PythonRunBib, PythonWriters

from ..main import BasicInput, PythonRunMd, PythonRunTex


class PyRunBibMdTex(BasicInput):
    """A class for processing BibTeX, Markdown and LaTeX files with various operations.

    This class provides functionality to handle references, figures, and content conversion
    between Markdown and LaTeX formats.
    """

    def __init__(
        self,
        path_output: str,
        tex_md_flag: str = ".md",
        template_name: str = "paper",
        options: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the PyRunBibMdTex instance.

        Args:
            path_output (str): Output directory path for processed files.
            tex_md_flag (str, optional): Flag indicating whether to process as LaTeX (".tex") or Markdown (".md"). Defaults to ".md".
            template_name (str, optional): Template type to use ("paper" or "beamer"). Defaults to "paper".
            options (dict[str, Any], optional): Additional configuration options. Defaults to {}.

        Raises:
            AssertionError: If tex_md_flag is not ".tex" or ".md" or if template_name is not "paper" or "beamer".
        """
        if options is None:
            options = {}

        super().__init__(options)

        self.tex_md_flag = re.sub(r"\.+", ".", "." + tex_md_flag)
        assert self.tex_md_flag in [".tex", ".md"], f"{tex_md_flag} must be `.tex` or `.md`."
        self.template_name = template_name.lower()
        assert self.template_name in ["paper", "beamer"], f"{template_name} must be `paper` or `beamer`."
        self.path_output = standard_path(path_output)

        # Bib
        # Path to bibliographic data, can be either a directory path or a specific file path
        self.bib_path_or_file = options.get("bib_path_or_file", "")  # input

        # Figures \includegraphics{/path/to/example.png}
        # Path to the figures directory (must be a directory path, not a file)
        self.includegraphics_figs_directory = options.get("includegraphics_figs_directory", "")
        self.shutil_includegraphics_figs = options.get("shutil_includegraphics_figs", True)
        self.includegraphics_figs_in_relative_path = options.get("includegraphics_figs_in_relative_path", True)
        includegraphics_figs_postfixes = options.get("includegraphics_figs_postfixes")
        if includegraphics_figs_postfixes is None:
            includegraphics_figs_postfixes = ["eps", "jpg", "png", "svg", "psd", "raw", "jpeg", "pdf"]
        self.includegraphics_figs_postfixes = includegraphics_figs_postfixes

        # Texs (Texes) \input{/path/to/example.tex}
        self.input_texs_directory = options.get("input_texs_directory", "")
        self.shutil_input_texs = options.get("shutil_input_texs", True)
        self.input_texs_in_relative_path = options.get("input_texs_in_relative_path", True)
        input_texs_postfixes = options.get("input_texs_postfixes")
        if input_texs_postfixes is None:
            input_texs_postfixes = ["tex", "latex"]
        self.input_texs_postfixes = input_texs_postfixes

        # (output) Folder name configurations
        self.fig_folder_name = options.get("fig_folder_name", "figs")  # "" or "figs" or "main"
        self.bib_folder_name = options.get("bib_folder_name", "bibs")  # "" or "bibs" or "main"
        self.md_folder_name = options.get("md_folder_name", "mds")  # "" or "mds" or "main"
        self.tex_folder_name = options.get("tex_folder_name", "texs")  # "" or "texs" or "main"

        # Cleanup options
        self.delete_original_md_in_output_folder = options.get("delete_original_md_in_output_folder", False)
        self.delete_original_tex_in_output_folder = options.get("delete_original_tex_in_output_folder", False)
        self.delete_original_bib_in_output_folder = options.get("delete_original_bib_in_output_folder", False)

        # Configuration options
        self.generate_html = options.get("generate_html", False)
        self.generate_tex = options.get("generate_tex", True)

        # Initialize helper classes
        self._python_bib = PythonRunBib(self.options)
        self._python_writer = PythonWriters(self.options)

        self._python_md = PythonRunMd(self.options)
        self._python_tex = PythonRunTex(self.options)

    def run_files(
        self, file_list_md_tex: list[str], output_prefix: str = "", output_level: str = "next"
    ) -> tuple[list[str], list[str]]:
        """Process a list of Markdown or LaTeX files.

        Args:
            file_list_md_tex (list[str]): list of input file paths (Markdown or LaTeX).
            output_prefix (str, optional): Prefix for output files. Defaults to "".
            output_level (str, optional): Output directory level ("previous", "current", or "next"). Defaults to "next".

        Returns:
            tuple[list[str], list[str]]: Tuple containing processed Markdown content and LaTeX content.
        """
        file_list_md_tex = [f for f in file_list_md_tex if f.endswith(self.tex_md_flag)]
        data_list_list = [read_list(standard_path(f), "r") for f in file_list_md_tex]
        if all(len(data_list) == 0 for data_list in data_list_list):
            return [], []

        file_base_name = os.path.splitext(os.path.basename(file_list_md_tex[0]))[0]
        output_prefix = output_prefix if output_prefix else file_base_name

        data_list_md_tex = combine_content_in_list(data_list_list, ["\n"])

        content_md, content_tex = self.python_run_bib_md_tex(
            output_prefix, data_list_md_tex, self.bib_path_or_file, output_level
        )
        return content_md, content_tex

    def python_run_bib_md_tex(
        self,
        output_prefix: str,
        data_list_md_tex: list[str],
        original_bib_data: list[str] | str | Library,
        output_level: str = "next",
    ) -> tuple[list[str], list[str]]:
        """Process BibTeX, Markdown and LaTeX content.

        Args:
            output_prefix (str): Prefix for output files.
            data_list_md_tex (list[str]): list of content lines (Markdown or LaTeX).
            original_bib_data (list[str] | str | Library): BibTeX data in various formats.
            output_level (str, optional): Output directory level ("previous", "current", or "next"). Defaults to "next".

        Returns:
            tuple[list[str], list[str]]: Tuple containing processed Markdown content and LaTeX content.
        """
        # Basic file names
        output_tex, output_md = output_prefix + ".tex", output_prefix + ".md"

        if len(data_list_md_tex) == 0:
            original_bib_data = self._python_bib.parse_to_single_standard_library(original_bib_data)
            if not original_bib_data.entries:
                return [], []

            data_list_md_tex = []
            for entry in original_bib_data.entries:
                data_list_md_tex.append(f"- [@{entry.key}]\n\n")
            data_list_md_tex.insert(0, f"## {output_prefix} - {len(data_list_md_tex)}\n\n")

        # Determine output path based on level
        if output_level == "previous":
            path_output = os.path.dirname(self.path_output)
        elif output_level == "next":
            path_output = os.path.join(self.path_output, output_prefix)
        elif output_level == "current":
            path_output = self.path_output
        else:
            path_output = self.path_output

        if not os.path.exists(path_output):
            os.makedirs(path_output)
        self.path_output_new = standard_path(path_output)

        return self._python_run_bib_md_tex(output_md, output_tex, data_list_md_tex, original_bib_data)

    def _python_run_bib_md_tex(
        self,
        output_md: str,
        output_tex: str,
        data_list_md_tex: list[str],
        original_bib_data: list[str] | str | Library,
    ) -> tuple[list[str], list[str]]:
        """Process BibTeX, Markdown and LaTeX content.

        Args:
            output_md (str): Output Markdown filename.
            output_tex (str): Output LaTeX filename.
            data_list_md_tex (list[str]): list of content lines (Markdown or LaTeX).
            original_bib_data (list[str] | str | Library): BibTeX data in various formats.

        Returns:
            tuple[list[str], list[str]]: Tuple containing processed Markdown content and LaTeX content.
        """
        # Copy figures if enabled
        if self.shutil_includegraphics_figs:
            figure_names = self.search_subfile_names(data_list_md_tex, self.includegraphics_figs_postfixes)
            self.shutil_copy_files(
                self.includegraphics_figs_directory,
                figure_names,
                self.path_output_new,
                self.fig_folder_name,
                self.includegraphics_figs_in_relative_path,
            )

        # Copy input texs (texes) if enabled
        if self.shutil_input_texs:
            input_tex_names = self.search_subfile_names(data_list_md_tex, self.input_texs_postfixes)
            self.shutil_copy_files(
                self.input_texs_directory,
                input_tex_names,
                self.path_output_new,
                self.tex_folder_name,
                self.input_texs_in_relative_path,
            )

        # Extract citation keys from content
        key_in_md_tex = self.search_cite_keys(data_list_md_tex, self.tex_md_flag)

        # Process bibliography
        full_bib_for_zotero, full_bib_for_abbr, full_bib_for_save = "", "", ""
        if key_in_md_tex:
            # Generate bib contents
            abbr_library, zotero_library, save_library = self._python_bib.parse_to_multi_standard_library(
                original_bib_data, key_in_md_tex
            )

            # Only for existing references
            key_in_md_tex = sorted(abbr_library.entries_dict.keys(), key=key_in_md_tex.index)

            # Write bibliography files
            _path_output = os.path.join(self.path_output_new, self.bib_folder_name)
            full_bib_for_abbr, full_bib_for_zotero, full_bib_for_save = (
                self._python_writer.write_multi_library_to_multi_file(
                    _path_output, abbr_library, zotero_library, save_library, key_in_md_tex
                )
            )

        # Process content based on format
        if self.tex_md_flag == ".md":
            # Write original markdown content
            write_list(data_list_md_tex, output_md, "w", os.path.join(self.path_output_new, self.md_folder_name), False)

            # Generate processed content and write to given files
            data_list_md, data_list_tex = self._python_md.special_operate_for_md(
                self.path_output_new,
                data_list_md_tex,
                output_md,
                full_bib_for_abbr,
                full_bib_for_zotero,
                self.template_name,
                self.generate_html,
                self.generate_tex,
            )
        else:
            data_list_md, data_list_tex = [], data_list_md_tex

        # Generate LaTeX output if enabled
        if self.generate_tex:
            self._python_tex.generate_standard_tex_data_list(
                data_list_tex,
                output_tex,
                self.path_output_new,
                self.fig_folder_name,
                self.tex_folder_name,
                self.bib_folder_name,
                os.path.basename(full_bib_for_abbr),
                self.template_name,
            )

        # Cleanup original files if enabled
        if self.delete_original_md_in_output_folder:
            self._cleanup_file(os.path.join(self.path_output_new, self.md_folder_name, output_md))

        if self.delete_original_tex_in_output_folder:
            self._cleanup_file(os.path.join(self.path_output_new, self.tex_folder_name, output_tex))

        if self.delete_original_bib_in_output_folder:
            for file in [full_bib_for_abbr, full_bib_for_zotero, full_bib_for_save]:
                self._cleanup_file(file)

        return data_list_md, data_list_tex

    @staticmethod
    def search_subfile_names(data_list: list[str], postfixes: list[str]) -> list[str]:
        """Search for figure filenames in content.

        Args:
            data_list (list[str]): list of content lines to search.
            figure_postfixes (Optional[list[str]], optional): list of figure file extensions to look for. Defaults to None.

        Returns:
            list[str]: list of found figure filenames.
        """
        regex = re.compile(rf"[\w\-]+\.(?:{'|'.join(postfixes)})", re.I)
        figure_names = []
        for line in data_list:
            figure_names.extend(regex.findall(line))
        return sorted(set(figure_names), key=figure_names.index)

    @staticmethod
    def shutil_copy_files(
        path_file: str, file_names: list[str], path_output: str, output_folder_name: str, relative_path: bool
    ) -> None:
        """Copy specified files from source directory to output directory.

        Searches for files recursively in the source directory and copies them to
        the output location, preserving either relative paths or using a flat structure.

        Args:
            path_file: Source directory path to search for files.
            file_names: list of filenames to copy.
            path_output: Destination directory path.
            output_folder_name: Name of the subfolder in output directory (used when relative_path=False).
            relative_path: If True, preserves relative path structure; if False, uses flat structure.

        Returns:
            None: Function executes side effects (file copying) but returns nothing.
        """
        # Early return if no files or invalid source path
        if not file_names or not path_file:
            return None

        # Validate source directory exists
        if not os.path.exists(path_file):
            print(f"Source directory does not exist: {path_file}")
            return None

        # Recursively search for matching files
        file_list = []
        for root, _, files in os.walk(path_file, topdown=False):
            for name in files:
                if name in file_names:
                    file_list.append(os.path.join(root, name))

        # Report missing files
        found_files = [os.path.basename(f) for f in file_list]
        not_found = [f for f in file_names if f not in found_files]
        if not_found:
            print(f"Files not found: {', '.join(not_found)}")

        # Copy each found file to destination
        for file_path in file_list:
            if relative_path:
                # Preserve relative path structure
                path_output_file = file_path.replace(path_file, path_output)
            else:
                # Use flat structure in specified folder
                path_output_file = os.path.join(path_output, output_folder_name, os.path.basename(file_path))

            # Create destination directory if needed
            output_dir = os.path.dirname(path_output_file)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Perform file copy
            shutil.copy(file_path, path_output_file)
        return None

    @staticmethod
    def search_cite_keys(data_list: list[str], tex_md_flag: str = ".tex") -> list[str]:
        r"""Extract citation keys from content according to their places.

        Args:
            data_list (list[str]): list of content lines to search.
            tex_md_flag (str, optional): Flag indicating content format (".tex" or ".md"). Defaults to ".tex".

        Returns:
            list[str]: list of found citation keys.

        Note:
            For LaTeX, searches for \\cite, \\citep, \\citet patterns.
            For Markdown, searches for [@key], @key; and ;@key] patterns.
        """
        cite_key_list = []
        if tex_md_flag == ".tex":
            regex_list = [re.compile(r"\\[a-z]*cite[tp]*{\s*([\w\-.,:/\s]*)\s*}")]
            cite_key_list.extend(regex_list[0].findall("".join(data_list)))
            cite_key_list = combine_content_in_list([re.split(",", c) for c in cite_key_list])
        elif tex_md_flag == ".md":
            regex_list = [
                re.compile(r"\[@([\w\-.:/]+)\]"),
                re.compile(r"@([\w\-.:/]+)\s*;"),
                re.compile(r";\s*@([\w\-.:/]*)\s*]"),
            ]
            cite_key_list = combine_content_in_list(
                [regex_list[i].findall("".join(data_list)) for i in range(len(regex_list))]
            )
        else:
            print(f"{tex_md_flag} must be `.tex` or `.md`.")

        cite_key_list = [c.strip() for c in cite_key_list if c.strip()]
        return sorted(set(cite_key_list), key=cite_key_list.index)

    def _cleanup_file(self, file_path: str) -> None:
        """Cleanup files and empty directories.

        Args:
            file_path (str): Path to file to be removed.
        """
        if os.path.exists(file_path):
            os.remove(file_path)
            dir_path = os.path.dirname(file_path)
            if dir_path != self.path_output_new:  # Don't remove the main output directory
                if len([f for f in os.listdir(dir_path) if f != ".DS_Store"]) == 0:
                    shutil.rmtree(dir_path)
