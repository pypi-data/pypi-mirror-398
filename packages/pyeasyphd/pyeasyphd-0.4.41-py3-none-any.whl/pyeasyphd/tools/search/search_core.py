import copy
import os
import re
import shutil
from typing import Any

from pyadvtools import (
    IterateCombineExtendDict,
    IterateUpdateDict,
    combine_content_in_list,
    pairwise_combine_in_list,
    read_list,
    sort_int_str,
    standard_path,
    write_list,
)
from pybibtexer.bib.bibtexparser import Library
from pybibtexer.main import PythonRunBib

from ...main import BasicInput
from .search_base import SearchInitialResult
from .search_writers import WriteAbbrCombinedResults
from .utils import keywords_type_for_title, switch_keywords_list, switch_keywords_type


class SearchResultsCore(BasicInput):
    """Core class for generating tex, md, html, and pdf from search results.

    Args:
        path_storage (str): Path to storage directory for bibliography files.
        path_output (str): Path to output directory for generated files.
        path_separate (str): Path to separate directory for individual results.
        j_conf_abbr (str): Abbreviation of journal or conference.
        options (dict): Configuration options.

    Attributes:
        path_storage (str): Path to storage directory.
        path_output (str): Path to output directory.
        path_separate (str): Path to separate directory.
        j_conf_abbr (str): Abbreviation of journal or conference.
        is_standard_bib_file_name (bool): Whether the bib file name follows standard format.
        keywords_type_list (list[str]): list of keyword types to search.
        keywords_dict (dict): dictionary of keywords for searching.
        delete_redundant_files (bool): Whether to delete redundant files after processing.
        generate_basic_md (bool): Whether to generate basic markdown files.
        generate_beauty_md (bool): Whether to generate beautiful markdown files.
        generate_complex_md (bool): Whether to generate complex markdown files.
        generate_tex (bool): Whether to generate LaTeX files.
        first_field_second_keywords (bool): Whether to search fields first, then keywords.
        deepcopy_library_for_every_field (bool): Whether to deep copy library for every field.
        deepcopy_library_for_every_keywords (bool): Whether to deep copy library for every keywords.
    """

    def __init__(
        self, path_storage: str, path_output: str, path_separate: str, j_conf_abbr: str, options: dict[str, Any]
    ) -> None:
        """Initialize SearchResultsCore with paths and configuration.

        Args:
            path_storage (str): Path to storage directory for bibliography files.
            path_output (str): Path to output directory for generated files.
            path_separate (str): Path to separate directory for individual results.
            j_conf_abbr (str): Abbreviation of journal or conference.
            options (dict[str, Any]): Configuration options.
        """
        super().__init__(options)
        self.path_storage: str = standard_path(path_storage)
        self.path_output: str = standard_path(path_output)
        self.path_separate: str = standard_path(path_separate)
        self.j_conf_abbr: str = j_conf_abbr

        # for bib
        # Whether the bib file name is standard, such as `TEVC_2023.bib`.
        self.is_standard_bib_file_name: bool = options.get("is_standard_bib_file_name", True)  # TEVC_2023.bib

        # for search
        self.keywords_dict = options.get("default_keywords_dict", {})
        if temp := options.get("keywords_dict", []):
            self.keywords_dict = temp

        if keywords_type_list := options.get("keywords_type_list", []):
            self.keywords_dict = {k: v for k, v in self.keywords_dict.items() if k in keywords_type_list}

        self.keywords_dict = {switch_keywords_type(k): v for k, v in self.keywords_dict.items()}

        self.search_field_list = options.get("default_search_field_list", ["title", "abstract"])
        if temp := options.get("search_field_list", []):
            self.search_field_list = temp

        # for pandoc
        self.delete_redundant_files: bool = options.get("delete_redundant_files", True)

        # for md
        self.generate_basic_md: bool = options.get("generate_basic_md", False)
        self.generate_beauty_md: bool = options.get("generate_beauty_md", False)
        self.generate_complex_md: bool = options.get("generate_complex_md", True)

        # for tex
        self.generate_tex = options.get("generate_tex", False)

        # for search
        self.first_field_second_keywords = options.get("first_field_second_keywords", True)
        self.deepcopy_library_for_every_field = options.get("deepcopy_library_for_every_field", False)
        self.deepcopy_library_for_every_keywords = options.get("deepcopy_library_for_every_keywords", False)

        # for bib
        self._python_bib = PythonRunBib(options)

    def optimize(self, search_year_list: list[str] = []) -> dict[str, dict[str, dict[str, dict[str, int]]]]:
        """Optimize search results for given years.

        Args:
            search_year_list (list[str], optional): list of years to search. Defaults to [].

        Returns:
            dict[str, dict[str, dict[str, dict[str, int]]]]: Nested dictionary containing search results.
        """
        search_year_list = list({str(i) for i in search_year_list})

        data_list = self._obtain_full_files_data(self.path_storage, "bib", search_year_list)

        entry_type_keyword_type_keyword_field_number_dict = self.optimize_core(data_list, search_year_list)
        return entry_type_keyword_type_keyword_field_number_dict

    def _obtain_full_files_data(
        self, path_storage: str, extension: str, search_year_list: list[str] | None = None
    ) -> list[str]:
        """Obtain data from all files with specified extension in storage path.

        Args:
            path_storage (str): Path to storage directory.
            extension (str): File extension to search for.
            search_year_list (list[str], optional): list of years to filter by. Defaults to [].

        Returns:
            list[str]: Combined content from all matching files.
        """
        if search_year_list is None:
            search_year_list = []

        regex = None
        if self.is_standard_bib_file_name and search_year_list:
            regex = re.compile(f"({'|'.join(search_year_list)})")

        file_list = []
        for root, _, files in os.walk(path_storage, topdown=True):
            files = [f for f in files if f.endswith(f".{extension}")]

            if regex:
                files = [f for f in files if regex.search(f)]

            file_list.extend([os.path.join(root, f) for f in files])

        return combine_content_in_list([read_list(f, "r") for f in sort_int_str(file_list)], None)

    def optimize_core(self, data_list: list[str], search_year_list) -> dict[str, dict[str, dict[str, dict[str, int]]]]:
        """Core optimization logic for processing bibliography data.

        Args:
            data_list (list[str]): list of bibliography data strings.
            search_year_list: list of years to search.

        Returns:
            dict[str, dict[str, dict[str, dict[str, int]]]]: Nested dictionary containing search results.
        """
        print("\n" + "*" * 9 + f" Search in {self.j_conf_abbr} " + "*" * 9)

        entry_type_year_volume_number_month_entry_dict = self._python_bib.parse_to_nested_entries_dict(data_list)

        # generate standard bib and output
        entry_type_keyword_type_keyword_field_number_dict: dict[str, dict[str, dict[str, dict[str, int]]]] = {}
        for entry_type in entry_type_year_volume_number_month_entry_dict:
            # obtain search years
            year_list = list(entry_type_year_volume_number_month_entry_dict[entry_type].keys())
            if search_year_list:
                year_list = [y for y in year_list if y in search_year_list]
            year_list = sort_int_str(year_list, reverse=True)
            if not year_list:
                print("year_list is empty.")
                continue

            # output prefix
            output_prefix = "-".join([self.j_conf_abbr, year_list[-1], year_list[0]])

            # generate paths
            p_origin = os.path.join(self.path_output, entry_type, f"{output_prefix}-Origin")
            p_separate = os.path.join(self.path_separate, entry_type)
            p_combine = os.path.join(self.path_output, entry_type, f"{output_prefix}-Combine")

            # obtain library
            new_dict = {year: entry_type_year_volume_number_month_entry_dict[entry_type][year] for year in year_list}
            entries = IterateCombineExtendDict().dict_update(new_dict)
            library = Library(entries)

            # search, generate and save
            keyword_type_keyword_field_number_dict = {}
            for keywords_type in self.keywords_dict:
                library = copy.deepcopy(library)

                if self.first_field_second_keywords:
                    keyword_field_number_dict = self._optimize_fields_keyword(
                        keywords_type, library, output_prefix, p_origin, p_separate, p_combine
                    )
                else:
                    keyword_field_number_dict = self._optimize_keywords_field(
                        keywords_type, library, output_prefix, p_origin, p_separate, p_combine
                    )
                keyword_type_keyword_field_number_dict.update({keywords_type: keyword_field_number_dict})

            # collect results
            entry_type_keyword_type_keyword_field_number_dict.setdefault(entry_type, {}).update(
                keyword_type_keyword_field_number_dict
            )

        return entry_type_keyword_type_keyword_field_number_dict

    def _optimize_fields_keyword(self, keywords_type, library, output_prefix, p_origin, p_separate, p_combine):
        """Optimize search by fields first, then keywords.

        Args:
            keywords_type: Type of keywords to search.
            library: Bibliography library to search.
            output_prefix (str): Prefix for output files.
            p_origin (str): Path to origin directory.
            p_separate (str): Path to separate directory.
            p_combine (str): Path to combine directory.

        Returns:
            dict: dictionary containing keyword field numbers.
        """
        no_search_library = library

        keyword_field_number_dict_ = {}
        for field in self.search_field_list:
            keyword_field_number_dict, no_search_library = self.core_optimize(
                [field], keywords_type, no_search_library, output_prefix, p_origin, p_separate, p_combine
            )

            if self.deepcopy_library_for_every_field:
                no_search_library = copy.deepcopy(library)

            temp = keyword_field_number_dict
            keyword_field_number_dict_ = IterateUpdateDict().dict_update(keyword_field_number_dict_, temp)
        return keyword_field_number_dict_

    def _optimize_keywords_field(self, keywords_type, library, output_prefix, p_origin, p_separate, p_combine):
        """Optimize search by keywords first, then fields.

        Args:
            keywords_type: Type of keywords to search.
            library: Bibliography library to search.
            output_prefix (str): Prefix for output files.
            p_origin (str): Path to origin directory.
            p_separate (str): Path to separate directory.
            p_combine (str): Path to combine directory.

        Returns:
            dict: dictionary containing keyword field numbers.
        """
        no_search_library = library

        keyword_field_number_dict, no_search_library = self.core_optimize(
            self.search_field_list, keywords_type, no_search_library, output_prefix, p_origin, p_separate, p_combine
        )
        return keyword_field_number_dict

    def core_optimize(
        self,
        search_field_list: list[str],
        keywords_type,
        library: Library,
        output_prefix: str,
        p_origin: str,
        p_separate: str,
        p_combine: str,
    ) -> tuple[dict[str, dict[str, int]], Library]:
        """Core optimization method for processing search results.

        Args:
            search_field_list (list[str]): list of fields to search.
            keywords_type: Type of keywords to search.
            library (Library): Bibliography library to search.
            output_prefix (str): Prefix for output files.
            p_origin (str): Path to origin directory.
            p_separate (str): Path to separate directory.
            p_combine (str): Path to combine directory.

        Returns:
            tuple[dict[str, dict[str, int]], Library]: Tuple containing keyword field numbers and remaining library.
        """
        error_pandoc_md_md: list[str] = []
        save_field_data_dict: dict[str, list[list[str]]] = {}
        keyword_field_number_dict: dict[str, dict[str, int]] = {}

        no_search_library = library
        for keywords_list in self.keywords_dict[keywords_type]:
            print(f"{output_prefix}-{keywords_type}-search-{keywords_list}")
            keywords_list_list, combine_keyword = switch_keywords_list(keywords_list)

            # for initial results
            error_md, field_data_dict, field_number_dict, no_search_library = SearchInitialResult(
                copy.deepcopy(self.options)
            ).main(
                search_field_list,
                p_origin,
                no_search_library,
                keywords_type,
                keywords_list_list,
                combine_keyword,
                output_prefix,
                p_separate,
            )

            if self.deepcopy_library_for_every_keywords:
                no_search_library = copy.deepcopy(library)

            # collect error parts
            error_pandoc_md_md.extend(error_md)

            # collect data
            for field in field_data_dict:
                temp = pairwise_combine_in_list(save_field_data_dict.get(field, []), field_data_dict[field], "\n")
                save_field_data_dict.update({field: temp})

            # collect number
            keyword_field_number_dict.update({combine_keyword: field_number_dict})

        kws_type = keywords_type_for_title(keywords_type)
        flag = "-".join(search_field_list)

        # for error parts in pandoc markdown to markdown
        if error_pandoc_md_md:
            error_pandoc_md_md.insert(0, f"# Error in pandoc md to md for {kws_type}\n\n")
            write_list(error_pandoc_md_md, rf"{flag}_{output_prefix}_error_pandoc_md_md.md", "a", p_combine)

        # combine part
        # for combined results
        error_pandoc_md_pdf, error_pandoc_md_html = WriteAbbrCombinedResults(copy.deepcopy(self.options)).main(
            search_field_list, keywords_type, save_field_data_dict, p_combine
        )

        # for error parts in pandoc markdown to pdf
        if error_pandoc_md_pdf:
            error_pandoc_md_pdf.insert(0, f"# Error in pandoc md to pdf for {kws_type}\n\n")
            write_list(error_pandoc_md_pdf, rf"{flag}_{output_prefix}_error_pandoc_md_pdf.md", "a", p_combine)

        # for error parts in pandoc markdown to html
        if error_pandoc_md_html:
            error_pandoc_md_html.insert(0, f"# Error in pandoc md to html for {kws_type}\n\n")
            write_list(error_pandoc_md_html, rf"{flag}_{output_prefix}_error_pandoc_md_html.md", "a", p_combine)

        # delete redundant files
        if self.delete_redundant_files:
            self.delete_files(keywords_type, p_origin, p_separate, p_combine)

        return keyword_field_number_dict, no_search_library

    def delete_files(self, keywords_type: str, p_origin: str, p_separate: str, p_combine: str) -> None:
        """Delete redundant files after processing.

        Args:
            keywords_type (str): Type of keywords being processed.
            p_origin (str): Path to origin directory.
            p_separate (str): Path to separate directory.
            p_combine (str): Path to combine directory.
        """
        # for initial tex md bib
        if os.path.exists(p_origin):
            shutil.rmtree(p_origin)

        # for separate keywords
        delete_folder_list = []
        if not self.generate_basic_md:
            delete_folder_list.append("basic")
        if not self.generate_beauty_md:
            delete_folder_list.append("beauty")
        if not self.generate_complex_md:
            delete_folder_list.append("complex")

        for d in delete_folder_list:
            for field in self.search_field_list:
                path_delete = os.path.join(p_separate, keywords_type, rf"{field}-md-{d}")
                if os.path.exists(path_delete):
                    shutil.rmtree(path_delete)

        # for combine
        delete_folder_list = ["md"]
        if not self.generate_basic_md:
            delete_folder_list.append("md-basic")
        if not self.generate_beauty_md:
            delete_folder_list.append("md-beauty")
        if not self.generate_complex_md:
            delete_folder_list.append("md-complex")
        if not self.generate_tex:
            delete_folder_list.extend(["tex", "tex-subsection"])

        for d in delete_folder_list:
            path_delete = os.path.join(p_combine, f"{d}")
            if os.path.exists(path_delete):
                shutil.rmtree(path_delete)
