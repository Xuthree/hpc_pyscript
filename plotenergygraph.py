# import io
import tempfile
from functools import partial
from itertools import chain, pairwise
from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
from adjustText import adjust_text
from matplotlib.axes import Axes
from nicegui import events, ui
from scipy.interpolate import CubicHermiteSpline

from tol_colormaps import color_set_definitions, tol_cset


import numpy as np


# def pchip_interpolate(x, y, x_new):
#     """
#     PCHIP 插值函数。

#     参数：
#         x: 原始 x 坐标数组。
#         y: 原始 y 坐标数组。
#         x_new: 需要插值的 x 坐标数组。

#     返回：
#         插值后的 y 坐标数组。
#     """

#     x = np.asarray(x, dtype=float)
#     y = np.asarray(y, dtype=float)
#     x_new = np.asarray(x_new, dtype=float)

#     n = len(x)
#     m = (y[1:] - y[:-1]) / (x[1:] - x[:-1])  # 斜率

#     d = np.zeros(n)
#     d[1:-1] = (m[:-1] * m[1:] > 0) * (
#         3
#         * (x[2:] - x[:-2])
#         / (
#             (2 * (x[1:-1] - x[:-2]) + (x[2:] - x[1:-1])) / m[:-1]
#             + ((x[1:-1] - x[:-2]) + 2 * (x[2:] - x[1:-1])) / m[1:]
#         )
#     )

#     # 处理边界导数，通常设置为与相邻导数相等
#     d[0] = d[1]
#     d[-1] = d[-2]

#     y_new_interp = np.zeros_like(x_new)

#     for i in range(n - 1):
#         mask = (x_new >= x[i]) & (x_new <= x[i + 1])
#         if np.any(mask):
#             delta_x = x_new[mask] - x[i]
#             h = x[i + 1] - x[i]
#             y_new_interp[mask] = (
#                 y[i]
#                 + d[i] * delta_x
#                 + (3 * m[i] - 2 * d[i] - d[i + 1]) * delta_x**2 / h
#                 + (d[i] + d[i + 1] - 2 * m[i]) * delta_x**3 / h**2
#             )

#     return y_new_interp


def random_use_tolcolor(num: int, set_name="bright"):
    cset = tol_cset(set_name)
    cset = list(cset.colors.values())  # type: ignore
    colors = [cset[i] for i in np.random.randint(0, len(cset), num)]
    return colors


