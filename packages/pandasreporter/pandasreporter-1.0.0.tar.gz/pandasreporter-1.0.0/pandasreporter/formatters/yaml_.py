"""A module for formatting data frames as YAML string."""

import yaml


def format_report(data_frame, opts) -> str:  # pylint: disable=unused-argument
    """Return the YAML representation of the data frame."""
    return yaml.dump(data_frame.to_dict(orient="records"), default_flow_style=False)
