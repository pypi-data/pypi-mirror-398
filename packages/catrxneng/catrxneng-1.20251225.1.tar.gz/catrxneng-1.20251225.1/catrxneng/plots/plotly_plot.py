import plotly.express as px
import plotly.graph_objects as go


class PlotlyPlot:
    fig: go.Figure
    # COLORS = px.colors.qualitative.Plotly
    # COLORS = [
    #     "#EB3437",
    #     "#714BDB",
    #     "#34B13F",
    #     "#E951B6",
    #     "#F0752E",
    #     "#76AAAC",
    #     "#0A0101",
    #     "#80490B",
    #     "#98ADF1",
    #     "#F8F411",
    # ]
    COLORS = [
        "red",
        "blue",
        "LightSeaGreen",
        "magenta",
        "Coral",  # orange
        "gray",
        "black",
        "lightblue",
        "brown",
        "yellow",
        "cyan",
    ]

    @staticmethod
    def plot_info_box(text):
        if text is None:
            return None
        text = text.replace("\\n", "\n")
        text = text.strip("\n")
        text = text.replace("\n", "<br>")
        annotations = [
            dict(
                x=0.5,
                y=-0.35,
                xref="paper",
                yref="paper",
                text=text,
                showarrow=False,
                font=dict(size=12, style="italic", weight="bold"),
            )
        ]
        return annotations
