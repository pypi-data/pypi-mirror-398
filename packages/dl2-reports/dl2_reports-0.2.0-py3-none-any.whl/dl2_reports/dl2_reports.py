from __future__ import annotations
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
import json
import datetime
import gzip
import base64
import html

from .utilities import analytics



class DL2Report:
    class ReportTreeComponent:
        """
        Base class for components in the report tree.
        """
        def __init__(self):
            self.parent: Optional[Any] = None

        def get_report(self) -> Optional[DL2Report]:
            """
            Gets the parent DL2Report instance.
            
            :param self: Description
            :return: Description
            :rtype: DL2Report | None
            """
            if self.parent is None:
                raise ValueError("Component is not attached to a report.")
            if hasattr(self.parent, "get_report"):
                return self.parent.get_report()
            
            return None
    
    class Visual(ReportTreeComponent):
        def __init__(self, type: str, dataset_id: Optional[str] = None, **kwargs):
            super().__init__()
            self.type = type
            self.dataset_id = dataset_id
            self.other_elements: List[Dict[str, Any]] = []
            self.props = kwargs
        


        def add_element(self, type: str, **kwargs) -> DL2Report.Visual:
            """
            Adds a visual element (annotation) to the visual.
            
            Args:
                type: The type of element ('trend', 'xAxis', 'yAxis', 'marker', 'label').
                **kwargs: Additional properties for the element:
                    * **color** (str): Color of the element.
                    * **line_style** (str): 'solid', 'dashed', or 'dotted'.
                    * **line_width** (int): Width of the line.
                    * **label** (str): Text label for the element.
                    * **coefficients** (List[float]): For 'trend' type (e.g., [intercept, slope]).
                    * **value** (any): For 'xAxis', 'yAxis', 'marker', 'label' types.
                    * **size** (int): For 'marker' type.
                    * **shape** (str): For 'marker' type ('circle', 'square', 'triangle').
            
            Returns:
                DL2Report.Visual: The Visual instance.
            """
            element = {"visual_element_type": type}
            element.update(kwargs)
            self.other_elements.append(element)
            return self
        
        def add_trend(self, coefficients: (List[float] | None) = None, **kwargs) -> DL2Report.Visual:
            """
            Adds a trend line element to the visual.
            
            Args:
                coefficients: List of coefficients for the trend line (e.g., [intercept, slope]).
                **kwargs: Additional properties for the trend element:
                    * **color** (str): Color of the trend line.
                    * **line_style** (str): 'solid', 'dashed', or 'dotted'.
                    * **line_width** (int): Width of the line.
            
            Returns:
                DL2Report.Visual: The Visual instance.
            """

            # TODO: Only allow trends for certain visual types?

            element: Dict[str, Any] = {"visual_element_type": "trend", "coefficients": []}

            if coefficients is None or isinstance(coefficients, int):
                # Auto-calculate coefficients if not provided
                # if coefficients is an int, treat that as the degree
                degree = (coefficients-1) if isinstance(coefficients, int) else 1

                # get the columns from the visual props
                x_column = self.props.get("x_column", None)
                y_column = self.props.get("y_column", None)

                if x_column is None or y_column is None:
                    raise ValueError("Cannot auto-calculate trend coefficients without x_column and y_column in visual props.")
                
                report = self.get_report()
                if report is None:
                    raise ValueError("Cannot auto-calculate trend coefficients without a parent report.")
                
                dataset_id = self.dataset_id
                if dataset_id is None or dataset_id not in report.datasets:
                    raise ValueError("Cannot auto-calculate trend coefficients without a valid dataset_id in the visual.")
                
                dataset: Dict[str, Any] = report.datasets[dataset_id]
                df = dataset.get("_df", None)

                if df is None or not isinstance(df, pd.DataFrame):
                    raise ValueError("Cannot auto-calculate trend coefficients without the original DataFrame in the dataset.")
                
                x = df[x_column].to_numpy()
                y = df[y_column].to_numpy()

                print(df)
                coefficients = analytics.calculate_trend_coefficients(x, y, degree=degree)

            
            element["coefficients"] = coefficients
            
            element.update(kwargs)
            self.other_elements.append(element)
            return self

        def to_dict(self) -> Dict[str, Any]:
            d: Dict[str, Any] = {
                "type": self.type,
                "elementType": "visual"
            }
            if self.dataset_id:
                d["datasetId"] = self.dataset_id
            
            if self.other_elements:
                d["otherElements"] = [DL2Report._camel_case_dict(e) for e in self.other_elements]
            
            # Convert snake_case keys to camelCase for the JSON
            for k, v in self.props.items():
                camel_k = "".join(word.capitalize() if i > 0 else word for i, word in enumerate(k.split("_")))
                if isinstance(v, dict):
                    d[camel_k] = DL2Report._camel_case_dict(v)
                elif isinstance(v, list):
                    d[camel_k] = [DL2Report._camel_case_dict(i) if isinstance(i, dict) else i for i in v]
                else:
                    d[camel_k] = v
            return d

    class Layout(ReportTreeComponent):
        def __init__(self, direction: str = "row", **kwargs):
            """
            Initializes a new Layout.
            
            Args:
                direction: The direction of the layout ('row' or 'column').
                **kwargs: Additional properties for the layout:
                    * **height** (int): Height of the layout in pixels.
                    * **gap** (int): Gap between children in pixels.
                    * **padding** (int): Padding in pixels.
                    * **margin** (int): Margin in pixels.
                    * **border** (bool/str): CSS border or boolean to enable default.
                    * **shadow** (bool/str): CSS box-shadow or boolean to enable default.
                    * **flex** (int): Flex grow value.
            """
            super().__init__()
            self.type = "layout"
            self.direction = direction
            self.children: List[DL2Report.Layout | DL2Report.Visual] = []
            self.props = kwargs

        def add_visual(self, type: str, dataset_id: Optional[str] = None, **kwargs) -> DL2Report.Visual:
            """
            Adds a generic visual to the layout.
            
            Args:
                type: The type of visual (e.g., 'line', 'area', 'bar').
                dataset_id: The ID of the dataset to use for the visual.
                **kwargs: Additional properties for the visual:
                    * **padding** (int): Padding in pixels.
                    * **margin** (int): Margin in pixels.
                    * **border** (bool/str): CSS border or boolean to enable default.
                    * **shadow** (bool/str): CSS box-shadow or boolean to enable default.
                    * **flex** (int): Flex grow value.
                    * **modal_id** (str): The ID of a modal to open when the expand icon is clicked.
            
            Returns:
                DL2Report.Visual: The Visual instance.
            """
            visual = DL2Report.Visual(type, dataset_id, **kwargs)
            visual.parent = self
            self.children.append(visual)
            return visual
        
        def add_layout(self, direction: str = "row", **kwargs) -> DL2Report.Layout:
            """
            Adds a nested layout to the current layout.
            
            Args:
                direction: The direction of the nested layout ('row' or 'column').
                **kwargs: Additional properties for the layout.
            
            Returns:
                DL2Report.Layout: The Layout instance.
            """
            layout = DL2Report.Layout(direction, **kwargs)
            layout.parent = self
            self.children.append(layout)
            return layout

        def add_kpi(self, dataset_id: str, value_column: str, title: str, **kwargs) -> DL2Report.Visual:
            """
            Adds a KPI visual to the layout.
            
            Args:
                dataset_id: The ID of the dataset.
                value_column: The column containing the KPI value.
                title: The title of the KPI.
                **kwargs: Additional properties:
                    * **comparison_column** (str): Column for the comparison value.
                    * **row_index** (int): Index of the row in the dataset (default 0).
                    * **format** (str): 'number', 'currency', or 'percent'.
                    * **currency_symbol** (str): Symbol for currency (default '$').
                    * **good_direction** (str): 'higher' or 'lower'.
                    * **breach_value** (float): Value that triggers a breach indicator.
                    * **warning_value** (float): Value that triggers a warning indicator.
                    * **padding**, **margin**, **border**, **shadow**, **flex**, **modal_id**: Common visual properties.
            
            Returns:
                DL2Report.Visual: The Visual instance.
            """
            return self.add_visual("kpi", dataset_id, value_column=value_column, title=title, **kwargs)

        def add_table(self, dataset_id: str, title: Optional[str] = None, **kwargs) -> DL2Report.Visual:
            """
            Adds a table visual to the layout.
            
            Args:
                dataset_id: The ID of the dataset.
                title: Optional title for the table.
                **kwargs: Additional properties:
                    * **columns** (List[str]): Optional array of column names to display.
                    * **page_size** (int): Number of rows per page (default 10).
                    * **table_style** (str): 'plain', 'bordered', or 'alternating'.
                    * **show_search** (bool): Whether to show the search bar (default True).
                    * **padding**, **margin**, **border**, **shadow**, **flex**, **modal_id**: Common visual properties.
            
            Returns:
                DL2Report.Visual: The Visual instance.
            """
            return self.add_visual("table", dataset_id, title=title, **kwargs)

        def add_card(self, title: str, text: str, **kwargs) -> DL2Report.Visual:
            """
            Adds a card visual with static or computed text.
            
            Args:
                title: The title of the card (supports {{expr}}).
                text: The text content of the card (supports {{expr}}).
                **kwargs: Additional properties:
                    * **padding**, **margin**, **border**, **shadow**, **flex**, **modal_id**: Common visual properties.
            
            Returns:
                DL2Report.Visual: The Visual instance.
            """
            return self.add_visual("card", None, title=title, text=text, **kwargs)

        def add_pie(self, dataset_id: str, category_column: str, value_column: str, **kwargs) -> DL2Report.Visual:
            """
            Adds a pie chart visual.
            
            Args:
                dataset_id: The ID of the dataset.
                category_column: The column for pie slices.
                value_column: The column for slice values.
                **kwargs: Additional properties:
                    * **inner_radius** (int): For donut chart style.
                    * **show_legend** (bool): Whether to show the legend.
                    * **padding**, **margin**, **border**, **shadow**, **flex**, **modal_id**: Common visual properties.
            
            Returns:
                DL2Report.Visual: The Visual instance.
            """
            return self.add_visual("pie", dataset_id, category_column=category_column, value_column=value_column, **kwargs)

        def add_bar(self, dataset_id: str, x_column: str, y_columns: List[str], stacked: bool = False, **kwargs) -> DL2Report.Visual:
            """
            Adds a bar chart visual (clustered or stacked).
            
            Args:
                dataset_id: The ID of the dataset.
                x_column: The column for the X-axis.
                y_columns: The list of columns for the Y-axis.
                stacked: Whether to stack the bars.
                **kwargs: Additional properties:
                    * **x_axis_label** (str): Label for X-axis.
                    * **y_axis_label** (str): Label for Y-axis.
                    * **show_legend** (bool): Whether to show the legend.
                    * **show_labels** (bool): Whether to show value labels on bars.
                    * **horizontal** (bool): Whether to display bars horizontally.
                    * **padding**, **margin**, **border**, **shadow**, **flex**, **modal_id**: Common visual properties.
            
            Returns:
                DL2Report.Visual: The Visual instance.
            """
            type = "stackedBar" if stacked else "clusteredBar"
            return self.add_visual(type, dataset_id, x_column=x_column, y_columns=y_columns, **kwargs)

        def add_scatter(self, dataset_id: str, x_column: str, y_column: str, **kwargs) -> DL2Report.Visual:
            """
            Adds a scatter plot visual.
            
            Args:
                dataset_id: The ID of the dataset.
                x_column: The column for the X-axis.
                y_column: The column for the Y-axis.
                **kwargs: Additional properties:
                    * **category_column** (str): Optional column for coloring points by category.
                    * **show_trendline** (bool): Whether to show a linear regression trendline.
                    * **show_correlation** (bool): Whether to show correlation stats.
                    * **point_size** (int): Size of the data points (default 5).
                    * **x_axis_label** (str): Label for X-axis.
                    * **y_axis_label** (str): Label for Y-axis.
                    * **padding**, **margin**, **border**, **shadow**, **flex**, **modal_id**: Common visual properties.
            
            Returns:
                DL2Report.Visual: The Visual instance.
            """
            return self.add_visual("scatter", dataset_id, x_column=x_column, y_column=y_column, **kwargs)

        def add_line(self, dataset_id: str, x_column: str, y_columns: List[str] | str, **kwargs) -> DL2Report.Visual:
            """
            Adds a line chart visual.
            
            Args:
                dataset_id: The ID of the dataset.
                x_column: The column for the X-axis.
                y_columns: The column(s) for the Y-axis.
                **kwargs: Additional properties:
                    * **smooth** (bool): Whether to use a smooth curve.
                    * **show_legend** (bool): Whether to show the legend.
                    * **show_labels** (bool): Whether to show value labels on points.
                    * **min_y** (float): Optional minimum Y-axis value.
                    * **max_y** (float): Optional maximum Y-axis value.
                    * **colors** (List[str]): Array of colors for the lines.
                    * **x_axis_label** (str): Label for X-axis.
                    * **y_axis_label** (str): Label for Y-axis.
                    * **padding**, **margin**, **border**, **shadow**, **flex**, **modal_id**: Common visual properties.
            
            Returns:
                DL2Report.Visual: The Visual instance.
            """
            return self.add_visual("line", dataset_id, x_column=x_column, y_columns=y_columns, **kwargs)

        def add_checklist(self, dataset_id: str, status_column: str, **kwargs) -> DL2Report.Visual:
            """
            Adds a checklist visual.
            
            Args:
                dataset_id: The ID of the dataset.
                status_column: Column name containing boolean/truthy value for completion.
                **kwargs: Additional properties:
                    * **warning_column** (str): Column name containing a date to check against.
                    * **warning_threshold** (int): Days before due date to trigger warning (default 3).
                    * **columns** (List[str]): Optional array of column names to display.
                    * **page_size** (int): Number of rows per page (default 10).
                    * **show_search** (bool): Whether to show the search bar (default True).
                    * **padding**, **margin**, **border**, **shadow**, **flex**, **modal_id**: Common visual properties.
            
            Returns:
                DL2Report.Visual: The Visual instance.
            """
            return self.add_visual("checklist", dataset_id, status_column=status_column, **kwargs)

        def add_histogram(self, dataset_id: str, column: str, **kwargs) -> DL2Report.Visual:
            """
            Adds a histogram visual.
            
            Args:
                dataset_id: The ID of the dataset.
                column: Column containing the numerical values to bin.
                **kwargs: Additional properties:
                    * **bins** (int): Number of bins (default 10).
                    * **color** (str): Color of the bars.
                    * **show_labels** (bool): Whether to show count labels.
                    * **x_axis_label** (str): Label for X-axis.
                    * **y_axis_label** (str): Label for Y-axis.
                    * **padding**, **margin**, **border**, **shadow**, **flex**, **modal_id**: Common visual properties.
            
            Returns:
                DL2Report.Visual: The Visual instance.
            """
            return self.add_visual("histogram", dataset_id, column=column, **kwargs)

        def add_heatmap(self, dataset_id: str, x_column: str, y_column: str, value_column: str, **kwargs) -> DL2Report.Visual:
            """
            Adds a heatmap visual.
            
            Args:
                dataset_id: The ID of the dataset.
                x_column: Column for X-axis categories.
                y_column: Column for Y-axis categories.
                value_column: Column for the heat value.
                **kwargs: Additional properties:
                    * **show_cell_labels** (bool): Whether to show value text inside cells.
                    * **min_value** (float): Optional minimum value for color scale.
                    * **max_value** (float): Optional maximum value for color scale.
                    * **color** (str|List[str]): Color scheme (e.g., "Viridis") or array of colors.
                    * **x_axis_label** (str): Label for X-axis.
                    * **y_axis_label** (str): Label for Y-axis.
                    * **padding**, **margin**, **border**, **shadow**, **flex**, **modal_id**: Common visual properties.
            
            Returns:
                DL2Report.Visual: The Visual instance.
            """
            return self.add_visual("heatmap", dataset_id, x_column=x_column, y_column=y_column, value_column=value_column, **kwargs)

        def add_boxplot(self, dataset_id: str, **kwargs) -> DL2Report.Visual:
            """
            Adds a box plot visual.
            
            Args:
                dataset_id: The ID of the dataset.
                **kwargs: Additional properties:
                    * **data_column** (str): Raw numerical values to calculate box stats (Data Mode).
                    * **category_column** (str): Column to group data by.
                    * **min_column**, **q1_column**, **median_column**, **q3_column**, **max_column**, **mean_column**: Pre-calc Mode columns.
                    * **direction** (str): 'vertical' or 'horizontal'.
                    * **show_outliers** (bool): Whether to show outliers (default True).
                    * **color** (str|List[str]): Fill color or D3 scheme name.
                    * **x_axis_label** (str): Label for X-axis.
                    * **y_axis_label** (str): Label for Y-axis.
                    * **padding**, **margin**, **border**, **shadow**, **flex**, **modal_id**: Common visual properties.
            
            Returns:
                DL2Report.Visual: The Visual instance.
            """
            return self.add_visual("boxplot", dataset_id, **kwargs)

        def add_modal_button(self, modal_id: str, button_label: str, **kwargs) -> DL2Report.Visual:
            """
            Adds a button that triggers a modal.
            
            Args:
                modal_id: The ID of the modal to open.
                button_label: The text to display on the button.
                **kwargs: Additional properties for the button:
                    * **padding**, **margin**, **border**, **shadow**, **flex**: Common visual properties.
            
            Returns:
                DL2Report.Visual: The Visual instance.
            """
            return self.add_visual("modal", id=modal_id, button_label=button_label, **kwargs)

        def to_dict(self) -> Dict[str, Any]:
            """
            Converts the layout and its children to a dictionary.
            
            Returns:
                Dict[str, Any]: A dictionary representation of the layout.
            """
            d: Dict[str, Any] = {
                "type": "layout",
                "direction": self.direction,
                "children": [c.to_dict() for c in self.children]
            }
            for k, v in self.props.items():
                camel_k = "".join(word.capitalize() if i > 0 else word for i, word in enumerate(k.split("_")))
                if isinstance(v, dict):
                    d[camel_k] = DL2Report._camel_case_dict(v)
                elif isinstance(v, list):
                    d[camel_k] = [DL2Report._camel_case_dict(i) if isinstance(i, dict) else i for i in v]
                else:
                    d[camel_k] = v
            return d

    class Page(ReportTreeComponent):
        def __init__(self, title: str, description: Optional[str] = None):
            """
            Initializes a new Page.
            
            Args:
                title: The title of the page.
                description: Optional description of the page.
            """
            super().__init__()
            self.title = title
            self.description = description
            self.rows: List[DL2Report.Layout] = []

        def add_row(self, direction: str = "row", **kwargs) -> DL2Report.Layout:
            """
            Adds a new layout row to the page.
            
            Args:
                direction: The direction of the row ('row' or 'column').
                **kwargs: Additional properties for the layout.
            
            Returns:
                DL2Report.Layout: The Layout instance.
            """
            row = DL2Report.Layout(direction, **kwargs)
            row.parent = self
            self.rows.append(row)
            return row

        def to_dict(self) -> Dict[str, Any]:
            """
            Converts the page to a dictionary.
            
            Returns:
                Dict[str, Any]: A dictionary representation of the page.
            """
            d: Dict[str, Any] = {
                "title": self.title,
                "rows": [r.to_dict() for r in self.rows]
            }
            if self.description:
                d["description"] = self.description
            return d

    class Modal(ReportTreeComponent):
        def __init__(self, id: str, title: str, description: Optional[str] = None):
            """
            Initializes a new Modal.
            
            Args:
                id: Unique identifier for the modal.
                title: The title of the modal.
                description: Optional description of the modal.
            """
            super().__init__()
            self.id = id
            self.title = title
            self.description = description
            self.rows: List[DL2Report.Layout] = []

        def add_row(self, direction: str = "row", **kwargs) -> DL2Report.Layout:
            """
            Adds a new layout row to the modal.
            
            Args:
                direction: The direction of the row ('row' or 'column').
                **kwargs: Additional properties for the layout.
            
            Returns:
                DL2Report.Layout: The Layout instance.
            """
            row = DL2Report.Layout(direction, **kwargs)
            row.parent = self
            self.rows.append(row)
            return row

        def to_dict(self) -> Dict[str, Any]:
            """
            Converts the modal to a dictionary.
            
            Returns:
                Dict[str, Any]: A dictionary representation of the modal.
            """
            d: Dict[str, Any] = {
                "id": self.id,
                "title": self.title,
                "rows": [r.to_dict() for r in self.rows]
            }
            if self.description:
                d["description"] = self.description
            return d

    @staticmethod
    def _camel_case_dict(d: Dict[str, Any]) -> Dict[str, Any]:
        new_d = {}
        for k, v in d.items():
            camel_k = "".join(word.capitalize() if i > 0 else word for i, word in enumerate(k.split("_")))
            if isinstance(v, dict):
                new_d[camel_k] = DL2Report._camel_case_dict(v)
            elif isinstance(v, list):
                new_d[camel_k] = [DL2Report._camel_case_dict(i) if isinstance(i, dict) else i for i in v]
            else:
                new_d[camel_k] = v
        return new_d
    
    @staticmethod
    def _make_dataset_serializable(dataset: Dict[str, Any]) -> Dict[str, Any]:
        serializable_dataset = dataset.copy()
        if "_df" in serializable_dataset:
            del serializable_dataset["_df"]
        return serializable_dataset

    def __init__(self, title: str, description: str = "", author: str = ""):
        """
        Initializes a new DL2Report.
        
        Args:
            title: The title of the report.
            description: A brief description of the report.
            author: The author of the report.
        """
        self.title = title
        self.description = description
        self.author = author
        self.pages: List[DL2Report.Page] = []
        self.modals: List[DL2Report.Modal] = []
        self.datasets: Dict[str, Dict[str, Any]] = {}
        self.compressed_datasets: Dict[str, str] = {}
        self.css_url = "https://cdn.jsdelivr.net/gh/kameronbrooks/datalys2-reporting@latest/dist/dl2-style.css"
        self.js_url = "https://cdn.jsdelivr.net/gh/kameronbrooks/datalys2-reporting@latest/dist/datalys2-reports.min.js"
        self.meta_tags: Dict[str, str] = {}

    def get_report(self) -> DL2Report:
        """
        Gets the parent DL2Report instance.
        
        :param self: Description
        :return: Description
        :rtype: DL2Report | None
        """
        return self

    def add_df(self, name: str, df: pd.DataFrame, format: str = "records", compress: bool = False) -> DL2Report:
        """
        Adds a DataFrame to the report.
        
        Args:
            name: Name of the dataset.
            df: The DataFrame to add.
            format: Data format ('records' or 'table').
            compress: Whether to compress the data using gzip.
        
        Returns:
            DL2Report: The DL2Report instance.
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
            "data": data,
            "_df": df  # Store original DataFrame for reference
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
        page.parent = self
        self.pages.append(page)
        return page

    def add_modal(self, id: str, title: str, description: Optional[str] = None) -> DL2Report.Modal:
        """
        Adds a modal to the report.
        
        Args:
            id: Unique identifier for the modal.
            title: The title displayed in the modal header.
            description: Optional description text.
        
        Returns:
            DL2Report.Modal: The Modal instance.
        """
        modal = DL2Report.Modal(id, title, description)
        modal.parent = self
        self.modals.append(modal)
        return modal

    def set_meta(self, name: str, content: str) -> DL2Report:
        """
        Sets a meta tag for the report.
        
        Args:
            name: The name of the meta tag.
            content: The content of the meta tag.
        
        Returns:
            DL2Report: The DL2Report instance.
        """
        self.meta_tags[name] = content
        return self

    def compile(self) -> str:
        """
        Compiles the report into a single HTML string.
        
        Returns:
            str: The compiled HTML string.
        """
        report_data = {
            "pages": [p.to_dict() for p in self.pages],
            "datasets": {name: self._make_dataset_serializable(ds) for name, ds in self.datasets.items()}
        }
        if self.modals:
            report_data["modals"] = [m.to_dict() for m in self.modals]
            
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
        """
        Saves the compiled report to a file.
        
        Args:
            filename: The path to the file to save.
        """
        with open(filename, "w", encoding="utf-8") as f:
            f.write(self.compile())

    def show(self, height: int = 800):
        """
        Displays the report directly in a Jupyter Notebook cell using an iframe.
        
        Args:
            height: The height of the iframe in pixels (default 800).
        """
        try:
            from IPython.display import IFrame
            import base64
            
            # Use a data URI with IFrame to avoid the UserWarning and local file issues.
            # This is the most portable way to embed the HTML.
            b64_html = base64.b64encode(self.compile().encode('utf-8')).decode('utf-8')
            data_uri = f"data:text/html;base64,{b64_html}"
            return IFrame(data_uri, width="100%", height=height)
        except ImportError:
            # Fallback for environments without IPython
            print("IPython not found. Save the report to an HTML file to view it.")

    def _repr_html_(self):
        """
        Enables automatic rendering in Jupyter Notebooks when the report object is the last line of a cell.
        
        Returns:
            str: An iframe string containing the report.
        """
        # We use srcdoc here because _repr_html_ must return a string.
        # This might still trigger a warning in some environments, but it's the standard way for _repr_html_.
        escaped_html = html.escape(self.compile())
        return f'<iframe srcdoc="{escaped_html}" width="100%" height="800px" style="border:none;"></iframe>'
