import streamlit as st
import pandas as pd

from pandas.api.types import (
    is_datetime64_any_dtype, 
    is_numeric_dtype
)

import plotly.graph_objects as go
from io import StringIO, BytesIO




# список для выбора типа отображения графика (для двух столбцов)
list_graphs = ["Линейный график",  
               "Диаграмма рассеяния" , 
               "Столбчатая диаграмма", 
               "Совместное распределение (гистограммы: одна над другой)",
               "Совместное распределение (гистограммы: одна наложена на другую)"
               ]
# dict_graph_one_col = {"Гистограмма" : go.Histogram}




# функция для построения графиков отображает заданный в параметрах график 
# и возвращает это буффер этого отображение
def graph_from_func(graph_func:go, x_title="", y_title="")->StringIO:
    fig = go.Figure()
    fig.add_trace(graph_func)
    fig.update_layout(title=f'График зависимости {y_title} от {x_title}', xaxis_title=x_title, yaxis_title=y_title)
    
    st.plotly_chart(fig)    
    buffer_html = StringIO()
    fig.write_html(buffer_html)

    return buffer_html



# функция определения типов
def default_cols_types(df:pd.DataFrame)->tuple[pd.DataFrame, list[str], list[str]]:

    list_cols_dates = []
    list_cols_numbers = []
    # цикл по всем столбцам
    for col in df.columns:
        # проверка столбец дата или нет
        if is_datetime64_any_dtype(df[col]):
            df[col] = pd.to_datetime(df[col])
            list_cols_dates.append(col)
        # проверка столбец числовой или нет
        elif is_numeric_dtype(df[col]):
           list_cols_numbers.append(col)

        
    return df, list_cols_dates, list_cols_numbers     



# функция простановки типов
def cols_types(df:pd.DataFrame)->pd.DataFrame:

    df, list_cols_dates, list_cols_numbers = default_cols_types(df)

    # Возможность пользовательского выбора форматов столбцов
    with st.expander(label="Изменение форматов столбцов"):
        options_cols_dates = st.multiselect(
            "Вы можете изменить столбцы выбранные с форматом ДАТА ВРЕМЯ",
            df.columns,
            default=list_cols_dates
        )

        options_cols_numbers = st.multiselect(
            "Вы можете изменить столбцы выбранные с форматом ЧИСЛО",
            df.columns,
            default=list_cols_numbers
        )

    # определение выбрал ли пользователь новые столбцы с форматом ДАТА
    new_cols_dates = set(options_cols_dates) ^ set(list_cols_dates)
    if new_cols_dates:
        list_cols_dates = options_cols_dates

     # определение выбрал ли пользователь новые столбцы с форматом ЧИСЛО
    new_cols_numbers = set(options_cols_numbers) ^ set(list_cols_numbers)
    if new_cols_numbers:
        list_cols_numbers = options_cols_numbers

    # сохраняем форматы стобцов в session_state
    st.session_state["list_cols_dates"] = list_cols_dates
    st.session_state["list_cols_numbers"] = list_cols_numbers
    
    # словарь со столбцами, в  которые не удалось проставить
    # выбранные пользователем форматы
    dict_exceptions = {} 
    # простановка выбранных форматов
    for col in df.columns:
        if col in list_cols_dates:
            try:
                df[col] = pd.to_datetime(df[col])
            except:
                dict_exceptions[col] = "ДАТА ВРЕМЯ"
        elif col in list_cols_numbers:
            try:
                df[col] = df[col].astype(float)
            except:
                dict_exceptions[col] = "ЧИСЛО"
        else:
            try:
             df[col] = df[col].astype(str)
            except:
                dict_exceptions[col] = "СТРОКА"

    # если есть столбцы, 
    # в которые не удалось проставить
    # выбранные пользователем форматы
    if bool(dict_exceptions):
        with st.expander("Ошибки форматов выбранных столбцов", expanded=True):
            st.warning(f"Следующие столбцы не изменили свой формат {dict_exceptions}")

    return df



# чтобы у пользователя
# была возможность получить Гистограмму для любого столбца,
# при этом выводится информация о релевантности построенного графика
def select_one_col(df:pd.DataFrame, col:str):

    # если значение числовое
    if col in st.session_state.list_cols_numbers:
        with st.expander(f"Статистические данные для числового столбца {col}", expanded=True):
             with st.container(border=True):
                st.write(f"Среднее значение - {df[col].mean()}")
                st.write(f"Медиана - {df[col].median()}")
                st.write(f"Среднеквадратичное отклонение - {df[col].std()}")

    # Проверка на релевантность нечисловых столбцов 
    # если кол-во уникальных нечисловых значений 
    # по отношению в количеству всех значений меньше  10% и их кол-во меньше 1000
    elif ( len(df[col].unique()) / df.shape[0] ) < 0.1 and len(df[col].unique()) < 1_000:
        st.write("**Возможно гистограмма для выбранного нечисловго значения будет иметь смысл для дальнейшего анализа**")
    else:
        st.write("**Вряд ли гистограмма для выбранного нечисловго значения будет иметь смысл для дальнейшего анализа**")
     
        
    # построение Гистограммы, с помощью общей функции используемой для построений     
    buffer_html = graph_from_func(
        go.Histogram(
            { "x" :  df[col].to_list() }, 
            nbinsx = 50,
            marker_color='blue'
            ),
        col,       
    )
    
    data_html = BytesIO( buffer_html.getvalue().encode("utf-8") )
    del buffer_html
    # соранение графика ( с сохраненеим интерактивного режима )
    btn = st.download_button("Выгрузка html", data=data_html, file_name="graph.html")
    if btn:
        del data_html



