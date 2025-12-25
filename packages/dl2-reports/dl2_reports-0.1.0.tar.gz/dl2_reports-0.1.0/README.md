# Datalys2 Reporting Python API

A Python library to build and compile interactive HTML reports using the Datalys2 Reporting framework.

## Installation

```bash
pip install dl2-reports
```

## Quick Start

```python
import pandas as pd
from dl2_reports import DL2Report

# Create a report
report = DL2Report(title="My Report")

# Add data
df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
report.add_df("my_data", df, compress=True)

# Add a page and visual
page = report.add_page("Overview")
page.add_row().add_kpi("my_data", value_column="A", title="Metric A")

# Save to HTML
report.save("report.html")
```

## Documentation

For detailed information on available visuals and configuration, see [DOCUMENTATION.md](DOCUMENTATION.md).