def arrowed_spines(
    ax,
    x_width_fraction=0.05,
    x_height_fraction=0.05,
    lw=None,
    ohg=0.3,
    locations=("bottom right", "left up"),
    **arrow_kwargs,
):
    """
    Add arrows to the requested spines
    Code originally sourced here: https://3diagramsperpage.wordpress.com/2014/05/25/arrowheads-for-axis-in-matplotlib/
    And interpreted here by @Julien Spronck: https://stackoverflow.com/a/33738359/1474448
    from https://stackoverflow.com/questions/33737736/matplotlib-axis-arrow-tip
    Then corrected and adapted by me for more general applications.
    :param ax: The axis being modified
    :param x_{height,width}_fraction: The fraction of the **x** axis range used for the arrow height and width
    :param lw: Linewidth. If not supplied, default behaviour is to use the value on the current left spine.
    :param ohg: Overhang fraction for the arrow.
    :param locations: Iterable of strings, each of which has the format "<spine> <direction>". These must be orthogonal
    (e.g. "left left" will result in an error). Can specify as many valid strings as required.
    :param arrow_kwargs: Passed to ax.arrow()
    :return: Dictionary of FancyArrow objects, keyed by the location strings.
    """
    # set/override some default plotting parameters if required
    arrow_kwargs.setdefault("overhang", ohg)
    arrow_kwargs.update({"clip_on": False, "length_includes_head": True})

    # axis line width
    if lw is None:
        # FIXME: does this still work if the left spine has been deleted?
        lw = ax.spines["left"].get_linewidth()

    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()

    # get width and height of axes object to compute
    # matching arrowhead length and width
    fig = ax.get_figure()
    bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    width, height = bbox.width, bbox.height

    # manual arrowhead width and length
    hw = x_width_fraction * (ymax - ymin)
    hl = x_height_fraction * (xmax - xmin)

    # compute matching arrowhead length and width
    yhw = hw / (ymax - ymin) * (xmax - xmin) * height / width
    yhl = hl / (xmax - xmin) * (ymax - ymin) * width / height

    # draw x and y axis
    annots = {}
    for loc_str in locations:
        side, direction = loc_str.split(" ")
        assert side in {"top", "bottom", "left", "right"}, "Unsupported side"
        assert direction in {"up", "down", "left", "right"}, "Unsupported direction"

        if side in {"bottom", "top"}:
            if direction in {"up", "down"}:
                raise ValueError(
                    "Only left/right arrows supported on the bottom and top"
                )

            dy = 0
            head_width = hw
            head_length = hl

            y = ymin if side == "bottom" else ymax

            if direction == "right":
                x = xmin
                dx = xmax - xmin
            else:
                x = xmax
                dx = xmin - xmax

        else:
            if direction in {"left", "right"}:
                raise ValueError("Only up/downarrows supported on the left and right")
            dx = 0
            head_width = yhw
            head_length = yhl

            x = xmin if side == "left" else xmax

            if direction == "up":
                y = ymin
                dy = ymax - ymin
            else:
                y = ymax
                dy = ymin - ymax

        annots[loc_str] = ax.arrow(
            x,
            y,
            dx,
            dy,
            fc="k",
            ec="k",
            lw=lw,
            head_width=head_width,
            head_length=head_length,
            **arrow_kwargs,
        )

    return annots


def interpolate_hermite(x, y, pts=200):
    """
    Generate a series of cubic Hermite interpolation points along the reaction path stationary points.

    Parameters:
    x (array-like) -- x coordinates
    y (array-like) -- y coordinates
    pts (int, optional) -- number of interpolation points (default: 200)

    Returns:
    x_pts (numpy.ndarray) -- interpolated x coordinates
    y_pts (numpy.ndarray) -- interpolated y coordinates
    """
    # Convert input x and y to numpy arrays
    x, y = np.array(x), np.array(y)
    # Ensure that the lengths of x and y arrays are the same
    assert len(x) == len(y), "The length of x and y arrays must be the same"
    if len(x) < 2:
        raise ValueError("At least two points are required for interpolation")
    # Initialize the derivative array; this is a simplified approach
    dydx = np.zeros_like(y)

    spline = CubicHermiteSpline(x, y, dydx)
    # Generate equidistant interpolation points between the minimum and maximum x values
    x_pts = np.linspace(x.min(), x.max(), pts)
    # Obtain the y coordinates of the interpolation points using the spline
    y_pts = spline(x_pts)
    return x_pts, y_pts


