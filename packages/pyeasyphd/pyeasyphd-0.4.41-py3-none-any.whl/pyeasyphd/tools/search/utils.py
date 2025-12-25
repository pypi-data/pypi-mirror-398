import os
import re

from pyadvtools import IterateSortDict, is_list_contain_list_contain_str, is_list_contain_str, write_list


def switch_keywords_list(xx: list[str] | list[list[str]]) -> tuple[list[list[str]], str]:
    """Switch keyword list format and generate combined keywords string.

    Args:
        xx (list[str] | list[list[str]]): Input keyword list or nested keyword list.
            Examples: ["evolutionary", "algorithm"] or [["evolution"], ["evolutionary"]]

    Returns:
        tuple[list[list[str]], str]: Tuple containing:
            - List of keyword lists with regex word boundaries
            - Combined keywords string for file naming
    """
    yyy: list[list[str]] = [[]]

    if is_list_contain_str(xx):
        yyy = [[rf"\b{x}\b" for x in xx]]
    elif is_list_contain_list_contain_str(xx):
        if len(xx) == 1:
            yyy = [[rf"\b{x}\b" for x in xx[0]]]
        elif len(xx) == 2:
            yyy = [[rf"\b{x}\b" for x in xx[0]], [rf"\b{x}\b" for x in xx[1]]]
        else:
            print(f"Not standard keywords: {xx}")
            return yyy, ""
    else:
        return yyy, ""

    combine_keywords = "_and_".join(yyy[0])
    if len(yyy) == 2:
        combine_keywords += "_without_{}".format("_and_".join(yyy[1]))

    # ['evol(?:ution|utionary) strateg(?:y|ies)', 'population(?:| |-)based', 'network(?:|s)']
    # '\bevol(?:ution|utionary) strateg(?:y|ies)\b_and_\bpopulation(?:| |-)based\b_and_\bnetwork(?:|s)\b'
    combine_keywords = combine_keywords.replace(r"\b", "")
    # 'evol(?:ution|utionary) strateg(?:y|ies)_and_population(?:| |-)based_and_network(?:|s)'
    combine_keywords = re.sub(r"\(\?:[\w\s\-|]*\) ", "0 ", combine_keywords)
    # 'evol0 strateg(?:y|ies)_and_population(?:| |-)based_and_network(?:|s)'
    combine_keywords = re.sub(r"\(\?:[\w\s\-|]*\)$", "1", combine_keywords)
    # 'evol0 strateg(?:y|ies)_and_population(?:| |-)based_and_network1'
    combine_keywords = re.sub(r"\(\?:[\w\s\-|]*\)_", "2_", combine_keywords)
    # 'evol0 strateg2_and_population(?:| |-)based_and_network1'
    combine_keywords = re.sub(r"\(\?:[\w\s\-|]*\)", "3", combine_keywords)
    # 'evol0 strateg2_and_population3based_and_network1'
    combine_keywords = combine_keywords.replace("/", "4")
    combine_keywords = combine_keywords.replace(" ", "5")
    # 'evol05strateg2_and_population3based_and_network1'
    return yyy, combine_keywords


def combine_keywords_for_title(combine_keywords: str) -> str:
    """Convert combined keywords string to human-readable title format.

    Args:
        combine_keywords (str): Combined keywords string with special characters.

    Returns:
        str: Human-readable title format with proper spacing and punctuation.
    """
    combine_keywords = combine_keywords.replace("_without_", " without ")
    combine_keywords = combine_keywords.replace("_and_", "; ")
    combine_keywords = combine_keywords.replace("0", "")
    combine_keywords = combine_keywords.replace("1", "")
    combine_keywords = combine_keywords.replace("2", "")
    combine_keywords = combine_keywords.replace("3", "-")
    combine_keywords = combine_keywords.replace("4", "/")  #
    combine_keywords = combine_keywords.replace("5", " ")
    return combine_keywords


