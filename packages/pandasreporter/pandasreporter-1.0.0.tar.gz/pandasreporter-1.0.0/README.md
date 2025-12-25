<img align="right" src="https://raw.github.com/cliffano/pandas-reporter/main/avatar.jpg" alt="Avatar"/>

[![Build Status](https://github.com/cliffano/pandas-reporter/workflows/CI/badge.svg)](https://github.com/cliffano/pandas-reporter/actions?query=workflow%3ACI)
[![Code Scanning Status](https://github.com/cliffano/pandas-reporter/workflows/CodeQL/badge.svg)](https://github.com/cliffano/pandas-reporter/actions?query=workflow%3ACodeQL)
[![Dependencies Status](https://img.shields.io/librariesio/release/pypi/pandasreporter)](https://libraries.io/pypi/pandasreporter)
[![Security Status](https://snyk.io/test/github/cliffano/pandas-reporter/badge.svg)](https://snyk.io/test/github/cliffano/pandas-reporter)
[![Published Version](https://img.shields.io/pypi/v/pandasreporter.svg)](https://pypi.python.org/pypi/pandasreporter)
<br/>

Pandas Reporter
---------------

Pandas Reporter is a report builder for Pandas DataFrame. It generates HTML, JSON, text, or YAML report containing the data in the data frame.

Installation
------------

    pip3 install pandasreporter

Usage
-----

Create pandasreporter object and run it:

    from pandasreporter import PandasReporter

    # Prepare your data frame
    data = {
        "Name": ["Barkley", "Pippen", "Robinson"],
        "DOB": ["19630220", "19650925", "19650806"],
        "City": ["Philadelphia", "Chicago", "San Antonio"],
    }
    data_frame = pd.DataFrame(data)

    pandas_reporter = PandasReporter()
    _opts = {
        "title": "Pandas Report",
        "generator": "Pandas Reporter",
        "rows_styler": <rows_styler_function>,
        "max_col_size": 80,
    }

    pandas_reporter.report(
        data_frame,
        "html", # other formatters: json, text, or yaml
        _opts,
    )

Configuration
-------------

These are the optional properties that you can use with `pandasreporter.report`.
Some example report files are available on [examples](examples) folder.

| Opt | Type | Description | Example | Formatter |
|-----|------|-------------|---------|----------|
| `max_col_size` | Number | Maximum value length | `80` | All |
| `title` | String | HTML report title value | `Pandas Report` | `html` |
| `generator` | String | HTML report generator meta | `Pandas Reporter` | `html` |
| `rows_styler` | Function | Data row styler | | `html` |

### HTML Rows Styler

Rows styler can be used to apply style to each of the table rows in HTML report.

Here's an example rows styler function which checks a row's "Expiry Date" column value against current date and a threshold date, and add background-color style accordingly:

    def rows_styler(row):
        today = pd.Timestamp.today()
        threshold_date = today + pd.DateOffset(days=self.expiry_threshold_in_days)
        if row["Expiry Date"] <= today:
            style = ["background-color: LightPink"] * len(row)
        elif row["Expiry Date"] <= threshold_date:
            style = ["background-color: LightYellow"] * len(row)
        else:
            style = ["background-color: LightGreen"] * len(row)
        return style

Colophon
--------

[Developer's Guide](https://cliffano.github.io/developers_guide.html#python)

Build reports:

* [Lint report](https://cliffano.github.io/pandas-reporter/lint/pylint/index.html)
* [Code complexity report](https://cliffano.github.io/pandas-reporter/complexity/radon/index.html)
* [Unit tests report](https://cliffano.github.io/pandas-reporter/test/pytest/index.html)
* [Test coverage report](https://cliffano.github.io/pandas-reporter/coverage/coverage/index.html)
* [Integration tests report](https://cliffano.github.io/pandas-reporter/test-integration/pytest/index.html)
* [API Documentation](https://cliffano.github.io/pandas-reporter/doc/sphinx/index.html)