class PlotEnergyProfile:
    def __init__(self, data: np.ndarray, ax: Axes):
        self.data = self.filter_data(data)
        self.ax = ax

        self.xtick_labels = self.data[3:, 0]
        self.colors = self.data[1, 1:]
        self.x = np.array([i for i in range(len(self.xtick_labels))])
        self.y_str_ = self.data[3:, 1:]
     
        self.ys = self.data[3:, 1:].T
        self.line_style = self.data[2, 1:]
        self.path_labels = self.data[0, 1:]
        self.ys_list = self.ys[self.ys != ''].astype(float)
        self.y_bias = (np.nanmax(self.ys_list) - np.nanmin(self.ys_list)) / 10
            
    
    def filter_data(self, nda: np.ndarray):
        """过滤掉 nda 中的空行，空列"""
        row_mask = np.any(nda != "", axis=1)
        col_mask = np.any(nda != "", axis=0)
        filtered_nda = nda[row_mask, :][:, col_mask]
        # filter_data = np.where(filtered_nda == "", np.nan, filtered_nda)
        return filtered_nda

    def filter_nan(self, x, y):  # -> tuple[Any, Any] | tuple[list[Any], list[Any]]:
        """过滤掉 y 中的 NaN 值"""
        x, y = np.array(x), np.array(y)
        pairs = filter(lambda pair: pair[1], zip(x, y)) ##np.isnan(pair[1])
        if pairs:
            x_new, y_new = zip(*pairs)
            return np.array(x_new).astype(float), np.array(y_new).astype(float)
        else:
            return np.array([]), np.array([])

    def _expand_xy(self, x, y, ratio=1.0):
        """_summary_

        Args:
            x (_type_): _description_
            y (_type_): _description_
            ratio (float, optional): the ratio of hline/slash.

        Returns:
            _type_: _description_
        """
        d = ratio / (2 + 2 * ratio)
        x = np.array(x)
        y = np.array(y)
        x_left = x - d
        x_right = x + d
        new_x = np.column_stack((x_left, x_right)).ravel()
        new_y = np.repeat(y, 2)
        return new_x, new_y

    def single_curve(self, x, y, marker="o", s=20, lw=2, ls="-", **kwargs):
        """plot scatter and smooth curve
           filter nan and interpolate hermite

        Args:
            x (list|ndarray): the x axis data
            y (list|ndarray): the y axis data
        """
        new_x, new_y = self.filter_nan(x, y)

        self.ax.scatter(new_x, new_y, marker=marker, s=s, **kwargs)
        x_smooth, y_smooth = interpolate_hermite(new_x, new_y)
        self.ax.plot(x_smooth, y_smooth, linewidth=lw, linestyle=ls, **kwargs)

    def plot_curve(self, **kwargs):
        """绘制多条平滑曲线型能垒图"""
        for i, y_values in enumerate(self.ys):
            self.single_curve(
                self.x,
                y_values,
                ls=self.line_style[i],
                color=self.colors[i],
                label=self.path_labels[i],
                **kwargs,
            )

    def single_line_dot(self, x, y, lw=2, slash_ls="--", ratio=0.6, **kwargs):
        """生成新的XY坐标点并绘制分段实线图"""
        new_x, new_y = self.filter_nan(x, y)
        x_new, y_new = self._expand_xy(new_x, new_y)
        x_pairs, y_pairs = pairwise(x_new), pairwise(y_new)
        for i, (xis, yis) in enumerate(zip(x_pairs, y_pairs)):
            if i % 2 == 0:
                line_stylei = "-"  # 实线
                r = 1
            else:
                line_stylei = slash_ls  # 虚线
                r = ratio
            self.ax.plot(
                xis, yis, linestyle=line_stylei, linewidth=lw * r, **kwargs
            )  # color=color, label=path_label)

    def plot_line_dot(self, slash_ls, **kwargs):
        """绘制多条虚实折线图"""
        # if self.path_labels.shape[0] > 1:  # 多条路径的情况
        for i, y_values in enumerate(self.ys):
            self.single_line_dot(
                self.x,
                y_values,
                slash_ls=slash_ls,
                color=self.colors[i],
                label=self.path_labels[i],
                **kwargs,
            )

    def single_line_curve(self, x, y, lw=2, ls="-", **kwargs):
        """单条曲线：根据中间体及过渡态类型绘制能垒图，对中间体绘制横线，对过渡态绘制曲线"""
        assert len(x) == len(self.xtick_labels) and len(y) == len(self.xtick_labels)
        new_x, new_y = self.filter_nan(x, y)
        new_xtick_labels, _ = self.filter_nan(self.xtick_labels, y)

        def segment_points(xi, yi, xlabel):
            if "TS" in xlabel:
                return [(xi, yi)]
            else:
                return list(zip(*self._expand_xy(xi, yi)))

        points = map(
            lambda xi_yi_label: segment_points(*xi_yi_label),
            zip(new_x, new_y, new_xtick_labels),
        )

        x_new, y_new = zip(*chain.from_iterable(points))
        x_smooth, y_smooth = interpolate_hermite(x_new, y_new, 100)
        self.ax.plot(x_smooth, y_smooth, linewidth=lw, linestyle=ls, **kwargs)
        # self._set_text_label(new_x, new_y, self.text_label, self.text_adjust)
        # return new_x, new_y

    def plot_line_curve(self, **kwargs):
        """绘制多条虚实折线图"""
        for i, y_values in enumerate(self.ys):
            self.single_line_curve(
                self.x,
                y_values,
                color=self.colors[i],
                label=self.path_labels[i],
                ls=self.line_style[i],
                **kwargs,
            )

    def set_xtick_labels(self, **kwargs):
        """设置x轴刻度标签"""
        self.ax.set_xticks(self.x, self.xtick_labels, **kwargs)

    def set_text_labels(
        self, text_label=False, text_adjust=False, y_bais=0.05, **kwargs
    ):
        """在图中添加文本标签"""
        # self.text_label, self.text_adjust = text_label, text_adjust
        for i, y_values in enumerate(self.ys):
            new_x, new_y = self.filter_nan(self.x, y_values)
            if text_label:
                texts = [
                    self.ax.text(
                        xi, yi + y_bais, f"{yi:.2f}", color=self.colors[i], **kwargs
                    )
                    for xi, yi in zip(new_x, new_y)
                ]
                if text_adjust:
                    adjust_text(texts, ax=self.ax)  # new_x, new_y,

    def set_legend(self, **kwargs):
        handles, labels = self.ax.get_legend_handles_labels()
        seen = set()
        unique = [
            (h, ll)
            for h, ll in zip(handles, labels)
            if ll not in seen and not seen.add(ll)
        ]
        self.ax.legend(*zip(*unique), **kwargs)

    def set_spines_style(self, spines_style):
        match spines_style:
            case "default":
                self.ax.tick_params(axis="y", direction="in")

            case "booklike":
                self.ax.set_xlim(self.x[0] - 0.5, self.x[-1] + 0.5)
                self.ax.tick_params(axis="both", direction="in")
                self.ax.set_yticks([])
                self.ax.spines[["bottom", "left", "right", "top"]].set_visible(False)
                arrowed_spines(
                    self.ax, lw=0.8, x_width_fraction=0.02, x_height_fraction=0.02
                )

            case "only_y":
                self.ax.spines.left.set_bounds(
                    self.ax.get_ylim()[0], self.ax.get_ylim()[1]
                )
                self.ax.set_xticks([])
                self.ax.spines[["bottom", "right", "top"]].set_visible(False)

            case "x_y":
                self.ax.spines.bottom.set_bounds(self.x[0], self.x[-1])
                self.ax.spines.left.set_bounds(
                    self.ax.get_ylim()[0], self.ax.get_ylim()[1]
                )
                self.ax.tick_params(axis="x", direction="out")
                self.ax.spines[["right", "top"]].set_visible(False)

    def set_colors(self, colors):
        self.colors = colors


