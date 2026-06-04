import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta, time
from default_data import dict_en_ru, dict_en_ru_city, dict_ru_ru, rolling_mean_days


# для дальнейшего использования для прогнозирования 
# (выполнение методом линейной регрессии по зависмости
# выбранного параметра от количества дней с даты первых данных)

def df_add_cols(df_pandas: pd.DataFrame)->pd.DataFrame:

    df_pandas['date'] = pd.to_datetime(df_pandas['date'])
    # сортируем данные по городу и дате
    df_pandas = df_pandas.sort_values(by=['city', 'date'])
    # для каждого города создаём признак отличия в днях между текущей и предыдущей датой
    # df_pandas['diff_days'] = df_pandas.groupby('city')['date'].diff().dt.days.fillna(0)
    df_pandas['diff_days'] = df_pandas.groupby('city')['date'].diff().dt.days.fillna(0)  
    # для каждого города создаём признак дней между текущей датой и датой с первыми данными
    df_pandas['X'] = df_pandas.groupby('city')['diff_days'].cumsum().astype(int)
    # у3бираем уже ненужный признак
    df_pandas.drop('diff_days', axis=1, inplace=True)

    return df_pandas



# Метод наименьших квадаратов для линейной регресии
# (расчётный способ)
# параметры функции, данные зависимости y от x
# возвращаемые значения коэффициенты линейной регрессии для выраженеия y = a * x + b

def mnk(X : np.array, Y : np.array)->tuple[float, float]:
       
    n = len(X)
    xy = X @ Y
    x_2 = X @ X
    x_sum = X.sum()
    y_sum = Y.sum()   

    a = (n * xy - x_sum * y_sum) / (n * x_2 - x_sum ** 2) 
    b = (y_sum - a * x_sum) / n

    return a, b



# Метод наименьших квадаратов для линейной регресии
# (numpy способ)
def mnk_np(X, Y):
    return np.polyfit(X, Y, 1)



# функция создаёт итоговый dataframe
# для построения графика с настоящими и прогнозируемыми данными (линейная регрессия)
# параметры функции
# df - Исходный DataFrame
# selected_city - выбранный город для прогнозирования
# selected_data_col - выбранный параметр для прогнозирования
# date_first_predict - дата первого прогноза
# days_data - какое количество данных используется для расчета прогноза
# days_predict - на какое количество днеей нужно сделать прогноз
# rolling_mean_days - сколько дней используется для сглаживания данных

def predict_data(
    df: pd.DataFrame, 
    selected_city: str, 
    selected_data_col: str,
    date_first_predict : datetime.date,
    days_data: int,
    days_predict: int,
    rolling_mean_days: int = rolling_mean_days 
    )->pd.DataFrame:

    # задание df, используемого для прогнозирования метод линейно регрессии 
    df_pandas = df_add_cols(df)     
    
    # до какой даты будет сделан прогноз
    date_last_predict = date_first_predict + timedelta(days=days_predict - 1)

    # выделение выбранного города и 
    # данных до даты последнего прогноза (для удобства построения графиков)
    mask_data = df_pandas['date'] <= date_last_predict
    mask_city = df_pandas.city == selected_city

    df_pandas_data = df_pandas[mask_data & mask_city].reset_index(drop=True)
    # используем метод скользящей стредней
    df_pandas_data['Y'] = df_pandas_data[selected_data_col].rolling(rolling_mean_days).mean()

    # первая дата, с которой используются данные для прогноза
    date_first_data = date_first_predict - timedelta(days=days_data)
    # для выделения данных для прогноза
    mask_data = (df_pandas_data['date'] >= date_first_data) & (df_pandas_data['date'] < date_first_predict)
    X_first = df_pandas_data[mask_data].X.iloc[0] # первый параметр X используемый для построения линейной регрессии
    X_last = df_pandas_data[mask_data].X.iloc[-1] # последний параметр X используемый для построения линейной регрессии
    # print(X_first, X_last)


    RD = df_pandas_data[selected_data_col].to_numpy()
    # Столбец с признаками historical/forecast data open-meteo.com
    DD = df_pandas_data['Данные']
    # при выборке данных учитываем, что используем метод скользящей средней
    XD, YD = df_pandas_data.X.iloc[rolling_mean_days - 1 : ].to_numpy(), df_pandas_data.Y.loc[rolling_mean_days - 1 : ].to_numpy()
    D =  df_pandas_data['date'].to_numpy()
    i1 = X_first
    i2 = X_last
    X = XD[i1:i2 + 1] # определение данных из прогнозного интервала
    Y = YD[i1:i2 + 1] # определение данных из прогнозного интервала
    DP = D[i1:i2 + 1] # закрепление данных из прогнозного интервала (будет использоваться как первая точка для линейного графика)

    # цикл по дням, используемым для прогнозирования
    # для каждого дня берётся выборка даныхх за закреплённое количество предыдущих значений X, Y
    # например, если прогноз на первый день строится на 20 предыдущих данных,
    # то и на второй день строится на 20 предыдущих данных
    # но при этом для второго дня последнее используемое для прогноза заняения 
    # это прогноз сделанный на первом шаге
    for d in range(0, days_predict):    

         # для каждого определения коэффициентов динейной регрессии
         # используется заданный интервад предыдущих данных,
         # в том числе если это не определение первого прогнозного значения,
         # то используются определённые на предыдущих шагах прогнозные значения
        a, b = mnk(X[ d : ], Y[ d: ]) 
        # print(a, b)
        a1, b1 = mnk_np(X[ d : ], Y[ d: ])
        # print(a1, b1)

        # построение прогноза
        y_predict =  a * (X_last + 1 + d) + b
        date_predict = date_first_predict + timedelta(days=d)

        X = np.append(X, X_last + d)
        Y = np.append(Y, y_predict)
        DP = np.append(DP, date_predict)

    # Y определены как скользящие средние, но для удлбной читаемости графика
    # лучше непрогнозное (а это первое значение) приравнять реальным данным
    # Y[-2 - d] = RD[i2]
    # df_predict_data = pd.DataFrame({"date" : DP[-2 - d : ], selected_data_col : Y[-2 - d : ]})


    df_predict_data = pd.DataFrame({'date' : DP[-1 - d : ], selected_data_col : Y[-1 - d : ]})
    df_real_data = pd.DataFrame({'date' : D, selected_data_col : RD, 'Данные' : DD})
    df_predict_data['Данные'] = "Прогнозируемые линейной регрессией"
    # df_real_data['Данные'] = "Настоящие"

    return pd.concat([df_real_data, df_predict_data], ignore_index=True)



