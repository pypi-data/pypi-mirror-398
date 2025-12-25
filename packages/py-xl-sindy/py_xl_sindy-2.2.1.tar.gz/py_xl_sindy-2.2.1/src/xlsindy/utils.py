"""
Utility function for XLsindy not related to the main functionnality.
"""

import sys


def print_progress(
    iteration: int,
    total: int,
    prefix: str = "",
    suffix: str = "",
    decimals: int = 1,
    bar_length: int = 100,
):
    """
    Displays a progress bar in the terminal.

    Parameters:
        iteration (int): Current iteration.
        total (int): Total number of iterations.
        prefix (str, optional): Prefix for the progress bar.
        suffix (str, optional): Suffix for the progress bar.
        decimals (int, optional): Number of decimal places to show in the percentage.
        bar_length (int, optional): Length of the progress bar in characters.
    """
    format_str = "{0:." + str(decimals) + "f}"
    percentage_complete = format_str.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = "*" * filled_length + "-" * (bar_length - filled_length)
    (
        sys.stdout.write(
            "\r%s |%s| %s%s %s" % (prefix, bar, percentage_complete, "%", suffix)
        ),
    )
    sys.stdout.flush()
    if iteration == total:
        sys.stdout.write("\n")
        sys.stdout.flush()