class EditableTable:
    def __init__(self, rows, cols):
        self.rows = rows
        self.columns = cols
        self.column_defs = self.enable(self.columns)
        self.table = ui.aggrid(
            {
                "defaultColDef": {"flex": 1},
                "columnDefs": self.column_defs,
                "rowData": self.rows,
                "rowSelection": "multiple",
                "stopEditingWhenCellsLoseFocus": True,
            }
        )
        self.table_area = ui.column()

    def _enable(self, col, key, value):
        col[key] = value
        return col

    def enable(self, cols: list[dict]) -> list[dict]:
        en_edit = partial(self._enable, key="editable", value=True)
        dissort = partial(self._enable, key="sortable", value=False)

        new_coldefs = list(map(en_edit, cols))
        new_coldefs = list(map(dissort, new_coldefs))
        return new_coldefs

    def delete_row(self):
        selected_rows = self.table.get_selected_rows()  # 获取选定的行
        if selected_rows:
            self.rows = [
                row for row in self.rows if row not in selected_rows
            ]  # 删除选定行
            ui.notify("Deleted selected_rows row(s).")
        else:
            ui.notify("No rows selected.")
        self.table.update()

    def add_row(self):
        # newid = max(dx["id"] for dx in self.rows) + 1
        new_row = {k: "" for k in self.rows[0].keys()}
        ui.notify(f"new row with {new_row}")
        self.rows.append(new_row)
        self.table.update()

    def add_column(self, column_name):
        if not column_name:
            ui.notify("name of column cannot be empty")
            return
        if column_name in self.columns:
            ui.notify(f"column '{column_name}' is existed")
            return
        new_col = {k: f"{column_name}" for k in self.columns[0].keys()}

        self.columns.append(new_col)
        for row in self.rows:
            row[column_name] = ""
        self.table.update()
        ui.notify(f"column '{column_name}' is added")

    def delete_column(self, column_name):
        if column_name not in self.columns:
            ui.notify(f"列 '{column_name}' 不存在")
            return
        self.columns.remove(column_name)
        for row in self.rows:
            del row[column_name]
        self.table.update()
        ui.notify(f"列 '{column_name}' 已删除")

    @property
    def data(self):
        rows = [list(self.rows[0].keys())]

        for row in self.rows:
            rows.append(list(row.values()))
        return rows

    def __str__(self) -> str:
        return "\n".join(",".join(row) for row in self.data)


