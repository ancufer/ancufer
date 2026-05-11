import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from math import ceil


# st.set_page_config(layout="wide")

# словарь для задания периода
dict_loan_term = {
    "1 месяц" : 1,
    "3 месяца" : 3,
    "6 месяцев" : 6,
    "9 месяцев" : 9,
    "1 год" : 1 * 12,
    "1.5 года" : 18,
    "2 года" : 2 * 12,
    "3 года" : 3 * 12,
    "4 года" : 4 * 12,
    "5 лет" : 5 * 12,
    "6 лет" : 6 * 12,
    "7 лет" : 7 * 12,
    "8 лет" : 8 * 12,
    "9 лет" : 9 * 12,
    "10 лет" : 10 * 12,
    "15 лет" : 15 * 12,
    "20 лет" : 20 * 12,
    "25 лет" : 25 * 12,
    "30 лет" : 30 * 12,
    } 


# В расчёте всех графиков предполагаются ежемесячные платежи по Кредиту

# Функция создания DataFrame с графиком погашений Кредита
# Принимает 
# list_dates- список с датами 
# list_debts - список с сумммами оставшегося долга
# list_part_debts - список с суммами гашения основного долга
# list_interests - список с суммами гашения начисленных процентов по кредиту
# list_payment - итоговый платеж по гредиту (гашения основного долга и процентов)
def df_table(
    list_dates:list[datetime.date], 
    list_debts:list[float], 
    list_part_debts:list[float], 
    list_interests:list[float], 
    list_payment:list[float]
    )->pd.DataFrame:
    
    df = pd.DataFrame(
                    {
                        'Дата' : list_dates, 
                        'Остаток основного долга после платежа' : list_debts,
                        'Погашение основного долга'  : list_part_debts, 
                        'Погашение процентов' : list_interests,
                        'Итоговый платёж' : list_payment,                        
                    }
                )

    return df


# функция для построения списка дат платежей
# first_date - дата, когда взят Кредит, предполагается ежемесяное гашений в эту дату
# N - период, на который взят Кредит в месяцах
def dates_list(first_date:datetime.date, N:int)->list[datetime.date]:
    # dt = datetime(2025, 9, 1).date()
    year = first_date.year
    month = first_date.month
    day = first_date.day

    # список дат выплат
    list_dates = [ datetime(year + int(m/12), (month - 1 + m)%12 + 1, day ).date() for m in range(0, N + 1)]

    return list_dates


# функция для Аннуитетного Кредита
# S - сумма Кредита (основного долга)
# P - месячная процентная ставка
# N - период, на который взят Кредит в месяцах
def annuitet_kredit(
    S:int,
    P:float,
    N:int
    )->tuple[list[float], list[float], list[float], list[float]]:

    # расчёт Аннуитеного платежа
    x = S * (  P + ( P/((1 + P)**N - 1) )  )
    x = ceil(x) # проценты, тоже надо учитывать
    
    list_debts = [S] # список непопогашенного долга, первый элемент равен выданному долгу

    # Первый элемент Ноль, так как впервую дату нет выплат
    list_part_debts =  [0] # список части гашения долга в аннуитетном платеже
    list_interests = [0] # список части гашения начисленных процентов в аннуитетном платеже
    Snext = S # для расчёта уменьшения суммы основного долга

    for m in range(1, N + 1):
        i = ceil( Snext * P) # расчёт оплаты процентов
        Snext -= x - i # расчёт уменьшения оставшейся суммы основного долга
        list_debts.append(round(Snext)) # добавление в список оставшейся суммы основного долга
        list_interests.append(i) # добавление в список гашения процентов
        list_part_debts.append(round(x - i, 0)) # добавление в список гашения основного долга


    # Корректировка последней выплаты по соновному долгу,
    # Так, чтобы итоговая выплата всех сумм равнялась выданной сумме долга
    list_part_debts[-1] += S - sum(list_part_debts)
    list_debts[-1] = list_debts[-2] - list_part_debts[-1]
    # Так как сумма аннуитета постоянаая, то корректируем последнюю выплату процентов
    list_interests[-1] = x - list_part_debts[-1] 

    # список с суммой Итогового платежа (аннуитет)
    list_payment = [x] * (N + 1)   

    return list_debts, list_part_debts, list_interests, list_payment


# функция для Дифференцированного Кредита
# S - сумма Кредита (основного долга)
# P - месячная процентная ставка
# N - период, на который взят Кредит в месяца
def diff_kredit(
    S:int,
    P:float,
    N:int
    )->tuple[list[float], list[float], list[float], list[float]]:

    # расчёт гашения основного долга
    b = round(S / N, 0)
    
    list_part_debts = [0] # список части гашения долга в аннуитетном платеже
    list_part_debts[1:] = [b] * N
    
    # Корректировка последней выплаты по соновному долгу,
    # Так, чтобы итоговая выплата всех сумм равнялась выданной сумме долга
    # (связано с округлением, которое нужно для упрощения)
    list_part_debts[-1] += S - sum(list_part_debts)

    list_debts = [ S - sum(list_part_debts[:m + 1]) for m in range(0, N + 1)] # список непопогашенного долга

    list_interests = [0]
    list_interests[1:] = [ ceil(list_debts[m] * P) for m in range(0, N)] # список гашения процентов

    list_payment = [ x + y for x, y in zip(list_part_debts, list_interests) ] # список с суммой Итогового платежа

    return list_debts, list_part_debts, list_interests, list_payment





 # функции для удобного отображения через разделители
