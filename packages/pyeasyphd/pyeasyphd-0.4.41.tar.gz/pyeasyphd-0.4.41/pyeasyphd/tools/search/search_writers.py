import copy
import os

from pyadvtools import combine_content_in_list, read_list, write_list
from pybibtexer.bib.bibtexparser import Library
from pybibtexer.main import PythonWriters

from ...main import BasicInput, PandocMdTo
from ...tools.search.utils import combine_keywords_for_file_name, combine_keywords_for_title, keywords_type_for_title


class WriteInitialResult(BasicInput):
    """Write initial results for single keyword.

    Args:
        options (dict): Configuration options.

    Attributes:
        options (dict): Configuration options.
    """

    def __init__(self, options: dict) -> None:
        """Initialize WriteInitialResult with configuration options.

        Args:
            options (dict): Configuration options.
        """
        super().__init__(options)

        self._level_title_md = "###"
        self._level_title_tex = "subsection"
        self._pandoc_md_to = PandocMdTo(options)

    def main(
        self,
        path_initial: str,
        output_prefix: str,
        field: str,
        keywords_type: str,
        combine_keywords: str,
        library_for_abbr: Library,
        library_for_zotero: Library,
        library_for_save: Library,
    ) -> tuple[list[list[str]], list[str]]:
        """Main method to write initial results.

        Args:
            path_initial (str): Path to initial directory.
            output_prefix (str): Prefix for output files.
            field (str): Field being searched.
            keywords_type (str): Type of keywords.
            combine_keywords (str): Combined keywords string.
            library_for_abbr (Library): Abbreviated bibliography library.
            library_for_zotero (Library): Zotero bibliography library.
            library_for_save (Library): Save bibliography library.

        Returns:
            tuple[list[list[str]], list[str]]: Tuple containing data and error messages.
        """
        error_pandoc_md_md = []

        # generate
        cite_keys = [entry.key for entry in library_for_abbr.entries]

        # update options
        _options = copy.deepcopy(self.options)
        _options["keep_entries_by_cite_keys"] = cite_keys
        _python_writer = PythonWriters(_options)

        # generate tex and md data
        data_list_tex, data_list_md, header = self.generate_content_tex_md(
            cite_keys, output_prefix, field, combine_keywords
        )

        # definition
        file_prefix = combine_keywords_for_file_name(combine_keywords)  # the file name prefix

        # write tex, md, and bib files
        data_list = [data_list_tex, data_list_md, library_for_abbr, library_for_zotero, library_for_save]
        mid_list = ["", "", "-abbr", "-zotero", "-save"]
        post_list = ["tex", "md", "bib", "bib", "bib"]
        path_write = os.path.join(path_initial, f"{field}-{keywords_type}")
        for i in range(len(post_list)):
            file_name = f"{file_prefix}{mid_list[i]}.{post_list[i]}"
            _python_writer.write_to_file(data_list[i], file_name, "w", path_write)

        # pandoc md to generate md file
        path_bib = os.path.join(path_write, f"{file_prefix}{mid_list[2]}.bib")  # bib_for_abbr
        data_list_pandoc_md = self._pandoc_md_to.pandoc_md_to_md(
            path_bib, path_write, path_write, f"{file_prefix}.md", f"{file_prefix}-pandoc.md"
        )

        # mian part
        # generate some md output data
        data_basic_md: list[str] = []
        data_beauty_md: list[str] = []
        data_complex_md: list[str] = []
        if data_list_pandoc_md:
            data_basic_md, data_beauty_md, data_complex_md = self.generate_basic_beauty_complex_md(
                header, cite_keys, data_list_pandoc_md, library_for_zotero
            )
        else:
            error_pandoc_md_md.append(f"- pandoc full false: {file_prefix}_pandoc.md" + "\n")

        # write basic beauty complex md files
        basic_beauty_complex = ["-basic", "-beauty", "-complex"]
        for d, name in zip([data_basic_md, data_beauty_md, data_complex_md], basic_beauty_complex, strict=True):
            write_list(d, f"{file_prefix}{name}.md", "w", path_write)

        # save all (tex, md, bib) files
        x = [f"{i}.{j}" for i, j in zip(mid_list, post_list, strict=True)]
        x.extend([f"{i}.md" for i in basic_beauty_complex])
        data_temp = [[os.path.join(path_write, file_prefix + i)] for i in x]
        return data_temp, error_pandoc_md_md

    def generate_basic_beauty_complex_md(
        self, header: str, cite_key_list: list[str], data_list_pandoc_md: list[str], library_for_zotero: Library
    ) -> tuple[list[str], list[str], list[str]]:
        """Generate basic, beauty, and complex markdown content.

        Args:
            header (str): Header string for the content.
            cite_key_list (list[str]): list of citation keys.
            data_list_pandoc_md (list[str]): list of pandoc markdown data.
            library_for_zotero (Library): Zotero bibliography library.

        Returns:
            tuple[list[str], list[str], list[str]]: Tuple containing basic, beauty, and complex markdown content.
        """
        data_basic_md, data_beauty_md, data_complex_md = [], [], []

        # library
        _options = copy.deepcopy(self.options)
        _python_writer = PythonWriters(_options)
        key_url_http_bib_dict = _python_writer.output_key_url_http_bib_dict(library_for_zotero)

        key_basic_dict, key_beauty_dict, key_complex_dict = self._pandoc_md_to.generate_key_data_dict(
            data_list_pandoc_md, key_url_http_bib_dict
        )

        if key_basic_dict and key_beauty_dict and key_complex_dict:
            data_basic_md, data_beauty_md, data_complex_md = [header + "\n"], [header + "\n"], [header + "\n"]
            for i in range(length := len(cite_key_list)):
                data_basic_md.extend(self._convert_to_special_list(key_basic_dict.get(cite_key_list[i], [])))
                data_beauty_md.extend(self._convert_to_special_list(key_beauty_dict.get(cite_key_list[i], [])))
                data_complex_md.extend(self._convert_to_special_list(key_complex_dict.get(cite_key_list[i], [])))
                if i < (length - 1):
                    data_basic_md.append("\n")
                    data_beauty_md.append("\n")
                    data_complex_md.append("\n")
        return data_basic_md, data_beauty_md, data_complex_md

    @staticmethod
    def _convert_to_special_list(data_list: list[str]) -> list[str]:
        """Convert data list to special formatted list.

        Args:
            data_list (list[str]): list of data strings.

        Returns:
            list[str]: Formatted list with proper indentation.
        """
        if len(data_list) > 0:
            data_list[0] = "- " + data_list[0]
        for j in range(len(data_list) - 1):
            if data_list[j][-1] == "\n":
                data_list[j + 1] = "  " + data_list[j + 1]
        return data_list

    def generate_content_tex_md(
        self, cite_key_list: list[str], output_prefix: str, field: str, combine_keywords: str
    ) -> tuple[list[str], list[str], str]:
        """Generate LaTeX and markdown content.

        Args:
            cite_key_list (list[str]): list of citation keys.
            output_prefix (str): Prefix for output files.
            field (str): Field being searched.
            combine_keywords (str): Combined keywords string.

        Returns:
            tuple[list[str], list[str], str]: Tuple containing LaTeX content, markdown content, and header.
        """
        c_k_f_t = combine_keywords_for_title(combine_keywords)

        number_references = len(cite_key_list)
        _title = f"{output_prefix} {field} contains {number_references} {c_k_f_t}"

        tex_header = f"\\{self._level_title_tex}" + "{" + _title + "}\n"
        tex_body = ["\\nocite{" + f"{c_k}" + "}\n" for c_k in cite_key_list]
        tex_tail = "\\printbibliography\n\n\\ifx \\clearPage \\undefined \\else \\clearpage \\fi\n"
        data_list_tex = combine_content_in_list([[tex_header], ["\n"], tex_body, ["\n"], [tex_tail]])

        md_header = f"{self._level_title_md}" + " " + _title + "\n"
        md_body = [r"- [@" + f"{c_k}" + "]\n" for c_k in cite_key_list]
        data_list_md = combine_content_in_list([[md_header], ["\n"], md_body])
        return data_list_tex, data_list_md, md_header


