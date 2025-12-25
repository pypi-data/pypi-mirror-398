import json
import os
import subprocess
from datetime import datetime

from pyadvtools import standard_path


class PaperLinksGenerator:
    """Generate markdown files with paper links from JSON data."""

    def __init__(
        self,
        full_json_c: str,
        full_json_j: str,
        full_json_k: str,
        data_base_path: str,
        keywords_category_name: str = "",
        display_year_period: int = 10,
    ):
        """Initialize the generator with base paths.

        Args:
            full_json_c (str): Path to conferences JSON file.
            full_json_j (str): Path to journals JSON file.
            full_json_k (str): Path to keywords JSON file.
            data_base_path (str): Path to data files directory.
            keywords_category_name (str, optional): Category name for keywords. Defaults to "".
            display_year_period (int, optional): Number of years to display. Defaults to 10.
        """
        self.full_json_c = full_json_c
        self.full_json_j = full_json_j
        self.full_json_k = full_json_k

        self.data_base_path = standard_path(data_base_path)

        # Process keyword category name and load data
        keywords_category_name = keywords_category_name.lower().strip() if keywords_category_name else ""
        category_prefix = f"{keywords_category_name}_" if keywords_category_name else ""
        keywords_list = self._load_json_data("keywords").get(f"{category_prefix}keywords", [])

        # Validate data availability
        if not keywords_list or not keywords_category_name:
            keywords_list, keywords_category_name = [], ""

        self.keywords_category_name = keywords_category_name
        self.keywords_list: list[str] = keywords_list

        self.display_year_period = display_year_period

    def generate_yearly_links(self, cj: str, folder_name: str = os.path.join("data", "Yearly")) -> None:
        """Generate yearly markdown table with paper links.

        Args:
            cj (str): Publication type - 'conferences' or 'journals'.
            folder_name (str, optional): Output folder name. Defaults to "data/Yearly".
        """
        flags = self._get_yearly_flags(cj)
        folder_flags = [f"{f}_all_months" for f in flags]

        self._generate_links(cj, flags, folder_flags, folder_name)

    def generate_monthly_links(self, folder_name: str = os.path.join("data", "Monthly")) -> None:
        """Generate monthly markdown table with journal paper links.

        Args:
            folder_name (str, optional): Output folder name. Defaults to "data/Weekly".
        """
        cj = "Journals"

        flags = ["All Months"]
        folder_flags = [f"current_year_{f.replace(' ', '_').lower()}" for f in flags]

        self._generate_links(cj, flags, folder_flags, folder_name)

    def generate_weekly_links(self, folder_name: str = os.path.join("data", "Weekly")) -> None:
        """Generate weekly markdown table with journal paper links.

        Args:
            folder_name (str, optional): Output folder name. Defaults to "data/Weekly".
        """
        cj = "Journals"

        flags = ["Current Issue", "Current Month"]
        folder_flags = [f"current_year_{f.replace(' ', '_').lower()}" for f in flags]

        self._generate_links(cj, flags, folder_flags, folder_name)

    def _generate_links(self, cj, flags, folder_flags, folder_name) -> None:
        json_data = self._load_json_data(cj.lower())
        if not json_data:
            return None

        # publisher
        md_content = self._create_md_header_publisher(cj, flags)
        table_rows = self._generate_table_rows_publisher(json_data, cj, folder_flags, folder_name)
        if table_rows:
            md_content.extend(table_rows)
            self._write_md_file(md_content, folder_name, f"{cj}_Publisher.md")

        # abbr
        md_content = self._create_md_header_abbr(cj, flags)
        table_rows = self._generate_table_rows_abbr(json_data, cj, folder_flags, folder_name)
        if table_rows:
            md_content.extend(table_rows)
            self._write_md_file(md_content, folder_name, f"{cj}_Abbreviation.md")
            self._convert_md_to_html(folder_name, f"{cj}_Abbreviation")

        return None

    def _convert_md_to_html(self, folder_name, file_name):
        """Convert markdown file to HTML using pandoc."""
        base_path = os.path.join(self.data_base_path, f"{folder_name}")
        file_md = os.path.join(base_path, f"{file_name}.md")
        file_html = os.path.join(base_path, f"{file_name}.html")

        try:
            cmd = f"pandoc {file_md} -o {file_html}"
            subprocess.run(cmd.split(), check=True, capture_output=True, text=True)
            os.remove(file_md)
        except subprocess.CalledProcessError as e:
            print("Pandoc error in pandoc md to html:", e.stderr)

    def generate_ieee_early_access_links(self, folder_name: str = os.path.join("data", "Weekly")) -> None:
        """Generate markdown for IEEE Early Access papers."""
        md_content = [
            "# Papers from Early Access\n\n",
            "|Publisher|**Current Month Papers**|**All Papers**|\n",
            "|-|-|-|\n",
        ]

        links = self._get_ieee_links()
        if any(links):
            md_content.append(f"|IEEE|{links[0]}|{links[1]}|\n")
            self._write_md_file(md_content, folder_name, "Journals_Early_Access.md")

        return None

    def _load_json_data(self, file_name: str) -> dict:
        """Load JSON data from file."""
        try:
            if file_name.lower().strip() == "conferences":
                file_path = os.path.expanduser(self.full_json_c)
            elif file_name.lower().strip() == "journals":
                file_path = os.path.expanduser(self.full_json_j)
            elif file_name.lower().strip() == "keywords":
                file_path = os.path.expanduser(self.full_json_k)
            else:
                file_path = ""

            if not os.path.exists(file_path):
                return {}

            with open(file_path, encoding="utf-8", newline="\n") as file:
                return json.load(file)

        except Exception as e:
            print(f"Error loading {file_name}.json: {e}")
            return {}

    def _get_yearly_flags(self, cj: str) -> list[str]:
        """Get yearly flags based on publication type."""
        current_year = datetime.now().year
        years = [str(y) for y in range(current_year - self.display_year_period, current_year)]
        flags = sorted(years, reverse=True)

        if cj.lower() == "conferences":
            flags = [str(current_year), *flags]

        return flags

    def _create_md_header_publisher(self, cj: str, flags: list[str]) -> list[str]:
        """Create markdown table header."""
        return [
            f"# Papers from {cj.title()} of Different Publishers\n\n",
            f"| | {'|'.join(f'**{f}**' for f in flags)}|\n",
            f"|-|{'|'.join('-' for _ in flags)}|\n",
        ]

    def _create_md_header_abbr(self, cj: str, flags: list[str]) -> list[str]:
        """Create markdown table header."""
        return [
            f"# Papers from {cj.title()} of Different Publishers\n\n",
            f"| |Publishers|{'|'.join(f'**{f}**' for f in flags)}|\n",
            f"|-|-|{'|'.join('-' for _ in flags)}|\n",
        ]

    # publisher
    def _generate_table_rows_publisher(
        self, json_data: dict, cj: str, folder_flags: list[str], period: str
    ) -> list[str]:
        """Generate markdown table rows."""
        rows = []
        idx = 1

        for publisher in json_data:
            cells = self._get_link_cells_publisher(publisher, cj, folder_flags, period)
            if any(cells):
                rows.append(f"|{idx}|{'|'.join(cells)}|\n")
                idx += 1

        return rows

    def _get_link_cells_publisher(self, publisher: str, cj: str, folder_flags: list[str], period: str) -> list[str]:
        """Get link cells for a publisher."""
        cells = []

        for flag in folder_flags:
            link_path = os.path.join(period, cj, flag, publisher.lower(), f"{publisher.lower()}_link.html")
            full_path = os.path.join(self.data_base_path, link_path)

            if os.path.exists(full_path):
                cells.append(f"[{publisher}]({link_path})")
            else:
                cells.append("")

        return cells

    # abbr
    def _generate_table_rows_abbr(self, json_data: dict, cj: str, folder_flags: list[str], period: str) -> list[str]:
        """Generate markdown table rows."""
        rows = []
        idx = 1

        for publisher in json_data:
            if cj.lower() not in json_data[publisher]:
                continue

            for abbr in json_data[publisher][cj.lower()]:
                cells = self._get_link_cells_abbr(publisher, abbr, cj, folder_flags, period)
                if any(cells):
                    rows.append(f"|{idx}|{publisher}|{'|'.join(cells)}|\n")
                    idx += 1

        return rows

    def _get_link_cells_abbr(
        self, publisher: str, abbr: str, cj: str, folder_flags: list[str], period: str
    ) -> list[str]:
        """Get link cells for a abbr."""
        cells = []
        for flag in folder_flags:
            link_path = os.path.join(period, cj, flag, publisher.lower(), abbr, f"{abbr}.html")
            full_path = os.path.join(self.data_base_path, link_path)
            if os.path.exists(full_path):
                cells.append(f"[{abbr}]({link_path})")
            else:
                cells.append("")

        return cells

    def _get_ieee_links(self, folder_name: str = os.path.join("data", "Weekly")) -> list[str]:
        """Get IEEE Early Access links."""
        links = []
        link_paths = [
            os.path.join(folder_name, "Journals_Early_Access", "current_year_current_month", "ieee", "ieee_link.html"),
            os.path.join(folder_name, "Journals_Early_Access", "all_years_all_months", "ieee", "ieee_link.html"),
        ]

        for link_path in link_paths:
            full_path = os.path.join(self.data_base_path, link_path)
            if os.path.exists(full_path):
                links.append(f"[IEEE Early Access]({link_path})")
            else:
                links.append("")

        return links

    def _write_md_file(self, content: list[str], period: str, file_name: str) -> None:
        """Write markdown content to file."""
        if len(content) == 0:
            return None

        output_dir = os.path.join(self.data_base_path, period)
        os.makedirs(output_dir, exist_ok=True)

        output_file = os.path.join(output_dir, file_name)
        with open(output_file, "w", newline="\n") as f:
            f.writelines(content)
        print(f"Generated: {output_file}")

        return None

    def generate_keywords_links_weekly(self, cj: str, folder_name: str = os.path.join("data", "Weekly")):
        flags = ["Current Issue", "Current Month"]
        folder_flags = [f"current_year_{f.replace(' ', '_').lower()}" for f in flags]

        self._generate_keywords_links(cj, folder_name, flags, folder_flags)

    def generate_keywords_links_monthly(self, cj: str, folder_name: str = os.path.join("data", "Monthly")):
        flags = ["All Months"]
        folder_flags = [f"current_year_{f.replace(' ', '_').lower()}" for f in flags]

        self._generate_keywords_links(cj, folder_name, flags, folder_flags)

    def generate_keywords_links_yearly(self, cj: str, folder_name: str = os.path.join("data", "Yearly")):
        flags = self._get_yearly_flags(cj)
        folder_flags = [f"{f}_all_months" for f in flags]

        self._generate_keywords_links(cj, folder_name, flags, folder_flags)

    def _generate_keywords_links(self, cj: str, folder_name: str, flags: list[str], folder_flags: list[str]):
        json_data = self._load_json_data(cj.title())
        if not json_data:
            return None

        keyword_publisher_abbr = self._process_keywords(cj, json_data)

        all_data_list = ["# Keywords\n\n", "| |Keywords|Links|\n", "|-|-|-|\n"]
        idx = 1
        for keyword in self._default_or_customized_keywords(keyword_publisher_abbr):
            data_list = [
                f"# {keyword.title()}\n\n",
                "|Publishers|Abbreviations|" + "|".join(flags) + "|\n",
                "|-|-|" + "|".join(["-" for _ in flags]) + "|\n",
            ]

            for publisher in keyword_publisher_abbr[keyword]:
                for abbr in keyword_publisher_abbr[keyword][publisher]:
                    lines = []
                    for ff in folder_flags:
                        ll = os.path.join(folder_name, cj.title(), ff, publisher.lower(), abbr, f"{abbr}.html")
                        if os.path.exists(os.path.join(self.data_base_path, ll)):
                            lines.append(f"[Link]({ll})")
                        else:
                            lines.append("")

                    if any(lines):
                        data_list.append(f"|{publisher}|{abbr}|" + "|".join(lines) + "|\n")

            if len(data_list) == 3:
                continue

            self._write_md_file(
                data_list, os.path.join(folder_name, f"{cj.title()}_Keywords"), f"{keyword.replace(' ', '_')}.md"
            )

            # Pandoc
            self._convert_md_to_html_keyword(folder_name, cj, keyword)

            ll = os.path.join(folder_name, f"{cj.title()}_Keywords", f"{keyword.replace(' ', '_')}.html")
            all_data_list.append(f"|{idx}|{keyword}|[Link]({ll})|\n")

            idx += 1

        category_postfix = f"_{self.keywords_category_name.title()}" if self.keywords_category_name else ""
        self._write_md_file(all_data_list, f"{folder_name}", f"{cj.title()}_Keywords{category_postfix}.md")

    def _default_or_customized_keywords(self, json_data):
        keywords = list(json_data.keys())

        # Get and sort publication types
        if self.keywords_category_name and self.keywords_list:
            _keywords = []
            for keyword in self.keywords_list:
                if keyword in keywords:
                    _keywords.append(keyword)
            return _keywords
        else:
            # default
            return sorted(keywords)

    def _convert_md_to_html_keyword(self, folder_name, cj, keyword):
        """Convert markdown file to HTML using pandoc."""
        base_path = os.path.join(self.data_base_path, folder_name, f"{cj.title()}_Keywords")
        file_md = os.path.join(base_path, f"{keyword.replace(' ', '_')}.md")
        file_html = os.path.join(base_path, f"{keyword.replace(' ', '_')}.html")

        try:
            os.system(f"pandoc {file_md} -o {file_html}")
            os.remove(file_md)
        except Exception as e:
            print(f"Pandoc conversion error: {e}")

    def _process_keywords(self, cj: str, json_data: dict):
        keyword_publisher_abbr = {}

        for publisher in json_data:
            for abbr in json_data[publisher][cj.lower()]:
                keywords_dict = json_data[publisher][cj.lower()][abbr].get("keywords_dict", {})

                # Clean and sort keywords
                cleaned_keywords = {}
                for category, words in keywords_dict.items():
                    if category.strip():
                        sorted_words = sorted({word.strip() for word in words if word.strip()})
                        cleaned_keywords[category.strip()] = sorted_words

                # For category
                # Flatten keywords and remove duplicates
                all_keywords = []
                for category, words in cleaned_keywords.items():
                    all_keywords.extend(words)
                    all_keywords.append(category)
                all_keywords = sorted(set(all_keywords))

                for keyword in all_keywords:
                    keyword_publisher_abbr.setdefault(keyword, {}).setdefault(publisher, []).append(abbr)

        return keyword_publisher_abbr