# чтобы у пользователя
# была возможность построить любой график для любого столбца,
# при этом выводится информация о релевантности построенного графика
def select_two_cols(df:pd.DataFrame, cols:dict[str:str]):
    # задание x, y определяется при последовательном 
    # выборе столбцов (сначал для X, потом для Y)
    # и отображается пользователю под выбираемой таблицей
    col_x = cols["X"]
    col_y = cols["Y"]

    #условия по типам данных столбцов
    w_t = "**Возможно график будет иметь смысл для дальнейшего анализа (для выбранных значений)**"
    w_f = "**Вряд ли график будет иметь смысл для дальнейшего анализа (для выбранных значений)**"
   
    # Проверка на релевантность нечисловых столбцов 
    # если кол-во уникальных нечисловых значений по осям X и Y
    # по отношению в количеству всех значений меньше  10% и их кол-во меньше 1000
    q_x = not(  ( len(df[col_x].unique()) / df.shape[0] ) < 0.1 and len(df[col_x].unique()) < 1_000  )
    q_y = not(  ( len(df[col_y].unique()) / df.shape[0] ) < 0.1 and len(df[col_y].unique()) < 1_000  )

    n_x = col_x in st.session_state.list_cols_numbers # проверка на тип ЧИСЛО данных для оси X
    n_y = col_y in st.session_state.list_cols_numbers # проверка на тип ЧИСЛО данных для оси Y
    d_x = col_x in st.session_state.list_cols_dates # проверка на тип ДАТА данных для оси X
    d_y = col_y in st.session_state.list_cols_dates # проверка на тип ДАТА данных для оси Y

    # выбор типа графика
    go_graf = st.selectbox("Выберите вид графика, который вы хотите построить", list_graphs, index=None)

    buffer_html = None

    
    if go_graf == "Линейный график":
        # проверка на релевантность выбранных столбцов графику
        if ( not (n_x or d_x) ) or (not n_y) or d_y:
            st.write(w_f) # сообщение о нерелевантности
            
        buffer_html = graph_from_func(
                go.Scatter(
                    { "x" :  df[col_x].to_list(), "y" : df[col_y].to_list() }, 
                    mode='lines+markers+text',
                    text=[col_x, col_y],
                    marker = {'color' : 'green', 'size' : 15} 
                    ),
            col_x,
            col_y
            )


    elif go_graf == "Диаграмма рассеяния":
        # проверка на релевантность выбранных столбцов графику
        if ( not (n_x or d_x) ) or (not n_y) or d_y:
            st.write(w_f) # сообщение о нерелевантности
           
        buffer_html = graph_from_func(
                go.Scatter(
                    { "x" :  df[col_x].to_list(), "y" : df[col_y].to_list() }, 
                    mode='markers+text',
                    text=[col_x, col_y],
                    marker={'color' : 'green', 'size' : 15} 
                    ),
            col_x,
            col_y
            )


    elif go_graf == "Столбчатая диаграмма":
        # проверка на релевантность выбранных столбцов графику
        if ( n_x or d_x or d_y or q_x  or (not n_y) ):
            st.write(w_f) # сообщение о нерелевантности данных (выбранных столбцов) выбранному графику
                
        buffer_html = graph_from_func(
                go.Bar(
                    { "x" :  df[col_x].to_list(), "y" : df[col_y].to_list() }, 
                    marker={'color' :'blue'}
                    ),
            col_x,
            col_y
            )


    elif go_graf == "Совместное распределение (гистограммы: одна над другой)":
        # проверка на релевантность выбранных столбцов графику
        if (  ( not n_x and q_x ) or ( not n_y and q_y ) ):
            st.write(w_f) # сообщение о нерелевантности данных (выбранных столбцов) выбранному графику
        elif (  ( not n_x and n_y ) or ( n_x and not n_y ) ):
            st.write(w_f) # сообщение о нерелевантности данных (выбранных столбцов) выбранному графику
        elif (  ( not n_x and not q_x ) and ( not n_y and not q_y ) ):
            st.write(w_t) # сообщение о возможной релевантности данных (выбранных столбцов) выбранному графику
  
        fig = go.Figure()
        fig.add_trace( go.Histogram({ "x" :  df[col_x].to_list() }, name=col_x, marker_color='blue', opacity=0.7) )
        fig.add_trace( go.Histogram({ "x" :  df[col_y].to_list() }, name=col_y, marker_color='orange',opacity=0.7) )

        fig.update_layout(barmode='stack',) # , barmode="stack" barmode='overlay'

        st.plotly_chart(fig)
        buffer_html = StringIO()
        fig.write_html(buffer_html)
        

    elif go_graf == "Совместное распределение (гистограммы: одна наложена на другую)":
                # проверка на релевантность выбранных столбцов графику
        if (  ( not n_x and q_x ) or ( not n_y and q_y ) ):
            st.write(w_f) # сообщение о нерелевантности данных (выбранных столбцов) выбранному графику
        elif (  ( not n_x and n_y ) or ( n_x and not n_y ) ):
            st.write(w_f) # сообщение о нерелевантности данных (выбранных столбцов) выбранному графику
        elif (  ( not n_x and not q_x ) and ( not n_y and not q_y ) ):
            st.write(w_t) # сообщение о возможной релевантности данных (выбранных столбцов) выбранному графику
  
        fig = go.Figure()
        fig.add_trace( go.Histogram({ "x" :  df[col_x].to_list() }, name=col_x, marker_color='blue', opacity=0.7) )
        fig.add_trace( go.Histogram({ "x" :  df[col_y].to_list() }, name=col_y, marker_color='orange',opacity=0.7) )

        fig.update_layout(barmode='overlay',) # , barmode="stack" barmode='overlay'

        st.plotly_chart(fig)
        buffer_html = StringIO()
        fig.write_html(buffer_html)
    



    # если выбран график и возвращено содержимое,
    # то это содержимое можно сохранить в html файл (поддерживает интерактивность)
    if go_graf and buffer_html:
        data_html = BytesIO( buffer_html.getvalue().encode("utf-8") )
        del buffer_html
        # соранение графика ( с сохраненеим интерактивного режима )
        btn = st.download_button("Выгрузка html", data=data_html, file_name="graph.html")
        if btn:
            del data_html

       

