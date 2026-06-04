# app.py

import streamlit as st
import sqlite3
import polars as pl
import pandas as pd
import numpy as np
import show_data
import show_statistic
import predict
import metrics


DB_PATH = "airflow_sf/project/data/weather.db"

st.set_page_config(page_title="WeatherInsight", layout="wide", page_icon="🌦️")
st.subheader("🌦️ WeatherInsight: Погодные тренды")

# Загрузка данных
@st.cache_data
def load_data(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    df = pl.read_database("SELECT * FROM weather ORDER BY date", conn)
    conn.close()
    return df

# функция с помощью интерполяции проставляет пропущенные значения
# для переданного в функцию города, при этом интерполяция зависит от даты
def df_interpol(df_pandas, city):
    """Интерполяция пропущенных значений для указанного города (работает с pandas)"""
    mask_city = df_pandas['city'] == city
    df_city = df_pandas[mask_city].copy()
    df_city = df_city.sort_values('date')
    
    # Сохраняем строковые колонки отдельно
    str_columns = df_city.select_dtypes(include=['object']).columns.tolist()
    
    # Устанавливаем дату как индекс
    df_city = df_city.set_index('date')
    
    # Выбираем только числовые колонки для интерполяции
    numeric_columns = df_city.select_dtypes(include=[np.number]).columns.tolist()
    
    # Интерполяция только числовых колонок
    df_city[numeric_columns] = df_city[numeric_columns].interpolate(method='time', limit_direction='both')
    
    df_city = df_city.reset_index()
    return df_city

# функция для обработки пропущенных значений
def df_fill_na(df):
    # преобразуем polars в pandas для удобной работы с пропусками
    df_pandas = df.to_pandas()

    # удаляем строки без города и/или даты (без них данные не идентифицировать)
    df_pandas = df_pandas.dropna(subset=['city', 'date'])
    
    # закрепляем формат даты
    df_pandas['date'] = pd.to_datetime(df_pandas['date'])
    
    # определяем все уникальные города
    city_unique = df_pandas["city"].unique()
    
    # для каждого города проставляем пропущенные значения
    df_frames = []
    for city in city_unique:
        df_city_interpolated = df_interpol(df_pandas, city)
        df_frames.append(df_city_interpolated)
    
    df_pandas_new = pd.concat(df_frames, ignore_index=True)

    # удаляем дубликаты (одна дата — одна запись на город)
    df_pandas_new['date'] = df_pandas_new['date'].dt.date
    df_pandas_new = df_pandas_new.drop_duplicates(subset=['city', 'date'], keep="first")
    
    # интерполированные значения могут быть нецелыми, а дождь либо был, либо нет
    if 'is_rainy' in df_pandas_new.columns:
        df_pandas_new['is_rainy'] = df_pandas_new['is_rainy'].round().astype(int)

    # удаляем строки, где всё ещё остались пропуски
    df_pandas_new = df_pandas_new.dropna(how="any")

    # возвращаем обратно в polars
    return pl.DataFrame(df_pandas_new)

# добавление новых столбцов, создание категориальных признаков
def df_add_cat_cols(df: pl.DataFrame) -> pd.DataFrame:
    df = df.with_columns(
        pl.when(pl.col('avg_temp') <= 10)
        .then(pl.lit("холодно"))
        .when((pl.col('avg_temp') > 10) & (pl.col('avg_temp') <= 20))
        .then(pl.lit("умеренно"))
        .otherwise(pl.lit("жарко"))
        .alias("cat_temp")
    )

    df = df.with_columns(
        pl.when(pl.col('total_precip') <= 0.5)
        .then(pl.lit("без осадков"))
        .when((pl.col('total_precip') > 0.5) & (pl.col('total_precip') <= 6))
        .then(pl.lit("небольшие"))
        .otherwise(pl.lit("сильные"))
        .alias("cat_precip")
    )
    
    df = df.with_columns(
        pl.when(
            ((pl.col('avg_temp') <= 15) & (pl.col('avg_wind') >= 10)) |
            ((pl.col('avg_temp') <= 5) & (pl.col('avg_wind') >= 5)) |
            ((pl.col('avg_temp') <= 20) & (pl.col('avg_wind') >= 15)) |
            (pl.col('avg_wind') >= 20) |
            (pl.col('avg_temp') < 0)
        )
        .then(pl.lit("не комфортно"))
        .when(
            ((pl.col('avg_temp') <= 15) & (pl.col('avg_wind') >= 5)) |
            ((pl.col('avg_temp') <= 20) & (pl.col('avg_wind') >= 10)) |
            (pl.col('avg_wind') >= 15) |
            (pl.col('avg_temp') < 5)
        )
        .then(pl.lit("умеренно"))
        .otherwise(pl.lit("комфортно"))
        .alias("cat_comfrort")
    )

    # преобразуем в pandas для совместимости с другими функциями
    df_pandas = df.to_pandas()
    df_pandas['date'] = pd.to_datetime(df_pandas['date']).dt.date
    
    return df_pandas

def load_and_change_df(DB_PATH: str) -> pd.DataFrame:
    try:
        df = load_data(DB_PATH)
    except Exception as e:
        st.error("❌ Не удалось загрузить данные. Убедитесь, что база данных существует и доступна.")
        st.stop()
        return pd.DataFrame()  # возвращаем пустой DataFrame при ошибке
    
    # обработка пропущенных значений
    df = df_fill_na(df)
    # добавление новых столбцов
    df_pandas = df_add_cat_cols(df)
    
    return df_pandas

def main():
    # загрузка и первичная обработка (работа с пропущенными значениями, создание новых признаков)
    df_pandas = load_and_change_df(DB_PATH)
    
    if not df_pandas.empty:
        # эксперимент для лучшего отображения страницы (чтобы CSS применился сразу)
        if "first_start" not in st.session_state:
            st.session_state["first_start"] = True
            st.rerun()
            
        tab_show_data, tab_metrics_df, statistic_df, predict_df = st.tabs(
            ["**Работа с таблицей**",
             "**Метрики погоды**",
             "**Статистические данные**",
             "**Прогноз**"]
        )
        
        with tab_show_data:
            try:
                show_data.show_dataframe(df_pandas)
            except Exception as e:
                st.warning(f"Измените параметры для отображения таблицы: {e}")
                
        with tab_metrics_df:
            metrics.metrics_df(df_pandas)
            
        with statistic_df:
            show_statistic.graph_df(df_pandas)
            
        with predict_df:
            predict.df_graph(df_pandas)
        
        # отображение надписей st.tabs с немного увеличенным шрифтом
        css = '''
            <style>
                .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
                    font-size: 1.1rem;
                }
            </style>
        '''
        st.markdown(css, unsafe_allow_html=True)

try:
    main()
except Exception as e:
    st.error(f"Ошибка при выполнении кода. {type(e).__name__}, строка {e.__traceback__.tb_lineno}, файл {__file__}:\n{e}")