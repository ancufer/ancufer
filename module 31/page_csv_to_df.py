import streamlit as st

import pandas as pd
import re
from io import TextIOWrapper, BytesIO


# небольшой список разделителей
list_seps = [
    ",",
    ":",
    ";"
    ]

encodings = ["utf-8", "cp1251"] # совсем небольшой список кодировки файлов


@st.cache_data()
def readcsv(uploaded_file:BytesIO, sep:str, header_row:int)->pd.DataFrame:
    df = pd.read_csv(uploaded_file, sep=sep,header=header_row)

    return df


# функция для получения таблицы из csv файла с заданными параметрами
def parameters_csv( uploaded_file:BytesIO, sep:str, max_lines:int, encode:str )->pd.DataFrame:

    # для обработки текстовых потоков
    text_wrapper = TextIOWrapper(uploaded_file, encoding=encode)
    # исключение возможной ошибки выбора кодировки          
    try:   
        lines = []
        l = 0 # счётчик считанных строк
        # считываем строки
        for line in text_wrapper:
            # так как read_csv по умолчанию пропускает пустые строки,
            # которые могут оказать и внутири данных используемых для таблиц,
            # то решил также через регулярные выражения убрать пустые строки
            if re.match("\s", line):
                continue
            
            lines.append(line)
            l +=1 
            if l == max_lines:
                break

    except UnicodeDecodeError:
        st.warning("Нет возможности открыть файл. Попробуйте выбрать другую кодировку")
        st.stop()

    def show():
        pass

    # отображаение выбранного csv файла
    st_df = pd.DataFrame({'Выбор строки с шапкой таблицы' : lines})

    # для удобства отображение через вкладки
    tab_csv, tab_df = st.tabs(["Отображение csv файла", "Отображение полученной таблицы"])

    # вкладка с выбором параметров для отображения таблицы 
    with tab_csv:
         # для дальнейшего выбора строки с шакой таблицы (так есть файлы с инфо строками до табличных данных)
        st.write("**Выберите первую строку с заголовками таблицы**")
        header_index = st.dataframe(st_df , selection_mode="single-row", on_select=show)
    
    header_row = header_index["selection"]["rows"]  
    # если строка выбрана, то используем её для отображения полученной таблицы в другой вкладке
    if len(header_row) > 0:        
        text_wrapper.seek(0)
        try:
            st.session_state["df"] = readcsv(uploaded_file, sep, header_row)
        except:
            st.session_state["warning"] = "Нет отображения таблицы с заданными параметрами."

    # вкладка для отображения таблицы
    with tab_df:
        if "warning" in st.session_state:
            st.warning(st.session_state.warning)
        elif len(header_row) < 1:
            st.warning("Выберите на левой вкладке строку с шапкой (заголовками столбцов)  для отображения табличных данных")
        elif "df" in st.session_state:
            st.dataframe(st.session_state.df.head(20)) # нет необходимости отображать всю таблицу
            return st.session_state.df

  

# так как файлы csv могут быть разные, в том числе с текстом вначале,
# описывающим табличные даннеы, то решил, что пользователь,
# пользуясь свосем небольшим инструментарием, может выбрать какие данные
# использовать для постронния таблицы
def df_from_csv(uploaded_file:BytesIO)->pd.DataFrame: 

    with st.expander("Параметры csv файла", expanded=True):
        # контейнер с выбором параметров для отображения csv таблицы
        with st.container(border=True):
            sep = st.selectbox(label="Выберите разделитель или поставьте свой", options=list_seps, accept_new_options=True)
            max_lines = st.number_input(label="Сколько строк показать (от 2 до 100)", min_value=2, max_value=100, value=20)
            encode = st.selectbox(label="Выберите кодировку файла", options=encodings)    

    if uploaded_file:
        df = parameters_csv(uploaded_file, sep, max_lines, encode )
        if df is not None:
            return df


# основная функция
def csv_to_df():

    uploaded_file = st.file_uploader("Загрузите файл с таблицей", type=["csv"])
    df = df_from_csv(uploaded_file)

    if uploaded_file:
        # очишаем состояния, при загрузке нового файла
        for key in st.session_state:
            del st.session_state[key]

    
    return df