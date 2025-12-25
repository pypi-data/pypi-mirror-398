# pylint: disable=too-few-public-methods
"""A module for reporting the certificate details
depending on output configurations.
"""

import pandas as pd
from .formatters.html import format_report as format_html
from .formatters.json import format_report as format_json
from .formatters.yaml_ import format_report as format_yaml
from .formatters.text import format_report as format_text


class PandasReporter:
    """A class for producing report from Pandas DataFrame."""

    def __init__(self) -> None:
        """Initialize the PandasReporter object."""

    def report(self, data_frame: pd.DataFrame, out_format: str, opts: dict) -> None:
        """Write the data to the output file or stdout."""

        if opts.get("max_col_size"):
            data_frame = data_frame.map(
                lambda x: x[0 : opts["max_col_size"]] if isinstance(x, str) else x
            )

        output = self._format_data(data_frame, out_format, opts)

        self._write_output(output, opts)

    def _format_data(self, data_frame, out_format, opts) -> str:
        """Format the data frame based on the output format."""
        if out_format == "html":
            output = format_html(data_frame, opts)
        elif out_format == "json":
            output = format_json(data_frame, opts)
        elif out_format == "yaml":
            output = format_yaml(data_frame, opts)
        else:
            output = format_text(data_frame, opts)
        return output

    def _write_output(self, output: str, opts: dict) -> None:
        """Write the output to the file or stdout."""
        if opts.get("out_file"):
            with open(opts["out_file"], "w", encoding="utf-8") as (stream):
                stream.write(output)
        else:
            print(output)