def number_with_sep(debt:int)->str:
    # для привычного отображения с разделением разрядов через пробел
    return '{0:_d}'.format(int(debt)).replace("_", " ") 


# функция ввода данных
def input_data():

    # для аккуратности все перечисленные элементы в контейнер
    with st.container(border=True):
        # есть возможность изменения вида ввода данных
        with st.expander("Настройка ввода данных"):
            chbx_debt = st.checkbox("Ввод через слайдеры: Кредит", key="debt")
            chbx_inp = st.checkbox("Ввод через слайдеры: Ставка", key="input")
            chbx_term = st.checkbox("Ввод через слайдеры: Период", key="term")

        # для удобства каждый воод данных можно сворачивать
        with st.expander("Ввод Кредит", expanded=True):
            if not chbx_debt:            
                debt = st.number_input(
                        label="Выберите сумму кредита (от 100 000 до 20 000 000)", 
                        min_value=100_000, 
                        max_value=20_000_000,
                        step = 10_000,
                        value = 1_000_000           
                    )

            else:            
                debt = st.slider(
                        label="Выберите сумму кредита (от 100 000 до 20 000 000, шаг 10 000)", 
                        min_value=100_000, 
                        max_value=20_000_000,
                        step = 10_000,
                        value = 1_000_000       
                        )
                
        # удобное отображение введённых данных (вызов функции для удобного отображения через разделители)
        # видно даже при свёрнутом поле ввода        
        st.text(f"Кредит {number_with_sep(debt)} ₽")                     

        with st.expander("Ввод Ставка", expanded=True):
            if not chbx_inp:    
                interest_rate = st.number_input(
                    label="Введите годовую процентную ставку в процентах (от 0.01% до 100%)", 
                    min_value=0.01, 
                    max_value=100.00,
                    step = 0.005,
                    value = 15.5,
                    format = "%0.3f"            
                    )
 
            else:
                interest_rate = st.slider(
                    label="Выберите годовую процентную ставку в процентах (от 0.01% до 100%, шаг 0.005%)", 
                    min_value=0.01, 
                    max_value=100.00,
                    step = 0.0005,
                    value = 15.5,
                    format = "%0.3f"            
                    )

        # удобное отображение введённых данных
        # видно даже при свёрнутом поле ввода          
        st.text("Ставка {0:.3f} %".format(interest_rate))

        # выделяем индекс для задания периода "по-умолчанию"
        ind = len(dict_loan_term.keys())//3
        with st.expander("Ввод Период", expanded=True):
            if not chbx_term:
                term = st.selectbox(
                    label="Выберите срок кредита",
                    options=dict_loan_term.keys(),
                    index=ind
                    )

            else:
                term = st.select_slider(
                    label="Выберите срок кредита",
                    options=dict_loan_term.keys(),
                    value=list(dict_loan_term.keys())[ind] # задание периода "по-умолчанию"
                    )
                
        # видно даже при свёрнутом поле ввода    
        st.text(f"Период {term}")
                
        # для удобства каждый воод данных можно сворачивать
        with st.expander("Ввод даты выдачи кредита", expanded=True):
                today = date.today()
                min_date = date(today.year - 10, 12, 31)
                max_date = date(today.year + 10, 12, 31)
                first_date = st.date_input(
                "Выберите даты своего отпуска",
                format="DD.MM.YYYY",
                value=today, 
                min_value=min_date,  
                max_value=max_date
                )

        st.write(f"Дата выдачи кредита {first_date.strftime('%d.%m.%Y')}")

        return debt, interest_rate/12/100, dict_loan_term[term], first_date

def main():

    st.header("Кредитный калькулятор")
    
    S, P, N, first_date = input_data()

    list_dates = dates_list(first_date, N)
    tab_annuit, tab_diff = st.tabs(["Аннуитетный график", "Дифференцированный график"], width=1000)
    with tab_annuit:
        list_debts, list_part_debts, list_interests, list_payment = annuitet_kredit(S, P, N)
        st.write(f"Сумма выплат по основному долгу **{ number_with_sep( sum(list_part_debts) ) }**")
        st.write(f"Сумма выплат процентов по кредиту **{ number_with_sep( sum(list_interests) ) }**")
        st.write(f"Аннуитетный платёж **{ number_with_sep( list_payment[1] ) }**")
        df = df_table(list_dates, list_debts, list_part_debts, list_interests, list_payment)
        st.dataframe(df)

    with tab_diff:
        list_debts, list_part_debts, list_interests, list_payment = diff_kredit(S, P, N)
        st.write(f"Сумма выплат по основному долгу **{ number_with_sep( sum(list_part_debts) ) }**")
        st.write(f"Сумма выплат процентов по кредиту **{ number_with_sep( sum(list_interests) ) }**")
        st.write(f"Платёж по основному долгу **{ number_with_sep( list_part_debts[1] ) }**")
        df = df_table(list_dates, list_debts, list_part_debts, list_interests, list_payment)
        st.dataframe(df)
        


try:
    main()
except Exception as e:
    st.error(f"Ошибка при выполнении кода. {type(e).__name__} строка {e.__traceback__.tb_lineno} файл {__file__}:\n{e}")