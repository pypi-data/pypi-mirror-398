# DateTree

**DateTree** is a high-level Python utility for managing, filtering, and querying collections of dates stored in a **Red Black Tree (RBTree)**.

It provides a clean, expressive API for adding date ranges, filtering by calendar fields, and performing efficient date queries, while guaranteeing predictable performance and sorted traversal.

---

## Why DateTree?

DateTree is useful when you need to:

- Store large collections of dates efficiently
- Perform frequent date-based queries (year, month, day)
- Filter dates deterministically and in sorted order
- Enforce constraints like allowed days of the week
- Avoid ad-hoc list filtering or repeated date generation

Dates are stored as **keys** in an RBTree, giving strong performance guarantees and deterministic behavior.

---

## Features

- Store dates in a balanced Red Black Tree
- Add single dates or inclusive date ranges
- Delete individual dates or ranges of dates
- Filter dates by:
  - year
  - month
  - day
  - combinations of the above
- Include or exclude specific days of the week
- Efficient range queries
- Sorted traversal
- Explicit, exception-driven error handling

---

## Basic Usage

This example demonstrates the most common workflow:  
include days of the week, add a date range, and filter results.

```python
from datetime import date
from bintrees import RBTree
from date_tree.date_tree import DateTree

tree = RBTree()
builder = DateTree(tree, date_obj="example")

# Include all days of the week
builder.include_days_of_week(include_all=True)

# Add an inclusive date range
builder.add_dates(date(2025, 1, 1), date(2025, 1, 31))

# Filter dates in January 2025
filtered = builder.filter_dates(month=1, year=2025)
```

## Installation

Install from PyPI:

```bash
pip install date-tree