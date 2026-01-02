"""Polars Extras"""

from __future__ import annotations

import polars as pl


def sort_frame(
    data: pl.DataFrame,
    by: str | list[str],
    descending: bool | list[bool] = False,
    nulls_last: bool | list[bool] = False,
) -> pl.DataFrame:
    regex_range = (
        r"\s*([\[\(])\s*([+-]?\d+(?:\.\d+)?|inf|-inf|\+inf)\s*,\s*([+-]?\d+(?:\.\d+)?|inf|\+inf|-inf)\s*([\]\)])\s*"
    )

    if isinstance(by, str):
        by = [by]

    if isinstance(descending, bool):
        by_desc = [descending for _ in by]
    else:
        by_desc = descending

    if isinstance(nulls_last, bool):
        by_nulls_last = [nulls_last for _ in by]
    else:
        by_nulls_last = nulls_last

    assert len(by) == len(by_desc) == len(by_nulls_last)

    sort_by = []

    f_order = []

    for f in by:
        if data[f].dtype == pl.Categorical or data[f].dtype == pl.String:
            sort_series = data[f].cast(pl.String).str.extract(regex_range, 2).cast(pl.Float64)
            if not sort_series.is_null().all():
                data = data.with_columns(sort_series.alias(f"__ORDERBY__{f}"))
                sort_by.append(f"__ORDERBY__{f}")
                f_order.append(f"__ORDERBY__{f}")
                continue
        sort_by.append(f)

    data = data.sort(by=sort_by, descending=by_desc, nulls_last=by_nulls_last)

    if len(f_order) > 0:
        return data.select(pl.selectors.exclude(f_order))
    else:
        return data
