import copy
import os
import re
import shutil
import time
from typing import Any

from pyadvtools import combine_content_in_list, delete_empty_lines_last_occur_add_new_line, read_list, write_list
from pybibtexer.bib.core import ConvertStrToLibrary
from pybibtexer.main.python_writers import PythonWriters

from .basic_input import BasicInput
from .pandoc_md_to import PandocMdTo


def batch_convert_citations(text):
    r"""Process all citations in the text, including multiple citations in one bracket.

    Example: [@ref1; @ref2] -> <sup>[@ref1](#ref1)</sup><sup>[@ref2](#ref2)</sup>
    """
    # Match all citation patterns within square brackets
    pattern = r"\[([^]]+)\]"

    def process_citation(match):
        citations = match.group(1)
        # Split multiple citations (support semicolon or comma separation)
        citation_list = re.split(r"[;,]", citations)

        result = []
        for citation in citation_list:
            citation = citation.strip()
            if citation.startswith("@"):
                cite_id = citation[1:]  # Remove the @ symbol
                result.append(f"[{citation}](#{cite_id.lower()})")
            else:
                # Keep non-citation content in original format
                result.append(f"[{citation}]")

        return "".join(result)

    return re.sub(pattern, process_citation, text)


class PythonRunMd(BasicInput):
    r"""Python markdown processing class.

    Args:
        options (dict[str, Any]): Configuration options.

    Attributes:
        delete_temp_generate_md (bool): Whether to delete temporary generated markdown files. Defaults to True.
        add_reference_in_md (bool): Whether to add references in markdown. Defaults to True.
        add_bib_in_md (bool): Whether to add bibliography in markdown. Defaults to False.
        replace_cite_to_fullcite_in_md (bool): Whether to replace citations with full citations in markdown. Defaults to False.
        replace_by_basic_beauty_complex_in_md (str): Replace by basic, beauty, or complex format. Defaults to "beauty".
        display_basic_beauty_complex_references_in_md (str): Display basic, beauty, or complex references. Defaults to "beauty".
        add_anchor_in_md (bool): Whether add anchor in markdown. Defaults to False.
        details_to_bib_separator (str): Separator between <details> and bibliography content. Defaults to "\n".
    """

    def __init__(self, options: dict[str, Any]) -> None:
        """Initialize PythonRunMd with configuration options.

        Args:
            options (dict[str, Any]): Configuration options.
        """
        super().__init__(options)

        # for md
        self.final_output_main_md_name: str = options.get("final_output_main_md_name", "")
        self.delete_temp_generate_md: bool = options.get("delete_temp_generate_md", True)
        self.add_reference_in_md: bool = options.get("add_reference_in_md", True)
        self.add_bib_in_md: bool = options.get("add_bib_in_md", False)
        self.replace_cite_to_fullcite_in_md: bool = options.get("replace_cite_to_fullcite_in_md", False)
        self.replace_by_basic_beauty_complex_in_md: str = options.get("replace_by_basic_beauty_complex_in_md", "beauty")
        self.display_basic_beauty_complex_references_in_md: str = options.get(
            "display_basic_beauty_complex_references_in_md", "beauty"
        )
        self.add_anchor_in_md: bool = options.get("add_anchor_in_md", False)
        self.details_to_bib_separator: str = options.get("details_to_bib_separator", "\n")

        # for md
        self._pandoc_md_to = PandocMdTo(self.options)

        _options = {}
        _options["is_standardize_bib"] = False
        _options["is_display_implicit_comments"] = False
        _options.update(options)
        self._generate_library = ConvertStrToLibrary(_options)

    def special_operate_for_md(
        self,
        path_output: str,
        data_list_md: list[str],
        output_md_name: str,
        full_bib_for_abbr: str,
        full_bib_for_zotero: str,
        template_name: str = "article",
        generate_html: bool = False,
        generate_tex: bool = True,
    ) -> tuple[list[str], list[str]]:
        """Perform special operations on markdown files.

        Args:
            path_output (str): Path to output directory.
            data_list_md (list[str]): list of markdown content lines.
            output_md_name (str): Name of output markdown file.
            full_bib_for_abbr (str): Path to abbreviated bibliography file.
            full_bib_for_zotero (str): Path to Zotero bibliography file.
            template_name (str): Name of template to use. Defaults to "article".
            generate_html (bool): Whether to generate HTML. Defaults to False.
            generate_tex (bool): Whether to generate LaTeX. Defaults to True.

        Returns:
            tuple[list[str], list[str]]: Tuple containing processed markdown and LaTeX content.
        """
        path_temp = os.path.join(path_output, "{}".format(time.strftime("%Y_%m_%d_%H_%M_%S")))
        if not os.path.exists(path_temp):
            os.makedirs(path_temp)

        # write original md content to temp file
        full_temp_md = os.path.join(path_temp, output_md_name)
        write_list(data_list_md, full_temp_md, "w", None, False)

        # pandoc md to md to update md content
        if read_list(full_bib_for_abbr, "r") and read_list(full_bib_for_zotero, "r"):
            data_list_md = self._special_operate_for_md(
                output_md_name, path_temp, full_bib_for_abbr, full_bib_for_zotero
            )
        elif os.path.exists(full_bib_for_abbr) and os.path.exists(full_bib_for_zotero):
            print(f"The content of bib: {full_bib_for_abbr} or {full_bib_for_zotero} is empty.")
        else:
            pass

        # main name
        main_name = self.final_output_main_md_name
        if len(main_name) == 0:
            main_name = output_md_name.split(".md")[0] + "_" + self.replace_by_basic_beauty_complex_in_md
            main_name = main_name + "_" + self.display_basic_beauty_complex_references_in_md + ".md"
        if main_name.lower() == output_md_name.lower():
            main_name = main_name.split(".md")[0] + "_.md"
        if main_name[-3:] != ".md":
            main_name = main_name + ".md"

        # write new generated md content to given file
        write_list(data_list_md, main_name, "w", path_output, False)

        # for generating html file from md file
        if data_list_md and generate_html:
            self._pandoc_md_to.pandoc_md_to_html(
                path_output, path_output, main_name, f"{main_name.split('.md')[0]}.html", True
            )

        # pandoc md to latex
        data_list_tex = []
        if generate_tex:
            n5 = "5_pandoc" + ".tex"
            data_list_tex = self._pandoc_md_to.pandoc_md_to_tex(template_name, path_temp, path_temp, output_md_name, n5)

        # delete temp path
        if self.delete_temp_generate_md:
            shutil.rmtree(path_temp)
        return data_list_md, data_list_tex

    def _special_operate_for_md(
        self, output_md_name: str, path_temp: str, full_bib_for_abbr: str, full_bib_for_zotero: str
    ) -> list[str]:
        """Perform special operations for markdown processing.

        Args:
            output_md_name (str): Name of output markdown file.
            path_temp (str): Path to temporary directory.
            full_bib_for_abbr (str): Path to abbreviated bibliography file.
            full_bib_for_zotero (str): Path to Zotero bibliography file.

        Returns:
            list[str]: list of processed markdown content lines.
        """
        # pandoc markdown to markdown
        n1 = "1_pandoc" + ".md"
        data_list_md = self._pandoc_md_to.pandoc_md_to_md(full_bib_for_abbr, path_temp, path_temp, output_md_name, n1)

        # use zotero bib to generate library
        bib_for_zotero = read_list(full_bib_for_zotero, "r")
        library = self._generate_library.generate_library(bib_for_zotero)

        _options = {}
        _options.update(self.options)
        _options["add_index_to_enties"] = False
        _python_writers = PythonWriters(_options)
        key_url_http_bib_dict = _python_writers.output_key_url_http_bib_dict(library)

        content_md = []
        if data_list_md and key_url_http_bib_dict:
            key_basic_dict, key_beauty_dict, key_complex_dict = self._pandoc_md_to.generate_key_data_dict(
                data_list_md, key_url_http_bib_dict
            )

            key_in_md = list(key_url_http_bib_dict.keys())

            # generate by replacing `- [@citation_key]` to `- [citation_key]`
            content = read_list(output_md_name, "r", path_temp)
            if self.replace_cite_to_fullcite_in_md:
                regex = re.compile(r"(\s*[-\+\*]\s*)\[@({})\]".format("|".join(key_in_md)))
                for i in range(len(content)):
                    if not (mch := regex.match(content[i])):
                        continue

                    content[i] = content[i].replace(mch.group(), mch.group(1) + "[" + mch.group(2) + "]")
            # add anchor
            if self.add_anchor_in_md:
                content = [batch_convert_citations(line) for line in content]
            n2 = "2_generate" + ".md"
            write_list(content, n2, "w", path_temp)

            # pandoc markdown to markdown
            n3 = "3_pandoc" + ".md"
            data_list_md = self._pandoc_md_to.pandoc_md_to_md(full_bib_for_abbr, path_temp, path_temp, n2, n3)

            # generate by replacing `- [citation_key]` to `- reference`
            if self.replace_cite_to_fullcite_in_md:
                regex = re.compile(r"(\s*)([-\+\*])(\s*)[\\]*\[({})[\\]*\]".format("|".join(key_in_md)))
                for i in range(len(data_list_md)):
                    if not (mch := regex.search(data_list_md[i])):
                        continue

                    space_one, b, space_two, cite_key = mch.groups()
                    if self.replace_by_basic_beauty_complex_in_md.lower() == "basic":
                        temp_list = copy.deepcopy(key_basic_dict[cite_key])
                    elif self.replace_by_basic_beauty_complex_in_md.lower() == "complex":
                        temp_list = copy.deepcopy(key_complex_dict[cite_key])
                    else:
                        temp_list = copy.deepcopy(key_beauty_dict[cite_key])

                    temp = "".join(self._special_format(temp_list, space_one, space_two))
                    data_list_md[i] = data_list_md[i].replace(mch.group(), space_one + b + space_two + temp.strip())
            n4 = "4_generate" + ".md"
            write_list(data_list_md, os.path.join(path_temp, n4), "w")

            # obtain footnote part (in the last part of the contents)
            main_part, last_part = [], []
            main_part_flag, last_part_flag = True, True
            for line_index in range(len(data_list_md)):
                if main_part_flag and re.match(r"#+ [\"']?References[\"']?\s[\[{]", data_list_md[line_index]):
                    main_part_flag = False
                    main_part = delete_empty_lines_last_occur_add_new_line(data_list_md[:line_index])
                if last_part_flag and re.match(r"^\[\^1]: ", data_list_md[line_index]):
                    last_part_flag = False
                    last_part = delete_empty_lines_last_occur_add_new_line(data_list_md[line_index:])

            if main_part_flag:
                main_part = delete_empty_lines_last_occur_add_new_line(data_list_md)
            if self.add_reference_in_md:
                main_part.append("\n## References\n")
            if len(last_part) > 0:
                last_part.insert(0, "[//]: (Footnotes)\n\n")
                last_part.append("\n")

            # for bib
            bib_in_md = []
            if self.add_bib_in_md:
                temp_c = combine_content_in_list([key_url_http_bib_dict[k][2] for k in key_in_md])
                bib_in_md = combine_content_in_list(
                    [
                        ["## Bibliography\n\n"],
                        [f"<details>{self.details_to_bib_separator}"],
                        ["```\n"],
                        temp_c,
                        ["```\n"],
                        ["</details>\n"],
                    ]
                )

            # Generate basic/beauty/complex markdown content
            if dct := eval(f"key_{self.display_basic_beauty_complex_references_in_md}_dict"):
                content_md = self._generate_content_md(dct, key_in_md, main_part, last_part, bib_in_md)
        return content_md

    @staticmethod
    def _special_format(temp_list: list[str], space_one: str, space_two: str) -> list[str]:
        """Apply special formatting for alignment.

        Args:
            temp_list (list[str]): list of strings to format.
            space_one (str): First space string.
            space_two (str): Second space string.

        Returns:
            list[str]: Formatted list of strings.
        """
        for j in range(len(temp_list) - 1):
            if temp_list[j][-1] == "\n":
                temp_list[j + 1] = (space_one + " " + space_two) + temp_list[j + 1]
        return temp_list

    def _generate_content_md(
        self,
        key_basic_beauty_complex_dict: dict[str, list[str]],
        key_in_md_tex: list[str],
        main_part: list[str],
        last_part: list[str],
        bib_in_md: list[str],
    ) -> list[str]:
        """Generate markdown content from various components.

        Args:
            key_basic_beauty_complex_dict (dict[str, list[str]]): dictionary of formatted references.
            key_in_md_tex (list[str]): list of citation keys in markdown/LaTeX.
            main_part (list[str]): Main content part.
            last_part (list[str]): Last content part.
            bib_in_md (list[str]): Bibliography content for markdown.

        Returns:
            list[str]: Generated markdown content.
        """
        temp_b = []
        if self.add_reference_in_md:
            temp_b = combine_content_in_list([key_basic_beauty_complex_dict[k] for k in key_in_md_tex], ["\n"])
        content_md = combine_content_in_list([main_part, ["\n"], temp_b, last_part, bib_in_md])
        return content_md
