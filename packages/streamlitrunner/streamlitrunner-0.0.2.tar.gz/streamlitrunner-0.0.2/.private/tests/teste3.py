import os
import sys
from typing import cast

import lasio
import lasio.examples
import plotly.graph_objects as go
import streamlit as st
from pandas import DataFrame
from plotly.subplots import make_subplots

sys.path.insert(0, os.path.abspath("./src"))

import streamlitrunner as sr

sr.run(client_toolbar_mode="auto")

st.set_page_config(layout="wide")


class SessionState:
    df: DataFrame

    def __contains__(self, name) -> bool:
        return hasattr(self, name)


session = cast(SessionState, st.session_state)

if "df" not in session:
    las = lasio.examples.open("6038187_v1.2.las")
    df = las.df()
    df["PROF"] = df.index


def main():
    st.button("Close", on_click=sr.close_app)
    curves = st.sidebar.multiselect("Curves", df.columns, default="CALI")
    N = len(curves)
    fig = make_subplots(
        1,
        N,
        shared_yaxes=True,
        horizontal_spacing=0.01,
        vertical_spacing=0.01,
    )
    for i, column_name in enumerate(curves):
        col = i + 1
        fig.add_trace(go.Scatter(name=column_name, y=df["PROF"], x=df[column_name]), row=1, col=col)
        fig.update_xaxes(col=col, mirror="allticks", ticks="inside", showgrid=True)
        fig.update_yaxes(col=col, mirror="allticks", ticks="inside", showgrid=True, autorange="reversed", matches="y")
    # fig.update_xaxes(fixedrange=True)
    fig.update_layout(height=1000, template="simple_white", plot_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True, theme=None)


if __name__ == "__main__":
    main()
