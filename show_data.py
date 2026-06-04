import pandas as pd
import streamlit as st

# функция в кэше для постраничного отображения таблицы

# функция принимает на вход страницу просмотра
# и количество строк на странице
# функция возвращает срез df, определённый страницей просмотра
#  и количеством строк на странице
@st.cache_resource
def get_page_data(dataset: pd.DataFrame, page_number: int, page_size: int)->pd.DataFrame:
    start = (page_number - 1) * page_size
    end = page_number * page_size
    return dataset[start:end]


# функция для простановки фильтров в таблицу df
def filter_dataframe(df_pandas: pd.DataFrame) -> pd.DataFrame:

    df = df_pandas.copy()
    
    # список столбцов типа дата
    cols_date = ['date']

    # список бинарных столбцов
    cols_binary = ['is_rainy']
        
    # список категориальных столбцов
    cols_cat =  ['city', 'cat_temp', 'cat_precip', 'cat_comfrort', 'Данные']

     # список числовых столбцов
    cols_numeric = ['avg_temp', 'total_precip',	'avg_wind', 'comfort_index']
  
    # создаётся контейнер (ограниченая зона окна) под фильтры
    filter_cont = st.container()

    with filter_cont:
        to_filter_columns = st.multiselect(
            "Выберите столбцы, по которым нужно проставить фильтр (чтобы убрать фильтр, просто уберите столбец)", 
            df.columns, 
            placeholder = "Столбцы"
            )
        for column in to_filter_columns:
            left, right = st.columns((0.05, 95)) #  доля ширины для колонок
            left.write("↳")
            # признак категориальный
            if column in cols_cat:
                user_cat_input = right.multiselect(
                    f"Выбор данных для {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                if len(user_cat_input) < 1:
                    return
                df = df[df[column].isin(user_cat_input)] # фильтр
            
            # фильтр для числовых столбцов
            elif column in cols_numeric:
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                if _min < _max:
                    user_num_input = right.slider(
                        f"Выбор данных для {column}",
                        min_value=_min,
                        max_value=_max,
                        value=(_min, _max),
                        step=step,
                    )
                    df = df[df[column].between(*user_num_input)]
                else:
                    st.warning("Измените парметры для отображения таблицы")
                
            # фильтр для столбцов с датами
            elif column in cols_date:
                user_date_input = right.date_input(
                    f"Выбор данных для {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    start_date, end_date = user_date_input
                    df = df.loc[ df[column].between(start_date, end_date) ]

            # фильтр по бинарному признаку
            elif column in cols_binary:
                user_date_input = right.checkbox(f"Установить признак для {column}")
                df = df[df[column]==int(user_date_input)]

    return df


# функция для отображения таблицы df
def show_dataframe(df: pd.DataFrame) -> pd.DataFrame:

    # раскрытие для выбора фильтров
    with st.expander(label="Простановка фильтров", expanded=True):
        # вызов филтра и схранение отфильтрованной таблицы
        df_filtered = filter_dataframe(df)

    with st.expander(label="Настройка просмотра страниц", expanded=True):
        page_size = st.number_input('Число строк на странице', 1, 1000, value=90, step=30, key="pagination_1")
        max_value=len(df)//page_size + 1
        # разделение df на страницы для более быстрого отображения
        page_number = st.number_input('Номер страницы просмотра', 1, max_value, key="pagination_2")
    st.write(f'Число страниц: {max_value}')

    # таблица для отображения (с учётом разделения на страницы)
    df_filtered_pagination = get_page_data(df_filtered, page_number, page_size)

    with st.container(border=True, key="tab_1"):
        st.write(f"Для сортировки по столбцу нажмите на его заголовок")
        st.dataframe(df_filtered_pagination.reset_index(drop=True))