# функиция построения графиков, 
# в зависимости от того выбран один или два столбца        
def build_graphs(df:pd.DataFrame, cols:dict[str:str]):

    # если выбран только один столбец (X)
    # то строим график по одному столбцу,
    # иначе строим графики по двум столбцам
    if not "Y" in cols:  
        select_one_col(df, cols["X"])
    else:
        select_two_cols(df, cols)



# Фунция для выбора отображанмых на графиках столбцов
def select_cols(df:pd.DataFrame)->dict[str:str]:

    cols_dict = dict() # словарь для соответствия выбранных столбцов координатам

    # раскрытие для выбора столбцов
    with st.expander(label="Выбор столбцов для аналиха на графиках", expanded=True):
        # понятней для пользователя, если он сможет выбирать
        # для одного или двух столбцов отображать график
        xy = st.radio(
            label="Выберите один столбец (X) или два столбца (X и Y) требуются для анализа на графиках", 
            options=["X", "X и Y"])

        # выбор столбцов
        col_x = st.selectbox(label="Выбор одного столбца (X)", options=df.columns, index=None, placeholder="Пока ничего не выбрано")                
        col_y = st.selectbox(
            label="Выбор второго столбца (Y)", 
            options=df.columns, 
            index=None, 
            placeholder="Пока ничего не выбрано",
            disabled=( xy != "X и Y") # если пользователем выбран режим только выбора столбца X
            )

        
    # при выборе столбцов (нет необходимости отображать всю таблицу)
    st.dataframe(  pd.concat( (df.head(20), df.tail(20)) )  )

    # заполнение данных словаря и его возврат
    # значение Y заполняется только если выбран режим заполнения "X и Y"
    if col_y and xy == "X и Y":
        cols_dict["Y"] = col_y
    if col_x:
        cols_dict["X"] = col_x  
        return cols_dict



# функция  df
def stat_df(df:pd.DataFrame):
    # вкладки для выбора столбцов и для отображения графиков для выбранныз столбцов
    tab_fornat_cols, tab_graph = st.tabs(
        ["Определение форматов столбцов и выбор столбцов для построения графиков", "📈 Построение графиков"]
        ) 
    with tab_fornat_cols:
        # df с определёнными типами столбцов 
        df = cols_types(df)
        # выбор столбцов
        selected_cols = select_cols(df)
    with tab_graph:
        # если есть выбранные столбцы, то строим графики, 
        # иначе сообщение, что столбцы не выбраны
        if selected_cols:
            build_graphs(df, selected_cols)
        else:
            st.warning("Надо выбрать один (X) или два столбца (X и Y)")