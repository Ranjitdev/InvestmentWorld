from src.Data_ingesion import *
from src.utils import *
import seaborn as sns
from matplotlib import pyplot as plt
import streamlit as st


class DataPlot:
    def __init__(self, data):
        self.__data = data

    def bybit_win_loss_bar_chart(self) -> None:
        try:
            fig, ax = plt.subplots(figsize=(20, 10))
            sns.barplot(
                self.__data, y='Win Loss No Trade', x='Day', estimator='sum', palette='bright', errorbar=None, ax=ax
            )
            st.pyplot(fig)
            plt.close(fig)
        except Exception as e:
            raise CustomException(e, sys)






