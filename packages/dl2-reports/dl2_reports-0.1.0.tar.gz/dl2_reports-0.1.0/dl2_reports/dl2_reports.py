from __future__ import annotations
from typing import Dict, List, Optional, Any
import pandas as pd
import json
import datetime
import gzip
import base64


class DL2Report:
    class Visual:
        def __init__(self, type: str, dataset_id: Optional[str] = None, **kwargs):
            self.type = type
            self.dataset_id = dataset_id
            self.props = kwargs

        def to_dict(self) -> Dict[str, Any]:
            d = {
                "type": self.type,
                "elementType": "visual"
            }
            if self.dataset_id:
                d["datasetId"] = self.dataset_id
            
            # Convert snake_case keys to camelCase for the JSON
            for k, v in self.props.items():
                camel_k = "".join(word.capitalize() if i > 0 else word for i, word in enumerate(k.split("_")))
                d[camel_k] = v
            return d

    class Layout:
        def __init__(self, direction: str = "row", **kwargs):
            self.type = "layout"
            self.direction = direction
            self.children: List[DL2Report.Layout | DL2Report.Visual] = []
            self.props = kwargs

        def add_visual(self, type: str, dataset_id: Optional[str] = None, **kwargs) -> DL2Report.Visual:
            visual = DL2Report.Visual(type, dataset_id, **kwargs)
            self.children.append(visual)
            return visual
        
        def add_layout(self, direction: str = "row", **kwargs) -> DL2Report.Layout:
            layout = DL2Report.Layout(direction, **kwargs)
            self.children.append(layout)
            return layout

        def add_kpi(self, dataset_id: str, value_column: str, title: str, **kwargs) -> DL2Report.Visual:
            return self.add_visual("kpi", dataset_id, value_column=value_column, title=title, **kwargs)

        def add_table(self, dataset_id: str, title: Optional[str] = None, **kwargs) -> DL2Report.Visual:
            return self.add_visual("table", dataset_id, title=title, **kwargs)

        def add_card(self, title: str, text: str, **kwargs) -> DL2Report.Visual:
            return self.add_visual("card", None, title=title, text=text, **kwargs)

        def add_pie(self, dataset_id: str, category_column: str, value_column: str, **kwargs) -> DL2Report.Visual:
            return self.add_visual("pie", dataset_id, category_column=category_column, value_column=value_column, **kwargs)

        def add_bar(self, dataset_id: str, x_column: str, y_columns: List[str], stacked: bool = False, **kwargs) -> DL2Report.Visual:
            type = "stackedBar" if stacked else "clusteredBar"
            return self.add_visual(type, dataset_id, x_column=x_column, y_columns=y_columns, **kwargs)

        def add_scatter(self, dataset_id: str, x_column: str, y_column: str, **kwargs) -> DL2Report.Visual:
            return self.add_visual("scatter", dataset_id, x_column=x_column, y_column=y_column, **kwargs)

        def to_dict(self) -> Dict[str, Any]:
            d = {
                "type": "layout",
                "direction": self.direction,
                "children": [c.to_dict() for c in self.children]
            }
            for k, v in self.props.items():
                camel_k = "".join(word.capitalize() if i > 0 else word for i, word in enumerate(k.split("_")))
                d[camel_k] = v
            return d

    class Page:
        def __init__(self, title: str, description: Optional[str] = None):
            self.title = title
            self.description = description
            self.rows: List[DL2Report.Layout] = []

        def add_row(self, direction: str = "row", **kwargs) -> DL2Report.Layout:
            row = DL2Report.Layout(direction, **kwargs)
            self.rows.append(row)
            return row

        def to_dict(self) -> Dict[str, Any]:
            d = {
                "title": self.title,
                "rows": [r.to_dict() for r in self.rows]
            }
            if self.description:
                d["description"] = self.description
            return d

    def __init__(self, title: str, description: str = "", author: str = ""):
        self.title = title
        self.description = description
        self.author = author
        self.pages: List[DL2Report.Page] = []
        self.datasets: Dict[str, Dict[str, Any]] = {}
        self.compressed_datasets: Dict[str, str] = {}
        self.css_url = "https://cdn.jsdelivr.net/gh/kameronbrooks/datalys2-reporting@latest/dist/dl2-style.css"
        self.js_url = "https://cdn.jsdelivr.net/gh/kameronbrooks/datalys2-reporting@latest/dist/datalys2-reports.min.js"
        self.meta_tags: Dict[str, str] = {}

    def add_df(self, name: str, df: pd.DataFrame, format: str = "records", compress: bool = False) -> DL2Report:
        """
        Adds a DataFrame to the report.
        
        :param name: Name of the dataset.
        :param df: The DataFrame to add.
        :param format: Data format ('records' or 'table').
        :param compress: Whether to compress the data using gzip.
        :return: The DL2Report instance.
        """
        columns = df.columns.tolist()
        dtypes = []
        for dtype in df.dtypes:
            if pd.api.types.is_numeric_dtype(dtype):
                dtypes.append("number")
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                dtypes.append("date")
            else:
                dtypes.append("string")

        if format == "records":
            data = df.to_dict(orient="records")
        else:
            data = df.values.tolist()

        dataset_entry = {
            "id": name,
            "format": format,
            "columns": columns,
            "dtypes": dtypes,
            "data": data
        }

        if compress:
            # Convert data to JSON string, then gzip, then base64
            json_data = json.dumps(data)
            compressed = gzip.compress(json_data.encode("utf-8"))
            b64_data = base64.b64encode(compressed).decode("utf-8")
            
            script_id = f"compressed-data-{name}"
            self.compressed_datasets[script_id] = b64_data
            
            dataset_entry["compression"] = "gzip"
            dataset_entry["compressedData"] = script_id
            dataset_entry["data"] = []
            
            # Enable GC for compressed data
            self.set_meta("gc-compressed-data", "true")

        self.datasets[name] = dataset_entry
        return self

    def add_page(self, title: str, description: Optional[str] = None) -> DL2Report.Page:
        page = DL2Report.Page(title, description)
        self.pages.append(page)
        return page

    def set_meta(self, name: str, content: str) -> DL2Report:
        self.meta_tags[name] = content
        return self

    def compile(self) -> str:
        report_data = {
            "pages": [p.to_dict() for p in self.pages],
            "datasets": self.datasets
        }
        report_data_json = json.dumps(report_data, indent=4)

        meta_html = ""
        for name, content in self.meta_tags.items():
            meta_html += f'    <meta name="{name}" content="{content}">\n'

        compressed_scripts = ""
        for script_id, b64_data in self.compressed_datasets.items():
            compressed_scripts += f'    <script id="{script_id}" type="text/b64-gzip">{b64_data}</script>\n'

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.title}</title>
    <meta name="description" content="{self.description}">
    <meta name="author" content="{self.author}">
    <meta name="last-updated" content="{datetime.datetime.now().isoformat()}">
{meta_html}
    <link rel="stylesheet" href="{self.css_url}">
</head>
<body>
{compressed_scripts}
    <div id="root"></div>
    <script id="report-data" type="application/json">
{report_data_json}
    </script>
    <script src="{self.js_url}"></script>
</body>
</html>"""
        return html

    def save(self, filename: str):
        with open(filename, "w", encoding="utf-8") as f:
            f.write(self.compile())
