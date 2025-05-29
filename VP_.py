import pandas as pd
import ipywidgets as widgets
from IPython.display import display, HTML, clear_output

# === Загрузка и подготовка данных ===
file_path = r"D:\Work\Python\Dash_express\OP\Result.csv"
df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig', decimal=',')

# Приведение чисел
for col in ["ОП", "ОП План", "ВП", "ВП План"]:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# Расчёт дополнительных столбцов
df["% ОП"] = df["ОП"] / df["ОП План"].replace(0, pd.NA)
df["% ВП"] = df["ВП"] / df["ВП План"].replace(0, pd.NA)

# === Фильтры ===
def dropdown(column_name):
    return widgets.Dropdown(
        options=["Все"] + sorted(df[column_name].dropna().unique().tolist()),
        value="Все",
        description=column_name + ":",
        layout=widgets.Layout(width="300px")
    )

region_filter = dropdown("Регион")
plan_filter = dropdown("Добавить в план")
manager_filter = dropdown("Менеджер")
buyer_filter = dropdown("Покупатель")

# === Подсветка ===
def highlight_cells(val):
    if pd.isna(val):
        return ''
    if val > 1:
        return 'background-color: lightgreen'
    elif val < 1:
        return 'background-color: lightcoral'
    return ''

# === Основная функция отображения ===
def update_dashboard(change=None):
    clear_output(wait=True)
    
    # Фильтрация
    dff = df.copy()
    if region_filter.value != "Все":
        dff = dff[dff["Регион"] == region_filter.value]
    if plan_filter.value != "Все":
        dff = dff[dff["Добавить в план"] == plan_filter.value]
    if manager_filter.value != "Все":
        dff = dff[dff["Менеджер"] == manager_filter.value]
    if buyer_filter.value != "Все":
        dff = dff[dff["Покупатель"] == buyer_filter.value]

    # Вывод фильтров
    display(HTML("<h2>📊 Интерактивный дашборд по продажам</h2>"))
    display(widgets.HBox([region_filter, plan_filter, manager_filter, buyer_filter]))

    # Отображаем таблицу
    display_cols = ["Менеджер", "Покупатель", "Код", "ОП", "ОП План", "% ОП", "ВП", "ВП План", "% ВП"]
    styled_df = dff[display_cols].style \
        .format({
            "ОП": "{:,.2f}",
            "ОП План": "{:,.2f}",
            "% ОП": "{:.0%}",
            "ВП": "{:,.2f}",
            "ВП План": "{:,.2f}",
            "% ВП": "{:.0%}"
        }) \
        .applymap(highlight_cells, subset=["% ОП", "% ВП"])
    
    display(HTML("<br><h4>📋 Таблица результатов</h4>"))
    display(styled_df)

# === Привязка изменений ===
region_filter.observe(update_dashboard, names='value')
plan_filter.observe(update_dashboard, names='value')
manager_filter.observe(update_dashboard, names='value')
buyer_filter.observe(update_dashboard, names='value')

# === Инициализация дашборда ===
update_dashboard()
