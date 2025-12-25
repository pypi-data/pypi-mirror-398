import datetime
import os
import re

from pyadvtools import combine_content_in_list, read_list, write_list

html_head = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{}</title>
"""

html_style = """  <style>
    html {font-size: 22px;}
    body {margin: 0 auto; max-width: 76em;}
    #copyID {font-size: 18px;}
  </style>
  <script>
    function copy(element) {
      if (element.type == "button"){
      element.type="text";
      }
      element.style.color="black";
      element.style.backgroundColor="#C7EDCC";
      element.select();
      element.setSelectionRange(0, 99999);
      navigator.clipboard.writeText(element.value);
      window.getSelection().removeAllRanges();
      element.type="button";
    }
  </script>
</head>
<body>
"""

html_tail = """
</body>
</html>
"""

textarea_header = '<textarea id="copyID" onclick="copy(this)" rows="16" cols="145">\n'
textarea_tail = "\n</textarea>"


def operate_on_generate_html(html_name: str) -> None:
    """Operate on generated HTML file to add styling and functionality.

    Args:
        html_name (str): Name of the HTML file to process.
    """
    if not (data_list := read_list(html_name, "r", None)):
        return None

    head_list = [html_head.format(os.path.basename(html_name).split(".")[0].strip()), html_style, "\n"]
    tail_list = [html_tail]

    content = "".join(data_list)
    content = content.replace("<pre><code>", textarea_header).replace("</code></pre>", textarea_tail)
    for i in re.findall(r"<li>(.*?)<details>", content, re.DOTALL):
        content = content.replace(rf"<li>{i}<details>", f"<li><details>\n<summary>\n{i.strip()}\n</summary>")
    data_list = combine_content_in_list([head_list, [content], tail_list])
    write_list(data_list, html_name, "w", None, False)
    return None


def is_last_week_of_month():
    """Check if today's date falls in the last week of the current month.

    Returns:
        bool: True if today is in the last week of the month, False otherwise.
    """
    # Get today's date
    today = datetime.date.today()

    # Calculate the last day of the current month
    # First, find the first day of next month
    if today.month == 12:
        next_month = datetime.date(today.year + 1, 1, 1)
    else:
        next_month = datetime.date(today.year, today.month + 1, 1)

    # Subtract one day to get the last day of the current month
    last_day_of_month = next_month - datetime.timedelta(days=1)

    # Calculate the week number of today and the last day of the month
    # Using isocalendar() which returns (year, week number, weekday)
    today_week = today.isocalendar()[1]
    last_day_week = last_day_of_month.isocalendar()[1]

    # For December, the week number might roll over to next year
    # If so, we need to adjust the comparison
    if today.month == 12 and today_week < last_day_week:
        # This handles the case where the last week of December is actually
        # the first week of the next year in the ISO calendar
        return True

    # Check if we're in the same week as the last day of the month
    return today_week == last_day_week
