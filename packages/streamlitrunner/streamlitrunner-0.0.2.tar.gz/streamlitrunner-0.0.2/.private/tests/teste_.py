import os
import sys
from typing import cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sys.path.insert(0, os.path.abspath("../../src"))

import streamlit as st

import streamlitrunner as sr

st.set_page_config(layout="wide")

sr.run()


class SessionState:
    xdata: list[str]
    ydata: list[str]
    rodado: bool
    df: pd.DataFrame
    minhaLista: list[str]

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)

    def __iter__(): ...


session = cast(SessionState, st.session_state)


# %% geracao de dados


if "rodado" not in session:
    index = np.linspace(0, 1000, 1000)
    print(len(index))
    data = [index]
    for func in [np.sin, np.cos, np.tan]:
        data.append(func(index))

    data.append(np.random.rand(len(index)))

    session.df = pd.DataFrame(
        {
            "indice": data[0],
            "seno": data[1],
            "cosseno": data[2],
            "tangente": data[3],
            "random": data[4],
        }
    )
    session.minhaLista = []
    session.rodado = True


# %%


dados = ["indice", "seno", "cosseno", "tangente", "random"]

session.xdata = st.sidebar.multiselect("X data", dados, default=dados[0])
session.ydata = st.sidebar.multiselect("Y data", dados, default=dados[0])


def nada(): ...


if st.sidebar.checkbox("Usar Pyplot"):
    fig, ax = plt.subplots(nrows=len(session.ydata), ncols=len(session.xdata), sharex=True, sharey=True, figsize=(10, 5))
    ax = np.array(ax).reshape(len(session.ydata), len(session.xdata))
    for j, x in enumerate(session.xdata):
        for i, y in enumerate(session.ydata):
            ax[i, j].plot(session.df[x].values, session.df[y].values)

    st.pyplot(fig)


else:
    fig = make_subplots(
        rows=len(session.ydata),
        cols=len(session.xdata),
        shared_xaxes=True,
        shared_yaxes=True,
        horizontal_spacing=0.01,
        vertical_spacing=0.01,
    )

    for x in session.xdata:
        for y in session.ydata:
            fig.add_trace(
                go.Scatter(y=session.df[y].values, x=session.df[x].values, mode="markers+lines"),
                col=session.xdata.index(x) + 1,
                row=session.ydata.index(y) + 1,
            )

    # if len(session.xdata) == 1:
    #     fig.update_xaxes(matches="x", showline=True, mirror="allticks", ticks="inside", showgrid=True)
    # else:
    #     fig.update_xaxes(showline=True, mirror="allticks", ticks="inside", showgrid=True)

    # if len(session.ydata) == 1:
    #     fig.update_yaxes(matches="y", showline=True, mirror="allticks", ticks="inside", showgrid=True)
    # else:
    #     fig.update_yaxes(showline=True, mirror="allticks", ticks="inside", showgrid=True)

    st.button("Close")
    fig.update_layout(width=1800, height=900, template="simple_white", plot_bgcolor="white")
    dado = st.plotly_chart(fig, key="iris", theme=None, use_container_width=True, on_select=nada)
    print(dado)
