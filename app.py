import streamlit as st
from src.Construct_app import *

with st.sidebar:
    selection = st.radio(' ', [
        'Home', 'NSE', 'Trade on Bybit'
    ])

if selection == 'Home':
    InitializeApp().home()

elif selection == 'NSE':
    InitializeApp().nse()

elif selection == 'Trade on Bybit':
    InitializeApp().bybit()





