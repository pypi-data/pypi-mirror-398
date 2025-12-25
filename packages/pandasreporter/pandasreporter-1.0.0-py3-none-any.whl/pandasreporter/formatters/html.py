"""A module for formatting data frames as HTML."""

import re
from dominate import document
from dominate.tags import meta, link
from dominate.util import raw


def format_report(data_frame, opts) -> str:
    """Return the HTML page with table having data frame as content."""

    if opts.get("rows_styler"):
        styled_data_frame = data_frame.style.apply(
            opts["rows_styler"], axis=1
        ).set_table_attributes('class="table table-striped table-bordered table-hover"')
    else:
        styled_data_frame = data_frame.style.set_table_attributes(
            'class="table table-striped table-bordered table-hover"'
        )

    table = styled_data_frame.to_html(doctype_html=False, index=False)
    table = re.sub(r"col_heading", "text-center table-active col_heading", table)

    doc = document(title=opts.get("title", "Pandas Report"))
    with doc.head:
        meta(charset="utf-8")
        meta(name="generator", content=opts.get("generator", "Pandas Reporter"))
        link(
            rel="stylesheet",
            href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.6/dist/css/bootstrap.min.css",
        )
    doc.body.add(raw(table))
    return doc.render()
