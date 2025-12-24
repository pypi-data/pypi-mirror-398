import os
import sys

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

sys.path.insert(0, os.path.abspath("./src"))

import streamlitrunner as sr

sr.run()

st.set_page_config(layout="wide")
dados = ["indice", "seno", "cosseno", "tangente", "random"]
st.sidebar.multiselect("X data", dados, default=dados[0])
df = px.data.iris()  # iris is a pandas DataFrame

fig = make_subplots(
    rows=1,
    cols=2,
    shared_xaxes=True,
    shared_yaxes=True,
    horizontal_spacing=0.01,
    vertical_spacing=0.01,
)
# fig = px.scatter(df, x="sepal_width", y="sepal_length")
fig.add_trace(
    go.Scatter(x=df["sepal_width"], y=df["sepal_length"], mode="markers+lines"),
    row=1,
    col=1,
)

def teste():
    ...

fig.update_layout(width=1800, height=900, template="simple_white", plot_bgcolor="white")
st.button("Close", on_click=sr.close_app)
event = st.plotly_chart(fig, key="iris", theme=None, on_select=teste,use_container_width=True)

# event