class WriteSeparateResult:
    """Write separate result for different keyword types."""

    def __init__(self) -> None:
        """Initialize WriteSeparateResult with title levels."""
        self._level_title_md = "##"
        self._level_title_tex = "section"

    def main(
        self, data_temp: list[list[str]], field: str, keywords_type: str, combine_keywords: str, path_separate: str
    ) -> None:
        """Main method to write separate results.

        Args:
            data_temp (list[list[str]]): list of data lists for different file types.
            field (str): Field being processed.
            keywords_type (str): Type of keywords.
            combine_keywords (str): Combined keywords string.
            path_separate (str): Path to separate directory.
        """
        k_t_f_t = keywords_type_for_title(keywords_type)
        _title = f"{field.title()} contains {k_t_f_t}"

        file_prefix = combine_keywords_for_file_name(combine_keywords)  # the file name prefix
        mid_list = ["", "", "-abbr", "-zotero", "-save", "-basic", "-beauty", "-complex"]
        post_list = ["tex", "md", "bib", "bib", "bib", "md", "md", "md"]

        len_data_temp = len(data_temp)  # len(data_temp) = len(mid_list) = len(post_list) = 8
        split_flag = mid_list.index("-abbr")

        for i in range(split_flag, len_data_temp):
            path_temp = os.path.join(path_separate, f"{keywords_type}", f"{field}-{post_list[i]}{mid_list[i]}")
            full_file = os.path.join(path_temp, rf"{file_prefix}.{post_list[i]}")
            temp_data_list = read_list(data_temp[i][0], "r", None)
            if not os.path.isfile(full_file):
                if post_list[i] == "md":
                    temp_data_list.insert(0, f"{self._level_title_md}" + " " + _title + "\n\n")
                elif post_list[i] == "tex":
                    temp_data_list.insert(0, f"\\{self._level_title_tex}" + "{" + _title + "}\n\n")
            else:
                temp_data_list.insert(0, "\n")
            write_list(temp_data_list, full_file, "a", None, False, False)  # Compulsory `a`
        return None


