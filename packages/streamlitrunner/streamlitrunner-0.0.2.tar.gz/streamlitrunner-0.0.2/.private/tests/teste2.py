import os
import sys

sys.path.insert(0, os.path.abspath("./src"))

import plotly.express as px
import streamlit as st

import streamlitrunner as sr

sr.run()

df = px.data.iris()

fig = px.scatter(df, x="sepal_width", y="sepal_length", facet_col="species")
fig.update_xaxes(fixedrange=True)


st.plotly_chart(fig)