class EnergyDiagramGUI:
    def __init__(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pic_title = ""
        self.x_label = "Reaction Pathway"
        self.y_label = r"$\Delta G\ ()$"
        self.plot_type = "Line_Dot"
        self.show_energy = False
        self.adjust_text = False
        self.legend = False
        self.random_color = False
        self.color_set_name = "bright"
        self.dot_dash_ratio = 0.6
        self.data_font_size = 12
        self.label_font_size = 12
        self.line_size = 2
        self.rotation_degree = 0.0
        self.ymin = -5.0
        self.ymax = 5.0
        self.xtick_label = ""
        self.plot_area = ui.element("div")
        self.table_area = ui.element("div")
        self.path_var = "./"
        self.data = None
        self.fig = None
        self.upfile = None
        self.colors = list()
        self.file_name = ""
        self.spines_style: Literal["default", "booklike", "only_y"] = "default"
        self.harizontal_alignment = "center"
        self.show_xtick_label = False
        self.create_ui()

    def handle_upload(self, e: events.UploadEventArguments):
        data_content = e.content.read().decode("utf-8")
        try:
            # print(data_content.splitlines())
            df = np.genfromtxt(data_content.splitlines(), delimiter=",", dtype=str)
            self.data = df[
                :, np.any(df != "", axis=0)
            ]  # df[:, ~np.all(df == "", axis=0)]
            ui.notify("Upload successful!", type="positive")
            self.file_name = e.name[0]
        except Exception as ee:
            ui.notify(f"Upload failed: {str(ee)}", type="negative")

    def table(self, data: np.ndarray):
        cols = [{"name": i, "label": i.capitalize(), "field": i} for i in data[0]]
        rows = []
        for j in data[1:]:
            row = {i: jj for i, jj in zip(data[0], j)}
            rows.append(row)
        return rows, cols

    def create_ui(self):
        with ui.row().classes("items-stretch"):
            with ui.card().classes("p-4 flex-1"):
                ui.label("Argument Info").classes("text-lg font-bold")

                with ui.row():
                    ui.input("Picture Title", value=self.pic_title).bind_value(
                        self, "pic_title"
                    ).classes("w-40")
                    ui.input("x label", value=self.x_label).bind_value(
                        self, "x_label"
                    ).classes("w-32")
                    ui.input("y label", value=self.y_label).bind_value(
                        self, "y_label"
                    ).classes("w-32")
                with ui.row():
                    ui.checkbox("Show Energy Text", value=self.show_energy).bind_value(
                        self, "show_energy"
                    ).classes("w-40")
                    ui.checkbox("Adjust Text", value=self.adjust_text).bind_value(
                        self, "adjust_text"
                    ).classes("w-32")
                    ui.checkbox("Legend", value=self.legend).bind_value(
                        self, "legend"
                    ).classes("w-32")

                with ui.row():
                    ui.checkbox("Xtick Label", value=self.show_xtick_label).bind_value(
                        self, "show_xtick_label"
                    ).classes("w-40")
                    ui.checkbox("Random Color", value=self.random_color).bind_value(
                        self, "random_color"
                    ).classes("w-40")
                with ui.row():
                    # ui.label(f'Change Xtick Label {MAX_COMMA_COUNT} 个逗号')
                    ui.input("Change Xtick Label", value=self.xtick_label).bind_value(
                        self, "xtick_label"
                    )
                # with ui.row():
                #     ui.textarea("Comment", value=self.comment).bind_value(self, "comment")
                with ui.row():
                    ui.number(
                        label="Data Font", value=self.data_font_size, min=1
                    ).bind_value(self, "data_font_size").classes("w-16")
                    ui.number(
                        label="Axis Font", value=self.label_font_size, min=1
                    ).bind_value(self, "label_font_size").classes("w-16")
                    ui.number(
                        label="Line Width", value=self.line_size, min=1
                    ).bind_value(self, "line_size").classes("w-16")

                    ui.number(label="YLim Min", value=self.ymin).bind_value(
                        self, "ymin"
                    ).classes("w-16")

                    ui.number(label="YLim Max", value=self.ymax).bind_value(
                        self, "ymax"
                    ).classes("w-16")
                    ui.number(
                        label="Dash Dot",
                        value=self.dot_dash_ratio,
                        min=0.1,
                        max=1,
                        step=0.01,
                    ).bind_value(self, "dot_dash_ratio").classes("w-16")

                with ui.row():
                    ui.number(
                        label="Rotation Degree", value=self.rotation_degree
                    ).bind_value(self, "rotation_degree").classes("w-32")

                    ui.select(
                        list(color_set_definitions.keys()),
                        label="Color Set",
                        value=self.color_set_name,
                    ).bind_value(self, "color_set_name").classes("w-32")
                    ui.select(
                        ["left", "right", "center"],
                        label="Rotation Center",
                        value="center",
                    ).bind_value(self, "harizontal_alignment").classes("w-32")

                with ui.row():
                    ui.select(
                        ["Curve", "Line_Dot", "Line_Curve"],
                        label="Plot Type",
                        value=self.plot_type,
                    ).bind_value(self, "plot_type").classes("w-32")
                    selected_format = ui.select(
                        ["PNG", "JPG", "SVG"], label="Choose format", value="PNG"
                    ).classes("w-32")
                    ui.select(
                        ["default", "booklike", "only_y", "x_y"],
                        label="Spines Style",
                        value=self.spines_style,
                    ).bind_value(self, "spines_style").classes("w-32")
                with ui.row():
                    self.upfile = ui.upload(
                        label="Select CSV",
                        on_upload=self.handle_upload,
                        auto_upload=True,
                    ).props("accept=.csv")  # .style('height: 40px;').classes('w-32')

                with ui.row().classes("justify-end"):
                    ui.button("Plot", on_click=self.draw_update)

                    ui.button(
                        "Save Figure",
                        on_click=lambda: self.save_fig(selected_format.value),
                    )
                    ui.button("Show Table", on_click=self.display_table)

            with ui.card().classes("p-4 flex-3"):
                ui.label("Plot Area").classes("text-lg font-bold")
                self.plot_area = ui.element("div")  # 占位符，用于显示图表

            with ui.card().classes("p-4 flex-2"):
                ui.label("Table Area").classes("text-lg font-bold")
                self.table_area = ui.element("div")

    def draw_plot(self):
        # 创建 Matplotlib 图形
        with ui.matplotlib(figsize=(6, 5), dpi=600).figure as fig:
            self.fig = fig  # 保存图形对象供后续使用
            ax = fig.gca()
            # plt.rc('font', family='Times New Roman')
            # plt.rc('mathtext', fontset='stix')
            ax.set_title(self.pic_title, fontsize=self.label_font_size)
            ax.set_xlabel(self.x_label, fontsize=self.label_font_size)
            ax.set_ylabel(self.y_label, fontsize=self.label_font_size)
            ax.set_ylim(self.ymin, self.ymax)
            ax.tick_params(
                axis="both",
                which="major",
                labelsize=self.label_font_size,
                direction="in",
            )
            try:
                if self.data is not None:
                    peg = PlotEnergyProfile(self.data, ax)
            except Exception as e:
                ui.notify(f"Data may be valid!,ERROR:\n {e}", color="red")
                raise e
            if self.random_color:
                self.colors.append(
                    random_use_tolcolor(len(peg.colors), self.color_set_name)
                )
            #     colors = random_use_tolcolor(len(peg.colors), self.color_set_name)
            if self.colors:
                peg.set_colors(self.colors[-1])

            match self.plot_type:
                case "Curve":
                    peg.plot_curve(lw=self.line_size)
                case "Line_Dot":
                    peg.plot_line_dot(
                        slash_ls="--", lw=self.line_size, ratio=self.dot_dash_ratio
                    )
                case "Line_Curve":
                    peg.plot_line_curve(lw=self.line_size)

            if self.legend:
                peg.set_legend(loc="best", frameon=False)

            peg.set_text_labels(
                self.show_energy,
                self.adjust_text,
                fontsize=self.data_font_size,
                ha=self.harizontal_alignment,
            )
            # ax.spines.left.set_bounds()
            # if self.x_label:

            peg.set_xtick_labels(
                fontsize=self.label_font_size,
                rotation=self.rotation_degree,
                ha=self.harizontal_alignment,
            )
            if self.xtick_label:
                xticklabel = self.xtick_label.split(",")
                assert len(xticklabel) == len(peg.xtick_labels), ui.notification(
                    "xtick label number not match!", color="red"
                )
                ax.set_xticklabels(xticklabel)
            peg.set_spines_style(self.spines_style)
            # if
            if not self.show_xtick_label:
                ax.set_xticklabels([])
                # ax.set_yticklabels([])
                ax.set_xticks([])
                # ax.set_yticks([])
            plt.rc("font", family="Times New Roman")
            plt.rc("mathtext", fontset="stix")

    def display_table(self):
        if self.data is not None:
            rows, cols = self.table(self.data)
            self.table_area.clear()
            with self.table_area:
                ui.table(rows=rows, columns=cols).classes("w-full")
                # tb = EditableTable(rows, cols)
                # with ui.row():
                #     tb.table
                # with ui.row():
                #     ui.button("Delete selected row", on_click=tb.delete_row)
                #     ui.button("New row", on_click=tb.add_row)
                # with ui.row():
                #     col_name = ''
                #     ui.input("Column name", value=col_name).bind_value(col_name)
                # with ui.row():
                #     ui.button("Delete column", on_click=tb.delete_column)
                #     ui.button("Add Column", on_click=tb.add_column(col_name))

    def save_fig(self, shuffix) -> None:
        if self.fig:
            ui.notify("figure is saved", color="green")
            file_path = f"plot.{shuffix.lower()}"
            self.fig.savefig(Path("./" + file_path), format=shuffix)
        else:
            ui.notify("No plot to save!", color="red")

    def run(self, *args, **kwargs) -> None:
        ui.run(*args, **kwargs)

    def draw_update(self) -> None:
        if self.plot_area:
            self.plot_area.clear()
            # if self.random_color:
            # self.colors = random_use_tolcolor(self.color_nums, self.color_set_name)
            with self.plot_area:
                self.draw_plot()


edg = EnergyDiagramGUI()
edg.run()
