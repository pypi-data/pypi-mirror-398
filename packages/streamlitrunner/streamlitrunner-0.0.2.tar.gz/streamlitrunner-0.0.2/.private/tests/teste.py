import os
import pprint
import sys

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

sys.path.insert(0, os.path.abspath("./src"))

import streamlitrunner as sr

sr.run()

fig = make_subplots(rows=1, cols=2)

fig.add_trace(go.Scatter(x=[1, 2, 3], y=[4, 5, 6]), row=1, col=1)

fig.add_trace(go.Scatter(x=[20, 30, 40], y=[50, 60, 70]), row=1, col=2)

fig.update_layout(height=600, width=800, title_text="Side By Side Subplots")
# fig.show()
st.button("Close", on_click=sr.close_app)
dado = st.plotly_chart(fig, theme=None, on_select="rerun")
os.system("cls")
pprint.pprint(dado)
