import streamlit as st
import pandas as pd
import plotly.express as px
from default_data import dict_en_ru, dict_en_ru_city, dict_ru_ru


def line_graph(data_graph: pd.DataFrame, selected_city_names: list, selected_data: str)->px.line:  

    fig = px.line(
        data_frame = data_graph,
        x = "date",
        y = selected_data,
        color = "city",
        color_discrete_sequence=["green", "orange", "blue", "violet"],
        labels=dict_en_ru,
        title= f'Зависимость показателя {dict_en_ru[selected_data]} от даты для {selected_city_names}',
        # width=1200, 
        height=800
    )

    return fig 



def hist_graph(data_graph: pd.DataFrame, selected_city_names: list, selected_data: str)->px.histogram:

    fig = px.histogram(
        data_frame = data_graph,
        x = "date",
        y = selected_data,
        color = "city",
        color_discrete_sequence=["green", "orange", "blue", "violet"],
        labels=dict_en_ru,
        title= f'Зависимость усреднённого (avg of) показателя {dict_en_ru[selected_data]} от даты для {selected_city_names}',
        histfunc="avg",
        barmode="group",
        nbins = 25,
        # width=1200, 
        height=800
    )

    return fig 



def box_graph(data_graph: pd.DataFrame, selected_city_names: list, selected_data: str)->px.box:    

    fig = px.box(
        data_frame = data_graph,
        x = "city",
        y = selected_data,
        color = "city",
        color_discrete_sequence=["green", "orange", "blue", "violet"],
        labels=dict_en_ru,
        title= f'Распределение показателя {dict_en_ru[selected_data]} для {selected_city_names}',  
        # width=1200, 
        height=800
    )

    return fig



def bar_graph(data_graph: pd.DataFrame, selected_city_names: list, selected_data: str)->px.bar:

    fig = px.bar(
        data_frame = data_graph,
        x = "date",
        y = selected_data,
        color = "city",
        color_discrete_sequence=["green", "orange", "blue", "violet"],
        labels=dict_en_ru,
        title= f'Зависимость показателя {dict_en_ru[selected_data]} от даты для {selected_city_names}',
        barmode="group",
        # width=1200, 
        height=800
    )

    return fig

    

# список для выбора типа отображения графика
dict_graphs = {
                "Линейный график" : line_graph,  
                "Гистограмма" : hist_graph,
                "Коробчатая диаграмма" : box_graph,
                'Столбчатая диаграмма' : bar_graph
            }



def graph_df(df):
    df_graph = df.copy()
    df_graph = df_graph[['date', 'city', 'avg_temp', 'total_precip', 'avg_wind', 'is_rainy']]

    graph_key = None
    
    with st.expander(label="Настройка данных для отображения графиков", expanded=True):
        selected_city_ru = st.multiselect(
                    "Выберите город или города",
                    dict_en_ru_city.values(),
                    default=list(dict_en_ru_city.values()),
                )
        selected_data_ru = st.selectbox(
                    "Выберите параметр",
                   ["Температура", "Количество осадков", "Ветер", "Признак дождя"],
                    )
        if selected_city_ru and selected_data_ru:
            # для перевода выбранных названий в столбцы df
            selected_city = list(filter(lambda key: dict_en_ru_city[key] in (selected_city_ru), dict_en_ru_city))          
            selected_data = list(filter(lambda key: dict_en_ru[key] == selected_data_ru, dict_en_ru))[0]

            # для читаемых данных ввода и данных на графиках
            selected_city_names = ", ".join([dict_ru_ru[c] for c in selected_city_ru])  
           
            data_graph = df_graph[df_graph.city.isin(selected_city)] # dataframe для графика
            
            graph_key = st.selectbox(
                      "Выберите график",
                      dict_graphs.keys()
                )

    if graph_key:
        fig = dict_graphs[graph_key](data_graph, selected_city_names, selected_data)
        st.plotly_chart(fig)