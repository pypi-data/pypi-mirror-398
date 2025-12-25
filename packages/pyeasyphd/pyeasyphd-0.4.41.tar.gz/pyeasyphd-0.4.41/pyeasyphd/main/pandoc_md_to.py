import copy
import os
import re
import subprocess
import time

from pyadvtools import (
    combine_content_in_list,
    delete_empty_lines_last_occur_add_new_line,
    insert_list_in_list,
    read_list,
    substitute_in_list,
    write_list,
)

from ..utils.utils import operate_on_generate_html
from .basic_input import BasicInput


class PandocMdTo(BasicInput):
    r"""Pandoc markdown to various formats (md, tex, html, pdf).

    Args:
        options (dict): Configuration options.

    Attributes:
        markdown_name (str): Markdown name. Defaults to "multi-markdown".
        markdown_citation (str): Markdown citation format. Defaults to "markdown_mmd".
        columns_in_md (int): Number of columns in markdown. Defaults to 120.
        display_one_line_reference_note (bool): Whether to display one line reference note. Defaults to False.
        cite_flag_in_tex (str): Citation flag in LaTeX. Defaults to "cite".
        add_url_for_basic_dict (bool): Whether to add url for items in basic dict. Defualts to True.
        add_anchor_for_basic_dict (bool): Whether to add anchor for items in basic dict. Defaults to False.
        add_anchor_for_beauty_dict (bool): Whether to add anchor for items in beauty dict. Defaults to False.
        add_anchor_for_complex_dict (bool): Whether to add anchor for items in complex dict. Defaults to False.
        details_to_bib_separator (str): Separator between <details> and bibliography content. Defaults to "\n".
    """

    def __init__(self, options: dict) -> None:
        """Initialize PandocMdTo with configuration options.

        Args:
            options (dict): Configuration options.
        """
        super().__init__(options)

        self.markdown_name: str = "multi-markdown"
        self.markdown_citation: str = "markdown_mmd"
        if self.markdown_name == "pandoc-markdown":
            self.markdown_citation = "markdown-citations"

        self.columns_in_md: int = options.get("columns_in_md", 120)
        self.display_one_line_reference_note: bool = options.get("display_one_line_reference_note", False)
        # tex
        self.cite_flag_in_tex: str = options.get("cite_flag_in_tex", "cite")

        self.add_url_for_basic_dict: bool = options.get("add_url_for_basic_dict", True)
        self.add_anchor_for_basic_dict: bool = options.get("add_anchor_for_basic_dict", False)
        self.add_anchor_for_beauty_dict: bool = options.get("add_anchor_for_beauty_dict", False)
        self.add_anchor_for_complex_dict: bool = options.get("add_anchor_for_complex_dict", False)

        self.details_to_bib_separator: str = options.get("details_to_bib_separator", "\n")

    def pandoc_md_to_md(
        self, path_bib: str, path_md_one: str, path_md_two: str, name_md_one: str | None, name_md_two: str | None
    ) -> list[str]:
        """Convert markdown to markdown using pandoc.

        Args:
            path_bib (str): Path to bibliography file.
            path_md_one (str): Path to source markdown directory.
            path_md_two (str): Path to destination markdown directory.
            name_md_one (Optional[str]): Name of source markdown file.
            name_md_two (Optional[str]): Name of destination markdown file.

        Returns:
            list[str]: list of processed markdown content lines.
        """
        full_one = path_md_one if name_md_one is None else os.path.join(path_md_one, name_md_one)
        full_two = path_md_two if name_md_two is None else os.path.join(path_md_two, name_md_two)
        return self._pandoc_md_to_md(full_one, full_two, path_bib)

    def _pandoc_md_to_md(self, full_md_one: str, full_md_two: str, path_bib: str) -> list[str]:
        """Internal method to convert markdown to markdown using pandoc.

        Args:
            full_md_one (str): Full path to source markdown file.
            full_md_two (str): Full path to destination markdown file.
            path_bib (str): Path to bibliography file.

        Returns:
            list[str]: list of processed markdown content lines.
        """
        if not os.path.exists(path_two := os.path.dirname(full_md_two)):
            os.makedirs(path_two)

        if os.path.exists(self.full_csl_style_pandoc):
            cmd = (
                f"pandoc {full_md_one} -t {self.markdown_citation} "
                f"-o {full_md_two} -M reference-section-title='References' "
                f"--citeproc --bibliography={path_bib} --csl={self.full_csl_style_pandoc} --columns {self.columns_in_md}"
            )
        else:
            cmd = (
                f"pandoc {full_md_one} -t {self.markdown_citation} "
                f"-o {full_md_two} -M reference-section-title='References' "
                f"--citeproc --bibliography={path_bib} --columns {self.columns_in_md}"
            )

        try:
            subprocess.run(cmd.split(), check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print("Pandoc error in pandoc md to md:", e.stderr)

        if not os.path.exists(full_md_two):
            print(f"- pandoc false from md to md: {os.path.basename(full_md_two)}\n")
            return []

        return self._standardize_markdown_content(full_md_two)

    @staticmethod
    def _standardize_markdown_content(full_md: str) -> list[str]:
        regex = re.compile(r"(\s*>*\s*[-+*]+)\s\s\s(.*)")
        for i in range(len(data_list := read_list(full_md, "r"))):
            if mch := regex.match(data_list[i]):
                data_list[i] = data_list[i].replace(mch.group(), mch.group(1) + " " + mch.group(2))
        return data_list

    # for pandoc markdown files to tex files
    def pandoc_md_to_tex(
        self, template_name: str, path_md: str, path_tex: str, name_md: str | None, name_tex: str | None
    ) -> list[str]:
        full_one = path_md if name_md is None else os.path.join(path_md, name_md)
        full_two = path_tex if name_tex is None else os.path.join(path_tex, name_tex)
        return self._pandoc_md_to_tex(full_one, full_two, template_name)

    def _pandoc_md_to_tex(self, full_md: str, full_tex: str, template_name: str) -> list[str]:
        """Pandoc."""
        if not os.path.exists(path_tex := os.path.dirname(full_tex)):
            os.makedirs(path_tex)

        if template_name.lower() == "beamer":
            cmd = f"pandoc {full_md} -t beamer -o {full_tex} --from markdown "
        else:
            cmd = f"pandoc {full_md} -o {full_tex} --from markdown "

        try:
            subprocess.run(cmd.split(), check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print("Pandoc error in pandoc md to tex:", e.stderr)

        if not os.path.exists(full_tex):
            print(f"- pandoc false from md to tex: {os.path.basename(full_md)}\n")
            return []

        return self._substitute_in_tex_from_md(read_list(full_tex, "r", None))

    def _substitute_in_tex_from_md(self, data_list: list[str]) -> list[str]:
        old_str_list = [r"{\[}@", r"{\[}-@", r"{\[}", r"{\]}", r"\\_"]
        new_str_list = [rf"\\{self.cite_flag_in_tex}" + "{", rf"\\{self.cite_flag_in_tex}" + "{", "{", "}", "_"]
        old_str_list.extend([r"\\footnote<.->{", r";", r"@"])
        new_str_list.extend([r"\\footnote{", ",", ""])
        return substitute_in_list(old_str_list, new_str_list, data_list)

    # for pandoc markdown files to html files
    def pandoc_md_to_html(
        self, path_md: str, path_html: str, name_md: str | None, name_html: str | None, operate: bool = False
    ) -> str:
        full_one = path_md if name_md is None else os.path.join(path_md, name_md)
        full_two = path_html if name_html is None else os.path.join(path_html, name_html)
        return self._pandoc_md_to_html(full_one, full_two, operate)

    @staticmethod
    def _pandoc_md_to_html(full_md: str, full_html: str, operate: bool = False) -> str:
        """Pandoc."""
        if not os.path.exists(path_html := os.path.dirname(full_html)):
            os.makedirs(path_html)

        cmd = f"pandoc {full_md} -o {full_html} --from markdown "

        try:
            subprocess.run(cmd.split(), check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print("Pandoc error in pandoc md to html:", e.stderr)

        if not os.path.exists(full_html):
            return f"- pandoc false from md to html: {os.path.basename(full_md)}\n"

        if operate:
            operate_on_generate_html(full_html)
        return ""

    # for pandoc markdown files to pdf files
    def pandoc_md_to_pdf(self, path_md: str, path_pdf: str, name_md: str | None, name_pdf: str | None) -> str:
        full_one = path_md if name_md is None else os.path.join(path_md, name_md)
        full_two = path_pdf if name_pdf is None else os.path.join(path_pdf, name_pdf)
        return self._pandoc_md_to_pdf(full_one, full_two)

    def _pandoc_md_to_pdf(self, full_md: str, full_pdf: str) -> str:
        """Pandoc."""
        if not os.path.exists(path_pdf := os.path.dirname(full_pdf)):
            os.makedirs(path_pdf)

        if os.path.exists(self.full_tex_article_template_pandoc):
            cmd = (
                f"pandoc {full_md} -o {full_pdf} --from markdown "
                f"--template {self.full_tex_article_template_pandoc} --listings --pdf-engine=xelatex"
            )
        else:
            cmd = f"pandoc {full_md} -o {full_pdf} --from markdown  --listings --pdf-engine=xelatex"

        try:
            subprocess.run(cmd.split(), check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print("Pandoc error in pandoc md to pdf:", e.stderr)

        if not os.path.exists(full_pdf):
            return f"- pandoc false from md to pdf: {os.path.basename(full_md)}\n"
        return ""

    # --------- --------- --------- --------- --------- --------- --------- --------- --------- #
    # md
    def generate_key_data_dict(
        self, pandoc_md_data_list: list[str], key_url_http_bib_dict: dict[str, list[list[str]]]
    ) -> tuple[dict[str, list[str]], dict[str, list[str]], dict[str, list[str]]]:
        """Generate."""
        key_reference_dict = self._generate_citation_key_reference_dict_from_pandoc_md(pandoc_md_data_list)
        (key_basic_dict, key_beauty_dict, key_complex_dict) = self._generate_basic_beauty_complex_dict(
            key_url_http_bib_dict, key_reference_dict
        )
        return key_basic_dict, key_beauty_dict, key_complex_dict

    def _generate_citation_key_reference_dict_from_pandoc_md(
        self, pandoc_md_data_list: list[str]
    ) -> dict[str, list[str]]:
        """Generate."""
        pandoc_md_data_list = self.__append_pandoc_md_reference_part(pandoc_md_data_list)

        line_index, len_data = 0, len(pandoc_md_data_list)
        if self.markdown_name == "pandoc-markdown":
            a_flag, b_flag = r"^:::\s{#ref-(.*)\s\.csl-entry}", r"^:::"
        else:  # multi-markdown
            a_flag, b_flag = r'^<div\sid="ref-(.*?)"', r"^</div>"

        regex_one, regex_two = re.compile(a_flag), re.compile(b_flag)
        key_reference_dict = {}
        while line_index < len_data:
            match_one = regex_one.search(pandoc_md_data_list[line_index])
            line_index += 1
            if not match_one:
                continue
            citation_key = match_one.group(1).strip()

            content = []
            while line_index < len_data:
                line = pandoc_md_data_list[line_index]
                if regex_two.search(line):
                    break

                line_index += 1
                if mch := re.search(r"([<\[]https?://)", line):
                    content.append(line.split(mch.group(1))[0][:-1])
                    break
                else:
                    if line.strip():
                        content.append(line)

            key_reference_dict.update({citation_key: delete_empty_lines_last_occur_add_new_line(content)})
        return key_reference_dict

    def __append_pandoc_md_reference_part(self, pandoc_md_data_list: list[str]) -> list[str]:
        """Append the line which starts with '::: {#'."""
        line_index, len_data = 0, len(pandoc_md_data_list)
        if self.markdown_name == "pandoc-markdown":
            a_flag, b_flag = r":::\s{#", r"}"
        else:  # multi-markdown
            a_flag, b_flag = r'<div\sid="ref', r">"
        regex = re.compile(a_flag)
        new_list = []
        while line_index < len_data:
            line = pandoc_md_data_list[line_index]
            line_index += 1
            if regex.search(line):
                while line_index < len_data:
                    if b_flag != line.rstrip()[-1]:
                        line = line.rstrip() + " " + pandoc_md_data_list[line_index].lstrip()
                        line_index += 1
                    else:
                        new_list.append(line)
                        break
                if line_index == len_data:
                    new_list.append(line)
            else:
                new_list.append(line)
        return delete_empty_lines_last_occur_add_new_line(new_list)

    def _generate_basic_beauty_complex_dict(
        self, key_url_http_bib_dict: dict[str, list[list[str]]], key_reference_dict: dict[str, list]
    ) -> tuple[dict[str, list[str]], dict[str, list[str]], dict[str, list[str]]]:
        """Generate."""
        header_list = [f"<details>{self.details_to_bib_separator}", "```\n"]
        tail_list = ["```\n", "</details>\n"]

        key_basic_dict: dict[str, list[str]] = {}
        key_beauty_dict: dict[str, list[str]] = {}
        key_complex_dict: dict[str, list[str]] = {}

        key_list_http = list(key_url_http_bib_dict.keys())
        key_list_md = list(key_reference_dict.keys())
        if set(key_list_http) != set(key_list_md):
            print(f"`key_list_md`: set({key_list_md}) should be the same with `key_list_http`: set({key_list_http}).")
            return key_basic_dict, key_beauty_dict, key_complex_dict

        for k in key_list_http:
            a: list[str] = copy.deepcopy(key_reference_dict[k])
            b: list[str] = copy.deepcopy(key_reference_dict[k])
            aa: list[str] = key_url_http_bib_dict[k][0]
            bb: list[str] = key_url_http_bib_dict[k][1]

            # add url
            if self.add_url_for_basic_dict:
                a.extend(aa)

            b.extend(bb)

            # add anchor
            if self.add_anchor_for_basic_dict:
                a = [f'<a id="{k.lower()}"></a>\n', *a]
            if self.add_anchor_for_beauty_dict or self.add_anchor_for_complex_dict:
                b = [f'<a id="{k.lower()}"></a>\n', *b]

            if self.display_one_line_reference_note:
                a = ["".join(a).replace("\n", " ").strip() + "\n"]
                b = ["".join(b).replace("\n", " ").strip() + "\n"]

            c = combine_content_in_list([b, header_list, key_url_http_bib_dict[k][2], tail_list])
            key_basic_dict.update({k: a})
            key_beauty_dict.update({k: b})
            key_complex_dict.update({k: c})
        return key_basic_dict, key_beauty_dict, key_complex_dict

    # --------- --------- --------- --------- --------- --------- --------- --------- --------- #
    # tex
    def generate_tex_content(self, file_prefix: str, path_subsection: str, path_bib: str, path_combine: str) -> None:
        # for latex
        # add template for tex file
        add_bib_name = os.path.join(os.path.basename(path_bib), f"{file_prefix}-abbr.bib")
        add_tex_name = os.path.join(os.path.basename(path_subsection), f"{file_prefix}.tex")
        insert_part_one, insert_part_two = self._generate_tex_content(file_prefix, add_tex_name, add_bib_name)

        # write tex
        data_temp = insert_list_in_list(self.article_template_tex, insert_part_one, r"\\begin{document}", "before")
        data_temp = insert_list_in_list(data_temp, insert_part_two, r"\\begin{document}", "after")
        write_list(data_temp, f"{file_prefix}.tex", "w", os.path.join(path_combine, "tex"))
        return None

    @staticmethod
    def _generate_tex_content(file_prefix: str, add_tex_name: str, add_bib_name: str) -> tuple[list[str], list[str]]:
        if len(file_prefix) == 0:
            file_prefix = "file_prefix"

        part_one = [
            "\\date{" + "{}".format(time.strftime("%B %d, %Y")) + "}\n\n",
            "\\ifx \\fullpath \\undefined\n",
            "    \\addbibresource{" + os.path.join("..", add_bib_name) + "}\n",
            "\\else\n",
            "    \\addbibresource{" + os.path.join("\\fullpath", add_bib_name) + "}\n",
            "\\fi\n\n",
        ]
        part_two = [
            "\n",
            "% \\maketitle\n",
            "\\tableofcontents\n\n",
            "\\ifx \\fullpath \\undefined\n",
            "    \\input{" + os.path.join("..", add_tex_name) + "}\n",
            "\\else\n",
            "    \\input{" + os.path.join("\\fullpath", add_tex_name) + "}\n",
            "\\fi\n",
        ]
        return part_one, part_two
