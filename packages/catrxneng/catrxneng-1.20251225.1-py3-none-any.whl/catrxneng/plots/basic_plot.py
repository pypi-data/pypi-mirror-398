import plotly.graph_objects as go
import numpy as np
import plotly.express as px
from typing import Any
from .plotly_plot import PlotlyPlot


class BasicPlot(PlotlyPlot):

    def __init__(self, title: str | None = None, color_palette: str | None = None):
        self.fig = go.Figure()
        self.title = title
        self.custom_palette = False
        self.is_sequential = False
        if color_palette:
            try:
                self.colors = getattr(px.colors.qualitative, color_palette)
            except AttributeError:
                self.colors = getattr(px.colors.sequential, color_palette)
                self.is_sequential = True
            # Only set colorway for qualitative palettes; sequential palettes
            # will be indexed directly in add_trace
            if not self.is_sequential:
                self.fig.update_layout(colorway=self.colors)
            self.custom_palette = True
        else:
            self.colors = self.COLORS
        self.right_axis = False
        self.info_text = ""
        self.trace_count = 0

    def add_trace(
        self,
        x: np.ndarray,
        y: np.ndarray,
        name: str | None = None,
        mode: str = "lines",
        yaxis: str = "y1",
        hover_labels: list | None = None,
        color: str | None = None,
        dash: str | None = None,
        symbol: str | None = None,
    ):
        # if isinstance(y, (float, int, np.number)):
        #     xmin = np.min(x)
        #     xmax = np.max(x)
        #     x = [xmin, xmax]
        #     y = [y, y]
        hovertemplate = None
        if hover_labels:
            hovertemplate = "<b>%{text}</b><br>X: %{x}<br>Y: %{y}<extra></extra>"
        # If the caller asked for the secondary y axis, remember that so
        # render() can create it even when no ylabel2 is explicitly passed.
        if yaxis == "y2":
            self.right_axis = True

        # Auto-assign color from sequential palette if not provided
        if color is None and self.custom_palette and self.is_sequential:
            color = self.colors[min(self.trace_count, len(self.colors) - 1)]
            self.trace_count += 1

        trace_kwargs: dict[str, Any] = dict(
            x=x,
            y=y,
            mode=mode,
            yaxis=yaxis,
            name=name,
            text=hover_labels,
            hovertemplate=hovertemplate,
            showlegend=name is not None,
        )
        if mode == "lines":
            trace_kwargs["line"] = dict(dash=dash, color=color)
        if mode == "markers":
            trace_kwargs["marker"] = dict(symbol=symbol, color=color)

        trace = go.Scatter(**trace_kwargs)
        self.fig.add_trace(trace)

    def add_vertical_line(
        self,
        x: float,
        line_dash: str = "dash",
        line_color: str = "black",
        line_width: int = 2,
    ):
        """
        Adds a vertical dashed line at the specified x-value.

        Args:
            x_value (float): The x-coordinate where the vertical line will be added.
            line_dash (str): The dash style of the line (default is "dash").
            line_color (str): The color of the line (default is "black").
            line_width (int): The width of the line (default is 2).
        """
        self.fig.add_shape(
            type="line",
            x0=x,
            x1=x,
            y0=0,
            y1=1,
            xref="x",
            yref="paper",
            line=dict(
                dash=line_dash,
                color=line_color,
                width=line_width,
            ),
        )

    def add_constant_trace(
        self,
        y: float,
        name: str | None = None,
        yaxis: str = "y1",
        color: str | None = None,
        dash: str | None = None,
    ):
        # Determine x range from existing traces in the figure
        all_x_values = []
        for trace in self.fig.data:
            if trace.x is not None and len(trace.x) > 0:
                all_x_values.extend(trace.x)

        x_vals = (
            [np.nanmin(all_x_values), np.nanmax(all_x_values)]
            if all_x_values
            else [None, None]
        )
        y_vals = [y, y]

        if yaxis == "y2":
            self.right_axis = True

        trace_kwargs: dict[str, Any] = dict(
            x=x_vals,
            y=y_vals,
            mode="lines",
            yaxis=yaxis,
            name=name,
            showlegend=name is not None,
        )
        trace_kwargs["line"] = dict(dash=dash, color=color)

        trace = go.Scatter(**trace_kwargs)
        self.fig.add_trace(trace)

    def format(
        self,
        xlabel: str,
        ylabel: str,
        xrange: list = None,
        yrange: list = None,
        y2label: str = None,
        y2range: list = None,
        # info_text=None,
    ):
        # if xrange is None:
        #     xrange = [None, None]
        # if yrange is None:
        #     yrange = [None, None]
        # if y2range is None:
        #     y2range = [None, None]

        # if info_text:
        #     self.info_text = info_text
        top = 50
        width = 700
        if self.info_text == "":
            bottom = 50
            height = 400
        else:
            bottom = 110
            height = None

        yaxis2 = None
        # If a secondary axis label was provided, create yaxis2 with that
        # title. Also create a default right-hand axis when any trace asked
        # for `yaxis='y2'` (self.right_axis) even if no ylabel2 was passed.
        if y2label:
            yaxis2 = dict(
                title=f"<b>{y2label}</b>",
                range=y2range,
                showline=True,
                linecolor="black",
                linewidth=2,
                mirror=True,
                nticks=9,
                overlaying="y",
                side="right",
            )
        elif self.right_axis:
            # create a minimal secondary axis so traces assigned to 'y2'
            # will be rendered on the right side.
            yaxis2 = dict(
                title="",
                range=y2range,
                showline=True,
                linecolor="black",
                linewidth=2,
                mirror=True,
                nticks=9,
                overlaying="y",
                side="right",
            )
        self.fig.update_layout(
            title=dict(text=f"<b>{self.title}</b>", x=0.5),
            xaxis_title=f"<b>{xlabel}</b>",
            yaxis_title=f"<b>{ylabel}</b>",
            width=width,
            height=height,
            margin=dict(t=top, b=bottom),
            yaxis=dict(
                range=yrange,
                showline=True,
                linecolor="black",
                linewidth=2,
                mirror=True,
                nticks=9,
            ),
            yaxis2=yaxis2,
            xaxis=dict(
                range=xrange,
                showline=True,
                linecolor="black",
                linewidth=2,
                mirror=True,
            ),
            legend=dict(x=1.05, y=1, xanchor="left", yanchor="top"),
            annotations=self.plot_info_box(self.info_text),
            plot_bgcolor="white",
            paper_bgcolor="white",
            colorway=self.colors if self.custom_palette else self.COLORS,
        )

    def render(
        self,
        xlabel: str,
        ylabel: str,
        xrange: list = None,
        yrange: list = None,
        ylabel2: str = None,
        yrange2: list = None,
        # info_text=None,
    ):
        self.format(
            xlabel=xlabel,
            ylabel=ylabel,
            xrange=xrange,
            yrange=yrange,
            y2label=ylabel2,
            y2range=yrange2,
        )
        self.fig.show()

    def add_info_text(self, *args):
        for line in args:
            if self.info_text:
                self.info_text += "\n" + line
            else:
                self.info_text = line
