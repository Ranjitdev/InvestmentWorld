import streamlit as st
from src.ConstructApp import *

with st.sidebar:
    selection = st.radio(' ', [
        'Home', 'NSE Today', 'NSE Historical',  'USD Bitcoin', 'Bybit',  'News', 'Overview', 'File Viewer'
    ])

if selection == 'Home':
    InitializeApp().home()

elif selection == 'NSE Today':
    InitializeApp().today()

elif selection == 'NSE Historical':
    InitializeApp().historical()

elif selection == 'USD Bitcoin':
    InitializeApp().bitcoin()

elif selection == 'Bybit':
    InitializeApp().bybit()

elif selection == 'News':
    pass

elif selection == 'Overview':
    pass

elif selection == 'File Viewer':
    InitializeApp().file_viewer()

