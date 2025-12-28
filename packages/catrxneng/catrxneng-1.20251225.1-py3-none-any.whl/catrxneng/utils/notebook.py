import os
import pickle
import pandas as pd
from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..reactors import Reactor
    from ..kinetic_models import KineticModel
    from ..simulate import Expt
    from ..plots import PlotlyPlot


class Notebook:
    expt: Optional["Expt"]
    km: Optional["KineticModel"]
    reactor: Optional["Reactor"]
    df: Optional[pd.DataFrame]
    data: Optional[dict[str, Any]]

    def __init__(self, script_path: str, descrip: str | None = None) -> None:
        self.script_path = script_path
        self.script_name = Path(script_path).stem
        self.script_dir = Path(script_path).parent
        self.path = self.script_path.replace(".py", ".html")
        self.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{self.script_name}</title>
            <meta charset="utf-8" /> 
            <style>
                body {{
                    text-align: center;
                    margin: 0 auto;
                    max-width: 1200px;
                    padding: 20px;
                }}
                h1 {{
                    margin-bottom: 30px;
                }}
                .plotly-graph-div {{
                    margin: 0 auto;
                }}
            </style>
        </head>
        <body>
            {f'<h1>{self.script_name}</h1>'}
        </body>
        </html>
        """
        if descrip:
            self.add_text_to_html(descrip)

    def add_plot_to_html(self, plot: "PlotlyPlot") -> None:
        include_plotlyjs = "inline" if "cdn.plot.ly" not in self.html else False
        plot_html = plot.fig.to_html(include_plotlyjs=include_plotlyjs)
        # head_content = plot_html.split("<head>")[1].split("</head>")[0]
        body_content = plot_html.split("<body>")[1].split("</body>")[0]
        # if html == "":
        #     html = initialize_html(script_name)
        self.html = self.html.replace(
            "</body>",
            f"<br><br>\n{body_content}\n<br>\n</body>",
        )

    @staticmethod
    def add_line_to_text(text: str, *args, color: str | None = None) -> str:
        lines = text.split("<br>") if text else []
        for line in args:
            if color:
                line = f'<span style="color: {color};">{line}</span>'
            lines.append(line)
        return "<br>".join(lines)

    def add_text_to_html(self, text: str) -> None:
        # Replace <br> with actual line breaks using block elements
        lines = text.split("<br>")
        lines_html = "".join(
            f'<p style="margin: 5px 0;">{line}</p>' for line in lines if line.strip()
        )
        centered_text = f'<div style="text-align: center;">{lines_html}</div>'
        self.html = self.html.replace(
            "</body>", f" <br>\n {centered_text}\n <br>\n</body>"
        )

    def add_table_to_html(self, table: str) -> None:
        centered_table = f'<div style="display: flex; justify-content: center;"><style>th, td {{ text-align: center; padding: 10px; }}</style>{table}</div>'
        self.html = self.html.replace(
            "</body>", f" <br>\n {centered_table}\n <br>\n</body>"
        )

    def save_html(self) -> None:
        with open(self.path, "w") as f:
            f.write(self.html)

    def save_dataframe(self, var_name: str, df: pd.DataFrame) -> None:
        filename = f"{self.script_name}_{var_name}.parquet"
        full_path = os.path.join(self.script_dir, filename)
        df.to_parquet(full_path)

    def save_pickle(self, var_name: str, data: Any) -> None:
        filename = f"{self.script_name}_{var_name}.pkl"
        full_path = os.path.join(self.script_dir, filename)
        with open(full_path, "wb") as f:
            pickle.dump(data, f)

    def load_dataframe(self, var_name: str) -> Optional[pd.DataFrame]:
        parquet_filename = f"{self.script_name}_{var_name}.parquet"
        parquet_full_path = os.path.join(self.script_dir, parquet_filename)
        try:
            return pd.read_parquet(parquet_full_path)
        except (FileNotFoundError, Exception):
            return None

    def load_pickle(self, var_name: str) -> Optional[Any]:
        pkl_filename = f"{self.script_name}_{var_name}.pkl"
        pkl_full_path = os.path.join(self.script_dir, pkl_filename)
        try:
            with open(pkl_full_path, "rb") as f:
                return pickle.load(f)
        except (FileNotFoundError, pickle.UnpicklingError, EOFError):
            return None
