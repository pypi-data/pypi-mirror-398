from typing import Any

from pyadvtools import IterateSortDict
from pybibtexer.bib.bibtexparser import Entry, Library
from pybibtexer.main import PythonRunBib


def generate_library_by_filters(
    original_data: list[str] | str | Library,
    issue_or_month_flag: str | list[str],  # filter
    year_flag: str | list[str] = "current_year",  # filter
    options: dict[str, Any] | None = None,
) -> Library:
    """Generate a Library object from input data with given filters.

    Args:
        original_data (list[str] | str | Library): Input bibliography data.
        issue_or_month_flag (str | list[str]): Flag for issue/month selection.
        year_flag (str | list[str], optional): Flag for year selection. Defaults to "current_year".
        options (dict[str, Any], optional): Additional options. Defaults to {}.
        full_json_c (str, optional): JSON configuration for conference proceedings. Defaults to "".
        full_json_j (str, optional): JSON configuration for journal articles. Defaults to "".

    Returns:
        Library: Processed library object.
    """
    if options is None:
        options = {}

    _options = {}
    # convert_str_to_library
    _options["is_standardize_bib"] = False  # default is True
    # middlewares_str_to_library.py
    _options["is_display_implicit_comments"] = False  # default is True

    # convert_library_to_library.py
    _options["choose_abbr_zotero_save"] = "save"  # default is "save"
    # middlewares_library_to_library.py
    _options["generate_entry_cite_keys"] = False  # default is False
    _options["function_common_again"] = False  # default is True
    _options["function_common_again_for_abbr"] = False  # default is True
    _options["function_common_again_for_zotero"] = False  # default is True
    _options["function_common_again_for_save"] = False  # default is True

    # convert_library_to_str.py
    # middlewares_library_to_str.py
    _options["is_sort_entry_fields"] = True  # compulsory
    _options["is_sort_blocks"] = True  # compulsory
    _options["sort_entries_by_field_keys_reverse"] = True  # compulsory

    # convert_str_to_str.py
    _options["default_additional_field_list"] = []
    # middlewares_str_to_str.py
    _options["substitute_in_bib"] = False  # default is True

    _options.update(options)
    _python_bib = PythonRunBib(_options)

    # Generate nested entries dictionary
    entry_type_year_volume_number_month_entry_dict = _python_bib.parse_to_nested_entries_dict(original_data)
    old_dict = entry_type_year_volume_number_month_entry_dict

    # Filter by year flag
    new_dict = _obtain_year_flag_library(old_dict, year_flag)

    # Filter by year flag
    if not (isinstance(year_flag, str) and (year_flag.lower().strip() == "current_year")):
        issue_or_month_flag = "all_months"

    # Filter by issue flag
    if issue_or_month_flag in ["current_issue"]:
        return _obtain_issue_flag_library(new_dict, issue_or_month_flag)

    # Filter by month flag
    return _obtain_month_flag_library(new_dict, issue_or_month_flag)


def _obtain_year_flag_library(
    nested_entries: dict[str, dict[str, dict[str, dict[str, dict[str, list[Entry]]]]]],
    year_flag: str | list[str] = "current_year",
):
    """Filter dictionary by year flag.

    Args:
        nested_entries: Nested dictionary containing bibliography entries.
        year_flag (str | list[str], optional): Year filter flag. Defaults to "current_year".

    Returns:
        dict: Filtered dictionary by year.
    """
    new_dict = {}
    for entry_type in nested_entries:
        years = list(nested_entries[entry_type])

        # Update years
        if isinstance(year_flag, list):  # given_years
            years = sorted(set(years).intersection(set(year_flag)))
        elif year_flag.lower().strip() == "all_years":  # all_years
            years = years
        elif year_flag.lower().strip() == "current_year":  # current_year
            years = years[:1]
        else:
            years = []
            print(f"Unknown year flag: {year_flag}.")

        for year in years:
            new_dict.setdefault(entry_type, {}).update({year: nested_entries[entry_type][year]})

    return new_dict


def _obtain_issue_flag_library(
    nested_entries: dict[str, dict[str, dict[str, dict[str, dict[str, list[Entry]]]]]],
    issue_flag: str = "current_issue",
) -> Library:
    """Filter dictionary by issue flag.

    Args:
        nested_entries: Nested dictionary containing bibliography entries.
        issue_flag (str, optional): Issue filter flag. Defaults to "current_issue".

    Returns:
        Library: Filtered library object.
    """
    nested_entries = IterateSortDict(True).dict_update(nested_entries)

    entries = []
    for entry_type in nested_entries:
        for year in nested_entries[entry_type]:
            temp_dict = nested_entries[entry_type][year]

            # Article entries
            if entry_type.lower() == "article":
                volumes, numbers, months = [], [], []
                for volume in (volumes := list(temp_dict)):
                    for number in (numbers := list(temp_dict[volume])):
                        months = list(temp_dict[volume][number])
                        break
                    break

                if issue_flag == "current_issue":  # current volume, current issue, and current month
                    entries.extend(temp_dict[volumes[0]][numbers[0]][months[0]])
                else:
                    print(f"Unknown issue flag: {issue_flag}.")

            else:
                # Non-article entries
                for volume in temp_dict:
                    for number in temp_dict[volume]:
                        for month in temp_dict[volume][number]:
                            entries.extend(temp_dict[volume][number][month])

    return Library(entries)


def _obtain_month_flag_library(
    nested_entries: dict[str, dict[str, dict[str, dict[str, dict[str, list[Entry]]]]]],
    month_flag: str | list[str] = "current_month",
) -> Library:
    """Filter dictionary by month flag.

    Args:
        nested_entries: Nested dictionary containing bibliography entries.
        month_flag (str | list[str], optional): Month filter flag. Defaults to "current_month".

    Returns:
        Library: Filtered library object.
    """
    new_dict = {}
    for entry_type in nested_entries:
        for year in nested_entries[entry_type]:
            for volume in nested_entries[entry_type][year]:
                for number in nested_entries[entry_type][year][volume]:
                    for month in nested_entries[entry_type][year][volume][number]:
                        new_dict.setdefault(entry_type, {}).setdefault(year, {}).setdefault(month, {}).setdefault(
                            volume, {}
                        ).setdefault(number, []).extend(nested_entries[entry_type][year][volume][number][month])

    # Sort
    nested_entries = IterateSortDict(True).dict_update(new_dict)

    entries = []
    for entry_type in nested_entries:
        for year in nested_entries[entry_type]:
            temp_dict = nested_entries[entry_type][year]
            default_months = list(temp_dict)

            # Update month
            new_months = []
            if month_flag == "current_month":  # current_month
                new_months = default_months[:1]
            elif month_flag == "all_months":  # all months
                new_months = default_months
            else:
                print(f"Unknown month flag: {month_flag}.")

            # Filter by month
            for month in new_months:
                for volume in temp_dict[month]:
                    for number in temp_dict[month][volume]:
                        entries.extend(temp_dict[month][volume][number])

    return Library(entries)
