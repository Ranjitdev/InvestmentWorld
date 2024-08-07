from src.YahooFianance import *
from src.Data_plot import *
from src.Data_ingesion import *
from src.Bybit_manager import *
from src.utils import *
import streamlit as st


class InitializeApp:
    def __init__(self):
        self.full_tickers_data = DataIngesion().get_tickers_data()
        self.sym_tickers_data = DataIngesion().get_tickers_data(market_cap=False)

    def home(self):
        try:
            pass
        except Exception as e:
            st.warning(f'Processing Error: {e}', icon='⚠')

    def nse(self):
        try:
            check_internet()
        except:
            st.warning('⚠ Not connected to internet, Please connect to 🌐internet and 🔄refresh')
        try:
            data = self.sym_tickers_data
            col1, col2, col3 = st.columns(3)
            with col1:
                name_selection = st.selectbox('Stock', ['Select'] + list(data['Name']))
            with col2:
                interval = st.selectbox('Interval', YfinanceConfigure.valid_intervals)
            with col3:
                period = st.selectbox('Period', YfinanceConfigure.valid_periods)
            col4, col5, col6 = st.columns(3)
            with col4:
                start = st.date_input('Start Date', None, min_value=dt(1970, 1, 1), max_value=dt.now())
            with col5:
                end = st.date_input('End Date', None, min_value=dt(2000, 1, 1), max_value=dt.now())
            if name_selection != 'Select':
                check_internet()
                ticker_sym = str(data[data['Name'] == name_selection]['Symbol'].item()) + '.NS'
                data = YfinanceData(ticker_sym, interval, period, start, end).get_data()
                info = YfinanceData(ticker_sym, interval, period, start, end).stock_info()
                tab1, tab2, tab3 = st.tabs(['Excel Data', 'Graphs', 'Company Info'])
                with tab1:
                    st.dataframe(data)
                with tab2:
                    st.caption('OHLC')
                    st.line_chart(data[['Open', 'High', 'Low', 'Close']])
                    st.caption('Volume')
                    st.bar_chart(data['Volume'])
                with tab3:
                    st.write(info)
        except Exception as e:
            st.warning(f'Processing Error: {e}', icon='⚠')
            raise CustomException(e, sys)

    def bybit(self):
        try:
            check_internet()
        except:
            st.warning('⚠ Not connected to internet, Please connect to 🌐internet and 🔄refresh')
        with st.form('form_1'):
            st.header('Search for Short or Long trade')

            col1, col2, col3 = st.columns(3)
            with col1:
                start_date = st.date_input(
                    'Start Date', value='today', min_value=dt(2000, 1, 1), max_value=dt.now()
                )
                start_hour = st.slider('Start hour', value=5, min_value=0, max_value=23)
                start_min = st.slider('Start min', value=30, min_value=0, max_value=55, step=5)

            with col2:
                end_date = st.date_input(
                    'End Date', value='today', min_value=dt(2000, 1, 1), max_value=dt.now()
                )
                end_hour = st.slider('End hour', value=9, min_value=0, max_value=23)
                end_min = st.slider('End min', value=30, min_value=0, max_value=55, step=5)

            with col3:
                selection = st.selectbox('Select trade type', ['Both', 'Short', 'Long'])
                tp_percent = st.number_input('Take Profit %', min_value=0.10, max_value=100.00, value=0.25, step=0.05)
                sl_percent = st.number_input('Stop Loss %', min_value=0.10, max_value=100.00, value=0.50, step=0.05)

            if st.form_submit_button('Start Now'):
                try:
                    check_internet()
                    start_datetime = dt(start_date.year, start_date.month, start_date.day, start_hour, start_min)
                    end_datetime = dt(end_date.year, end_date.month, end_date.day, end_hour, end_min)
                    if start_datetime < end_datetime:
                        initiate_trade = InitiateBybitTrade(start_datetime, end_datetime, tp_percent, sl_percent)
                        make_textdoc('bybit_datetime', str(dt.now().strftime("%d/%b/%Y %H:%M:%S.%f %p")))

                        if selection == 'Short':
                            with st.spinner('Wait while checking...'):
                                data = initiate_trade.bitcoin_trade(selection)
                                DataIngesion().update_bybit_data(data)
                                # DataIngesion().update_gsheet(data)
                                # DataIngesion().update_mysql_server()
                            st.dataframe(data)
                        if selection == 'Long':
                            with st.spinner('Wait while checking...'):
                                data = initiate_trade.bitcoin_trade(selection)
                                DataIngesion().update_bybit_data(data)
                                # DataIngesion().update_gsheet(data)
                                # DataIngesion().update_mysql_server()
                            st.dataframe(data)
                        if selection == 'Both':
                            with st.spinner('Wait while checking...'):
                                data = initiate_trade.bitcoin_trade(selection)
                                # data.to_csv(DataIngesionConfig.bybit_test_data, index=False)
                                DataIngesion().update_bybit_data(data)
                                # DataIngesion().update_gsheet(data)
                                # DataIngesion().update_mysql_server()
                            st.dataframe(data)
                    else:
                        st.warning('Check Start date and End date')
                except Exception as e:
                    logging.error(e)
                    st.error(f'⚠ Got Error {e}')
                    raise CustomException(e, sys)
            st.caption(f'{dt.now().strftime("%d/%b/%Y %H:%M:%S.%f %p")}')

        try:
            st.caption(f'Old data from: {read_textdoc("bybit_datetime")}')
            tab1, tab2 = st.tabs(['Data', 'Charts'])
            with tab1:
                st.dataframe(DataIngesion().get_bybit_data())
            with tab2:
                pass
                # DataPlot(DataIngesion().get_bybit_data()).bybit_win_loss_bar_chart()
        except Exception as e:
            print(f'Error {e}')







