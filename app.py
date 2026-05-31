# app.py

import streamlit as st
import sqlite3
import polars as pl
import pandas as pd
import show_data
import show_statistic
import predict


DB_PATH = "data/weather.db"

st.set_page_config(page_title="WeatherInsight", layout="wide", page_icon="🌦️")
st.subheader("🌦️ WeatherInsight: Погодные тренды")

# Загрузка данных
@st.cache_data
def load_data(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    df = pl.read_database("SELECT * FROM weather ORDER BY date", conn)
    conn.close()
    return df

# ИСПРАВЛЕННАЯ функция интерполяции
def df_interpol(df, city):
    mask_city = df['city'] == city  # отбираем только данные города
    df_new = df[mask_city].sort_values(by='date')  # сортируем данные для города
    df_new = df_new.set_index('date')  # закрепляем даты как индекс
    
    # ВАЖНО: Выбираем только числовые колонки для интерполяции
    numeric_cols = df_new.select_dtypes(include=['float64', 'int64']).columns
    
    # Применяем интерполяцию только к числовым колонкам
    if len(numeric_cols) > 0:
        df_new[numeric_cols] = df_new[numeric_cols].interpolate(method='time', limit_direction='both')
    
    df_new.reset_index(level=0, inplace=True)
    df_new['city'] = city  # восстанавливаем колонку города
    return df_new

# функция для обработки пропущенных значений
def df_fill_na(df):
    # pandas поудобней для удаления пропущенных значений 
    # (в Polars, как правило, надо удалять null, NaN)
    df_pandas = df.to_pandas()

    # если нет названия города и/или даты прогноза, 
    # то сложно идентифицировать принадлежность данных    
    df_pandas = df_pandas.dropna(subset=['city','date']) 
      
    # закрепляем формат дата
    df_pandas['date'] = pd.to_datetime(df_pandas['date'])
    
    # Принудительно преобразуем числовые колонки
    numeric_cols = ['avg_temp', 'min_temp', 'max_temp', 'total_precip', 'avg_wind', 'is_rainy']
    for col in numeric_cols:
        if col in df_pandas.columns:
            df_pandas[col] = pd.to_numeric(df_pandas[col], errors='coerce')
  
    # определяем все уникальные города
    city_unique = df_pandas["city"].unique()
    
    # для каждого города проставляем пропущенные значения
    # и создаём новый df
    df_pandas_new = pd.concat((
        df_interpol(df_pandas, c) for c in city_unique
    ))

    # не может быть двух записей о погоде в одном городе и в одну дату
    df_pandas_new['date'] = df_pandas_new['date'].dt.date
    df_pandas_new = df_pandas_new.drop_duplicates(subset=['city','date'], keep="first")
    
    # интерполируемые значения могут быть нецелыми,
    # а дождь или был или нет
    if 'is_rainy' in df_pandas_new.columns:
        df_pandas_new['is_rainy'] = df_pandas_new['is_rainy'].round().astype(int)

    # если вдруг ещё остались строки с пропущенным значением, то удаляем всю строку
    df_pandas_new = df_pandas_new.dropna(how="any")

    # всё назад в polars
    return pl.DataFrame(df_pandas_new)

# добавление новых столбцов
# создание категориальных признаков
def df_add_cat_cols(df: pl.DataFrame) -> pd.DataFrame:

    df = df.with_columns(
        pl.when( pl.col('avg_temp') <= 10 )
        .then( pl.lit("холодно") )
        .when( (pl.col('avg_temp') > 10) & (pl.col('avg_temp') <= 20) )
        .then( pl.lit("умеренно") )
        .otherwise( pl.lit("жарко") )
        .alias("cat_temp")
    )

    df = df.with_columns(
        pl.when( pl.col('total_precip') <= 0.5 )
        .then( pl.lit("без осадков") )
        .when( (pl.col('total_precip') > 0.5) & (pl.col('total_precip') <= 6) )
        .then( pl.lit("небольшие") )
        .otherwise( pl.lit("сильные") )
        .alias("cat_precip")
    )
    
    df = df.with_columns(
        pl.when( ( (pl.col('avg_temp') <= 15) & (pl.col('avg_wind') >= 10) )
                 |
                 ( (pl.col('avg_temp') <= 5) &  (pl.col('avg_wind') >= 5) )
                 |
                 ( (pl.col('avg_temp') <= 20) &  (pl.col('avg_wind') >= 15) )
                 |
                 ( (pl.col('avg_wind') >= 20) )
                |
                 ( (pl.col('avg_temp') < 0) )
            )
        .then( pl.lit("не комфортно") )
        .when( ( (pl.col('avg_temp') <= 15) & (pl.col('avg_wind') >= 5) )
                |
                 ( (pl.col('avg_temp') <= 20) & (pl.col('avg_wind') >= 10) )
                |
                 (pl.col('avg_wind') >= 15)
                |
                 (pl.col('avg_temp') < 5)
            )
        .then( pl.lit("умеренно") )
        .otherwise( pl.lit("комфортно") )
        .alias("cat_comfrort")
    )

    # по условиям задачи приводим к pandas
    df_pandas = df.to_pandas()

    # для уверенности закрепляем формат дата
    df_pandas['date'] = pd.to_datetime(df_pandas['date']).dt.date
    
    return df_pandas

def load_and_change_df(DB_PATH: str) -> pd.DataFrame:
    try:
        df = load_data(DB_PATH)
    except Exception as e:
        st.error("❌ Не удалось загрузить данные. Убедитесь, что база данных существует и доступна.")
        st.stop()
        return
    # ОБРАБОТКА ПРОПУЩЕННЫХ ЗНАЧЕНИЙ
    df = df_fill_na(df)
    # добавление новых столбцов
    df_pandas = df_add_cat_cols(df)    

    return df_pandas

def main():
    # загрузка и первичная обработка (работа с пропущенными значениями, простановка новых признаков)
    df_pandas = load_and_change_df(DB_PATH)    
    if not df_pandas.empty:
        # эксперимент, ради лучшего отображения страницы сразу с html css (иначе запаздывало)
        if not "first_start" in st.session_state:
            st.session_state["first_start"] = True
            st.rerun()
            
        tab_show_data, statistic_df, predict_df = st.tabs(
            ["**Работа с таблицей**", 
             "**Статистические данные**",
             "**Прогноз**"]
        )
        with tab_show_data:
            try:
                show_data.show_dataframe(df_pandas)
            except:
                st.warning("Измените параметры для отображения таблицы")
        with statistic_df:
            show_statistic.graph_df(df_pandas)
        with predict_df:
            predict.df_graph(df_pandas)

        # Отображение надписей st.tabs с немного увеличенным шрифтом 
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
    st.error(f"Ошибка при выполнении кода. {type(e).__name__} строка {e.__traceback__.tb_lineno} файл {__file__}:\n{e}")