class WriteAbbrCombinedResults:
    """Write combined results for abbreviations (such as `TEVC`, `PNAS`).

    Args:
        options (dict): Configuration options.

    Attributes:
        options (dict): Configuration options.
        pandoc_md_basic_to_pdf (bool): Whether to convert basic markdown to PDF.
        pandoc_md_beauty_to_pdf (bool): Whether to convert beauty markdown to PDF.
        pandoc_md_complex_to_pdf (bool): Whether to convert complex markdown to PDF.
        pandoc_md_basic_to_html (bool): Whether to convert basic markdown to HTML.
        pandoc_md_beauty_to_html (bool): Whether to convert beauty markdown to HTML.
        pandoc_md_complex_to_html (bool): Whether to convert complex markdown to HTML.
    """

    def __init__(self, options: dict) -> None:
        """Initialize WriteAbbrCombinedResults with configuration options.

        Args:
            options (dict): Configuration options.
        """
        self.pandoc_md_basic_to_pdf: bool = options.get("pandoc_md_basic_to_pdf", False)
        self.pandoc_md_beauty_to_pdf: bool = options.get("pandoc_md_beauty_to_pdf", False)
        self.pandoc_md_complex_to_pdf: bool = options.get("pandoc_md_complex_to_pdf", False)
        self.pandoc_md_basic_to_html: bool = options.get("pandoc_md_basic_to_html", False)
        self.pandoc_md_beauty_to_html: bool = options.get("pandoc_md_beauty_to_html", False)
        self.pandoc_md_complex_to_html: bool = options.get("pandoc_md_complex_to_html", True)

        self._level_title_md = "##"
        self._level_title_tex = "section"
        self._pandoc_md_to = PandocMdTo(options)

    def main(
        self, search_field_list, keywords_type: str, field_data_dict: dict[str, list[list[str]]], path_combine: str
    ) -> tuple[list[str], list[str]]:
        """Main method to write combined results for abbreviations.

        Args:
            search_field_list: list of search fields.
            keywords_type (str): Type of keywords.
            field_data_dict (dict[str, list[list[str]]]): dictionary containing field data.
            path_combine (str): Path to combine directory.

        Returns:
            tuple[list[str], list[str]]: Tuple containing error messages for PDF and HTML conversion.
        """
        path_subsection = os.path.join(path_combine, "tex-subsection")
        path_md = os.path.join(path_combine, "md")
        path_bib = os.path.join(path_combine, "bib")

        mid_list = ["", "", "-abbr", "-zotero", "-save", "-basic", "-beauty", "-complex"]
        post_list = ["tex", "md", "bib", "bib", "bib", "md", "md", "md"]
        path_list = [path_subsection, path_md, path_bib, path_bib, path_bib]
        for i in ["-basic", "-beauty", "-complex"]:
            path_list.append(os.path.join(path_combine, f"md{i}"))
        # len(mid_list) == len(post_list) == len(path_list) == 8

        k_t_f_t = keywords_type_for_title(keywords_type)

        error_pandoc_md_pdf, error_pandoc_md_html = [], []
        for field in search_field_list:
            if not field_data_dict.get(field):
                continue

            # write files
            file_prefix = f"{field}-{keywords_type}"  # the file name prefix
            _title = f"{field.title()} contains {k_t_f_t}"

            for j in range(0, len(post_list)):
                temp = combine_content_in_list([read_list(file, "r") for file in field_data_dict[field][j]], ["\n"])
                if post_list[j] == "md":
                    temp.insert(0, f"{self._level_title_md}" + " " + _title + "\n\n")
                elif post_list[j] == "tex":
                    temp.insert(0, f"\\{self._level_title_tex}" + "{" + _title + "}\n\n")
                write_list(temp, f"{file_prefix}{mid_list[j]}.{post_list[j]}", "w", path_list[j])

            # generate tex pdf html
            # for tex
            self._pandoc_md_to.generate_tex_content(file_prefix, path_subsection, path_bib, path_combine)

            # for pdf
            for i in ["basic", "beauty", "complex"]:
                if eval(f"self.pandoc_md_{i}_to_pdf"):
                    error_flag_pdf = self._pandoc_md_to.pandoc_md_to_pdf(
                        os.path.join(path_combine, f"md-{i}"),
                        f"{file_prefix}-{i}.md",
                        os.path.join(path_combine, f"pdf-{i}"),
                        f"{file_prefix}-{i}.pdf",
                    )
                    if error_flag_pdf:
                        error_pandoc_md_pdf.append(error_flag_pdf)

            # for html
            for i in ["basic", "beauty", "complex"]:
                if eval(f"self.pandoc_md_{i}_to_html"):
                    error_flag_html = self._pandoc_md_to.pandoc_md_to_html(
                        os.path.join(path_combine, f"md-{i}"),
                        os.path.join(path_combine, f"html-{i}"),
                        f"{file_prefix}-{i}.md",
                        f"{file_prefix}-{i}.html",
                        True,
                    )
                    if error_flag_html:
                        error_pandoc_md_html.append(error_flag_html)
        return error_pandoc_md_pdf, error_pandoc_md_html