def line_graph(df_plot: pd.DataFrame, selected_city_name: str, selected_data: str)->px.line:

    fig = px.line(
        data_frame = df_plot,
        x = "date",
        y = selected_data,
        color = "Данные",
        color_discrete_sequence=["blue", "red", "green"],
        labels=dict_en_ru,
        title= f'Прогнозные и фактические значения показателя {dict_en_ru[selected_data]} от даты для {selected_city_name}',
        markers=True,
        # width=1200, 
        height=800
    )

    return fig 





# входящая функция кода модуля
def df_graph(df: pd.DataFrame):
    # Добавил условие для расчёта последней фактической (historical) даты
    # Это условие добавил в Dag
    mask = (df['Данные'] == "Прошлые данные с сайта open-meteo.com")
    last_index = mask[mask][::-1].idxmax()  # Получаем индекс последнего True в инвертированной маске
    df_date_max = df.loc[last_index, 'date']  # Получаем псоледнюю фактическую/настоящую/historical дату
    
    
    # ввод данных, используемых для прогноза
    with st.expander(label="Настройка данных для прогнозирования", expanded=True):
        selected_city_ru = st.selectbox(
                    "Выберите город",
                    dict_en_ru_city.values(),
                    key="city"             
                )
        selected_data_ru = st.selectbox(
                    "Выберите параметр",
                    ["Температура", "Количество осадков", "Ветер", "Индекс комфорта (чем выше — тем комфортнее)"],
                    key="parameter"
                    )
        days_data = st.number_input(
                        label="Выберите какое количество дней будет использовано для построения прогноза", 
                        min_value=7, 
                        max_value=( df_date_max - df.date.min() ).days // 2, #( df.date.max() - df.date.min() ).days // 2,
                        step=1,
                        value=20,
                        format="%0d",
                        key="predict_1"        
                        )

        date_first_predict =  st.date_input(
                    "Выбор даты, на которую нужно сделать прогноз",              
                    value = df_date_max,
                    # value =df.date.min() + \
                        # timedelta(
                        # days=( df_date_max - df.date.min() ).days // 2 #( df.date.max() - df.date.min() ).days // 2                      
                        # ),

                    max_value=df_date_max, #df.date.max(),
                    min_value=df.date.min() + timedelta(days=rolling_mean_days + days_data),
                    key="predict_2"
                )  
        

        days_predict = st.number_input(
                        label="Выберите на какое количество дней нужен прогноз", 
                        value=( df.date.max() - date_first_predict ).days + 1,
                        min_value=1, 
                        max_value=( df.date.max() - date_first_predict ).days + 1, #( df.date.max() - date_first_predict ).days + 1,
                        step=1,
                        key="predict_3"                 
                    )     

    df['date'] = pd.to_datetime(df['date']).dt.date           


    if selected_city_ru and selected_data_ru:
        # для перевода выбранных названий в столбцы df
        selected_city = list(filter(lambda key: dict_en_ru_city[key] == selected_city_ru, dict_en_ru_city))[0]          
        selected_data = list(filter(lambda key: dict_en_ru[key] == selected_data_ru, dict_en_ru))[0]
        # для читаемых данных ввода и данных на графиках
        selected_city_name = dict_ru_ru[selected_city_ru]  
    
    # определение данных для построения линейного графика
    # с настоящими и прогнозными значениями
    # график будет построен тольно по последнюю дату прогноза
    df_plot = predict_data(
        df,
        selected_city = selected_city, 
        selected_data_col  = selected_data,
        date_first_predict = datetime.combine(date_first_predict, time.min),
        days_data = days_data,
        days_predict = days_predict,      
        )

    
    fig = line_graph(df_plot, selected_city_name, selected_data)
    st.plotly_chart(fig)