import streamlit as st
from page_csv_to_df import csv_to_df
from page_df_statistic import stat_df

# режим широкого отображения элементов streamlit
st.set_page_config(layout="wide")


# базовая функция приложения
def main():
    # выбор параметров csv файла для отображения таблицы
    tab_csv_to_df, statistic_df = st.tabs(["**Загрузка и формирование таблицы**", "**Выбор и отображение статистических данных**"])
    with tab_csv_to_df:
        df = csv_to_df()
    with statistic_df:
        if df is not None:
            stat_df(df)
        else:
            st.warning("Не выбрана таблица для отображения")

    # Отображение надписей st.tabs с немного увеличенным шрифтом 
    css = '''
        <style>
            .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
            font-size:1.1rem;
            }
        </style>
        '''

    st.markdown(css, unsafe_allow_html=True)
    

try:
    main()
except Exception as e:
    st.error(f"Ошибка при выполнении кода. {type(e).__name__} строка {e.__traceback__.tb_lineno} файл {__file__}:\n{e}")