def combine_keywords_for_file_name(combine_keywords: str) -> str:
    """Convert combined keywords string to valid file name format.

    Args:
        combine_keywords (str): Combined keywords string.

    Returns:
        str: File name safe string with underscores and hyphens.
    """
    combine_keywords = combine_keywords_for_title(combine_keywords)
    combine_keywords = combine_keywords.replace("/", "-")
    combine_keywords = combine_keywords.replace("; ", "_and_")
    combine_keywords = combine_keywords.replace(" ", "_")
    return combine_keywords


def switch_keywords_type(keywords_type: str) -> str:
    """Normalize keywords type string for consistent formatting.

    Args:
        keywords_type (str): Keywords type string to normalize.

    Returns:
        str: Normalized keywords type with consistent separators.
    """
    keywords_type = keywords_type.replace("/", "-")
    keywords_type = keywords_type.replace(" ", "_")
    keywords_type = re.sub(r"-+", "-", keywords_type)
    keywords_type = re.sub(r"_+", "_", keywords_type)
    return keywords_type.strip()


def keywords_type_for_title(keywords_type: str) -> str:
    """Convert keywords type string to title format.

    Args:
        keywords_type (str): Keywords type string with underscores.

    Returns:
        str: Title format with spaces instead of underscores.
    """
    keywords_type = keywords_type.replace("_", " ")
    return keywords_type.strip()


def extract_information(old_dict: dict[str, dict[str, dict[str, dict[str, dict[str, int]]]]], path_output: str) -> None:
    """Extract and organize search information into markdown tables.

    Args:
        old_dict (dict[str, dict[str, dict[str, dict[str, dict[str, int]]]]]): Nested dictionary containing search results.
        path_output (str): Output directory path for generated markdown files.
    """
    new_dict: dict[str, dict[str, dict[str, dict[str, dict[str, int]]]]] = {}

    for abbr in old_dict:
        for entry_type in old_dict[abbr]:
            for keyword_type in old_dict[abbr][entry_type]:
                for keyword in old_dict[abbr][entry_type][keyword_type]:
                    for field in old_dict[abbr][entry_type][keyword_type][keyword]:
                        no = old_dict[abbr][entry_type][keyword_type][keyword][field]
                        (
                            new_dict.setdefault(entry_type, {})
                            .setdefault(field, {})
                            .setdefault(keyword_type, {})
                            .setdefault(keyword, {})
                            .update({abbr: no})
                        )

    new_dict = IterateSortDict(False).dict_update(new_dict)

    for entry_type in new_dict:
        for field in new_dict[entry_type]:
            data_list = []
            for keyword_type in new_dict[entry_type][field]:
                for keyword in new_dict[entry_type][field][keyword_type]:
                    abbr_list = sorted(new_dict[entry_type][field][keyword_type][keyword].keys())
                    num_list = [new_dict[entry_type][field][keyword_type][keyword][abbr] for abbr in abbr_list]

                    a = f"|Keywords Types|Keywords|{'|'.join(list(abbr_list))}|\n"
                    if a not in data_list:
                        data_list.append(a)

                    b = f"|-|-|{'|'.join(['-' for _ in abbr_list])}|\n"
                    if b not in data_list:
                        data_list.append(b)

                    keyword = combine_keywords_for_file_name(keyword)
                    data_list.append(f"|{keyword_type}|{keyword}|{'|'.join([str(n) for n in num_list])}|\n")

            write_list(data_list, f"{field}-keywords_count.md", "w", os.path.join(path_output, entry_type), False)


temp_html_style = """  <style>
    html {font-size: 19px;}
    body {margin: 0 auto; max-width: 22em;}
    table {
      border-collapse: collapse;
      border: 2px solid rgb(200,200,200);
      letter-spacing: 1px;
      font-size: 0.8rem;
    }
    td, th {
      border: 1px solid rgb(190,190,190);
      padding: 10px 20px;
    }
    td {text-align: center;}
    caption {padding: 12px;}
  </style>
</head>
<body>
"""


if __name__ == "__main__":
    pass
