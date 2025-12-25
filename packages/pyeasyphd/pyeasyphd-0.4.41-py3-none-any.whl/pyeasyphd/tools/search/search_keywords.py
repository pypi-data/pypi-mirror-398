import copy
import os
import re
from pathlib import Path
from typing import Any

from pyadvtools import generate_nested_dict, read_list, standard_path, write_list
from pybibtexer.tools.experiments_base import generate_standard_publisher_abbr_options_dict

from ...main import PandocMdTo
from ...utils.utils import html_head, html_style, html_tail
from .data import obtain_search_keywords
from .search_core import SearchResultsCore
from .utils import extract_information, temp_html_style


class Searchkeywords:
    """Search keywords in bibliography data.

    Args:
        path_storage (str): Path to storage directory for journals or conferences.
        path_output (str): Path to output directory for journals or conferences.
        options (dict): Configuration options.

    Attributes:
        path_storage (str): Path to storage directory.
        path_output (str): Path to output directory.
        options (dict): Configuration options.
        search_year_list (list[str]): list of years to search. Defaults to [].
    """

    def __init__(self, path_storage: str, path_output: str, options: dict[str, Any]) -> None:
        """Initialize Searchkeywords with storage and output paths.

        Args:
            path_storage (str): Path to storage directory.
            path_output (str): Path to output directory.
            options (dict[str, Any]): Configuration options.
        """
        self.path_storage = standard_path(path_storage)
        self.path_output = standard_path(path_output)

        options_ = {}
        options_["display_one_line_reference_note"] = True  # default is False
        options_["is_standardize_bib"] = False  # default is True
        options_["choose_abbr_zotero_save"] = "save"  # default is "save"
        options_["function_common_again"] = True  # default is True
        options_["function_common_again_for_abbr"] = False  # default is True
        options_["function_common_again_for_zotero"] = False  # default is True
        options_["function_common_again_for_save"] = False  # default is True
        options_["is_sort_entry_fields"] = True  # default is True
        options_["is_sort_blocks"] = True  # default is True
        options_["sort_entries_by_field_keys_reverse"] = True  # default is True
        options_["generate_entry_cite_keys"] = True  # default is True

        options_["default_keywords_dict"] = obtain_search_keywords()
        options_["default_search_field_list"] = ["title", "abstract"]
        options_.update(options)
        self.options = options_

        self.search_year_list = options.get("search_year_list", [])
        self._path_separate = self.path_output + "-Separate"

        self._path_statistic = self.path_output + "-Statistics"
        self._path_combine = self.path_output + "-Combine"

    def run(self) -> None:
        """Run the keyword search process."""
        all_dict = {}
        publisher_abbr_dict = generate_standard_publisher_abbr_options_dict(self.path_storage, self.options)
        for publisher in publisher_abbr_dict:
            for abbr in publisher_abbr_dict[publisher]:
                options = publisher_abbr_dict[publisher][abbr]

                path_storage = os.path.join(self.path_storage, publisher, abbr)
                path_output = os.path.join(self.path_output, publisher, abbr)
                entry_type_keyword_type_keyword_field_number_dict = SearchResultsCore(
                    path_storage, path_output, self._path_separate, abbr, options
                ).optimize(copy.deepcopy(self.search_year_list))

                all_dict.update({abbr: entry_type_keyword_type_keyword_field_number_dict})

        if not self.options.get("print_on_screen", False):
            extract_information(all_dict, self._path_statistic)

            print()
            self._generate_bib_html_for_publisher(publisher_abbr_dict, "bib")
            print()
            self._generate_bib_html_for_publisher(publisher_abbr_dict, "html")
            self._generate_link_to_bib_html_for_combine()

            print()
            self._pandoc_md_to_html_in_path_separate()
            self._generate_link_to_html_bib_for_separate()

        return None

    def _extract_files(
        self, publisher_abbr_dict: dict, ext: str = "html"
    ) -> dict[str, dict[str, dict[str, dict[str, list[str]]]]]:
        data_dict = {}
        for publisher in publisher_abbr_dict:
            for abbr in publisher_abbr_dict[publisher]:
                p = os.path.join(self.path_output, publisher, abbr)
                if not os.path.exists(p):
                    continue

                for entry_type in [f for f in os.listdir(p) if os.path.isdir(os.path.join(p, f))]:
                    if not (folders := [f for f in os.listdir(os.path.join(p, entry_type)) if "combine" in f.lower()]):
                        continue

                    for root, _, files in os.walk(os.path.join(p, entry_type, folders[0])):
                        for file in [f for f in files if f.endswith(ext)]:
                            (
                                data_dict.setdefault(file, {})
                                .setdefault(entry_type, {})
                                .setdefault(publisher, {})
                                .setdefault(abbr, [])
                                .append(os.path.join(root, file))
                            )
        return data_dict

    def _generate_bib_html_for_publisher(self, publisher_abbr_dict, ext: str = "html") -> None:
        data_dict = self._extract_files(publisher_abbr_dict, ext)
        for file in data_dict:
            basename = file.split(".")[0]
            for entry_type in data_dict[file]:
                for publisher in data_dict[file][entry_type]:
                    print(f"Generate {ext} for `{publisher}-{entry_type}-{basename}`")
                    data_list = []
                    for abbr in data_dict[file][entry_type][publisher]:
                        for i in range(ll := len(data_dict[file][entry_type][publisher][abbr])):
                            full_file = data_dict[file][entry_type][publisher][abbr][i]
                            temp_data_list = read_list(full_file, "r", None)
                            if ext == "html":
                                if mch := re.search(r"(<h3.*)</body>", "".join(temp_data_list), re.DOTALL):
                                    temp_data_list = mch.group(1).splitlines(keepends=True)

                            data_list.extend(temp_data_list)
                            if i < (ll - 1):
                                data_list.append("\n")
                        data_list.append("\n")

                    p = os.path.join(self._path_combine, entry_type, publisher, ext)
                    if ext == "html":
                        data_list_ = [html_head.format(basename)]
                        data_list_.extend(html_style)
                        data_list_.append(f'<h2 id="{publisher.upper()}">{publisher.upper()}</h2>\n')
                        data_list_.extend(data_list)
                        data_list_.append(html_tail)
                        write_list(data_list_, f"{basename}.{ext}", "w", p, False)

                    else:
                        write_list(data_list, f"{basename}.{ext}", "w", p, False)
        return None

    def _generate_link_to_bib_html_for_combine(self) -> None:
        nested_dict = generate_nested_dict(self._path_combine)

        for entry_type in nested_dict:
            data_dict = {}
            for publisher in nested_dict[entry_type]:
                for ext in nested_dict[entry_type][publisher]:
                    if ext == "html":
                        for file in nested_dict[entry_type][publisher][ext]:
                            data_dict.setdefault(publisher, []).append(file)

                    if ext == "bib":
                        for file in nested_dict[entry_type][publisher][ext]:
                            if not re.search(r"\-zotero", file):
                                continue

                            data_dict.setdefault(publisher, []).append(file)

            data_list = self._html_format(entry_type, data_dict, "Publishers", "combine")
            write_list(data_list, f"{entry_type.lower()}_links.html", "w", self._path_combine, False)
        return None

    def _pandoc_md_to_html_in_path_separate(self) -> None:
        mds = []
        for root, _, files in os.walk(self._path_separate):
            mds.extend([os.path.join(root, f) for f in files if f.endswith(".md")])

        for full_md in mds:
            print(f"pandoc md to html for `{full_md.split(self._path_separate)[-1]}`")
            full_html = full_md.replace("-md", "-html").replace(".md", ".html")
            PandocMdTo({}).pandoc_md_to_html(full_md, full_html, None, None, True)

    def _generate_link_to_html_bib_for_separate(self) -> None:
        for entry_type in (nested_dict := generate_nested_dict(self._path_separate)):
            data_dict = {}
            for keywords_type in nested_dict[entry_type]:
                for ext in nested_dict[entry_type][keywords_type]:
                    if not re.search(r"(\-html\-|\-bib\-zotero)", ext):
                        continue

                    for file in nested_dict[entry_type][keywords_type][ext]:
                        data_dict.setdefault(os.path.basename(file).split(".")[0], []).append(file)

            data_list = self._html_format(entry_type, data_dict, "Keywords", "separate")
            write_list(data_list, f"{entry_type.lower()}_links.html", "w", self._path_separate, False)
        return None

    @staticmethod
    def _html_format(entry_type, data_dict, name_flag, index):
        data_list = [html_head.format(f"{entry_type.title()} Links"), temp_html_style]
        data_list.append('\n<table border="1">\n')
        data_list.append(f"<caption>{entry_type.title()} Links</caption>\n")

        data_list.extend(["<thead>\n", "<tr>\n", f"<th>{name_flag}</th>\n", "</tr>\n", "</thead>\n"])

        x = '<td><a href="{}" target="_blank">{}</a></td>\n'
        data_list.append("<tbody>\n")
        for name in data_dict:
            data_list.append("<tr>\n")
            data_list.append(f"<td>{name}</td>\n")

            for f in data_dict[name]:
                folders = Path(f).parts[1:]
                if index == "combine":
                    data_list.append(x.format(f, folders[-1].split("-")[0].title() + ":" + f.split(".")[-1]))
                elif index == "separate":
                    data_list.append(x.format(f, folders[-2].split("-")[0].title() + ":" + f.split(".")[-1]))
            data_list.append("</tr>\n")
        data_list.append("</tbody>\n")

        data_list.append("</table>\n")
        data_list.append(html_tail)
        return data_list
