import os
import sys
from typing import cast

import lasio
import lasio.examples
import plotly.graph_objects as go
import streamlit as st
from pandas import DataFrame
from plotly.subplots import make_subplots

sys.path.insert(0, os.path.abspath("../../src"))

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



def main0():
    import numpy as np
    import plotly.graph_objects as go

    st.button("Close", on_click=sr.close_app)
    # Create figure
    fig = go.Figure()

    # Add traces, one for each slider step
    for step in np.arange(0, 5, 0.1):
        fig.add_trace(
            go.Scatter(
                visible=False,
                line=dict(color="#00CED1", width=6),
                name="𝜈 = " + str(step),
                x=np.arange(0, 10, 0.01),
                y=np.sin(step * np.arange(0, 10, 0.01))))

    # Make 10th trace visible
    fig.data[10].visible = True

    # Create and add slider
    steps = []
    for i in range(len(fig.data)):
        step = dict(
            method="update",
            args=[{"visible": [False] * len(fig.data)},
                {"title": "Slider switched to step: " + str(i)}],  # layout attribute
        )
        step["args"][0]["visible"][i] = True  # Toggle i'th trace to "visible"
        steps.append(step)

    sliders = [dict(
        active=10,
        currentvalue={"prefix": "Frequency: "},
        pad={"t": 50},
        steps=steps
    )]

    fig.update_layout(
        sliders=sliders,height=1000, template="simple_white", plot_bgcolor="white"
    )

    st.plotly_chart(fig, use_container_width=True, theme=None)



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
    main0()
