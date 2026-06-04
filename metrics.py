import streamlit as st
import pandas as pd
from default_data import dict_en_ru, dict_en_ru_city, dict_ru_ru

# Функция для выбора города и для простановки метрик для выбранного города
def metrics_df(df_pandas:pd.DataFrame):

    with st.container(border=True):
        selected_city_ru = st.selectbox(
            "Выберите город",
            dict_en_ru_city.values(),
            key="city_mertric"             
        )


        min_date = df_pandas.date.min()
        max_date = df_pandas.date.max()
        dates = st.date_input(
            "Выберите с какой по какую дату нужно отобразить метрики",
            format="DD.MM.YYYY",
            value=[min_date, max_date], 
            min_value=min_date,  
             max_value=max_date
            )

        if selected_city_ru and len(dates) > 1:
            # для перевода выбранного названия города в значение столбца city df
            selected_city = list(filter(lambda key: dict_en_ru_city[key] == selected_city_ru, dict_en_ru_city))[0]
            date_min = dates[0]    
            date_max = dates[1]
            mask_city = df_pandas.city == selected_city
            mask_date = df_pandas['date'].between(date_min, date_max)
            city_data = df_pandas[mask_city & mask_date].reset_index(drop=True)

            st.subheader(f"Показатели за период с {date_min:%d.%m.%Y} по {date_max:%d.%m.%Y}")
                       
            rainy_days = city_data.is_rainy.sum()
            avg_temp = city_data.avg_temp.mean()
            avg_wind = city_data.avg_wind.mean()
            avg_wind = city_data.total_precip.mean()
            avg_comfort = city_data.comfort_index.mean()

            c_temp, c_wind, c_percip, c_rain, c_comf = st.columns(5)
            c_temp.metric("Средняя температура", f"{avg_temp:.1f}°C")
            c_wind.metric("Средний ветер", f"{avg_wind:.1f}м/с")
            c_percip.metric("Среднее количество осадков", f"{int(avg_wind)}мм")
            c_rain.metric("Дождливых дней", int(rainy_days))
            c_comf.metric("Средний комфорт", f"{avg_comfort:.1f}")