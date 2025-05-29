import streamlit as st
import pandas as pd
import requests
from io import BytesIO

FILE_URL = "https://raw.githubusercontent.com/N-sam-sn/OP/main/Result.csv"

@st.cache_data
def load_data():
    response = requests.get(FILE_URL)
    response.raise_for_status()
    df = pd.read_csv(BytesIO(response.content), encoding="utf-8-sig", sep=None, engine="python")
    df.columns = df.columns.str.replace('\ufeff', '').str.strip()

    required_cols = ["ОП", "ОП План", "ВП", "ВП План"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        st.error(f"Отсутствуют необходимые колонки: {', '.join(missing)}")
        st.stop()

    for col in required_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["% ОП"] = df["ОП"] / df["ОП План"].replace(0, pd.NA)
    df["% ВП"] = df["ВП"] / df["ВП План"].replace(0, pd.NA)

    return df

df = load_data()
st.title("📊 Дашборд по продажам")

st.sidebar.header("🔎 Фильтрация")

def multiselect_with_all(label, options):
    all_label = "Все"
    selected = st.sidebar.multiselect(label, [all_label] + options, default=all_label)
    return options if all_label in selected else selected

filtered_df = df.copy()

if "Регион" in df.columns:
    regions = sorted(df["Регион"].dropna().unique())
    region_selection = multiselect_with_all("Регион", regions)
    filtered_df = filtered_df[filtered_df["Регион"].isin(region_selection)]

if "Менеджер" in filtered_df.columns:
    managers = sorted(filtered_df["Менеджер"].dropna().unique())
    manager_selection = multiselect_with_all("Менеджер", managers)
    filtered_df = filtered_df[filtered_df["Менеджер"].isin(manager_selection)]

if "Добавить в план" in filtered_df.columns:
    plans = sorted(filtered_df["Добавить в план"].dropna().unique())
    plan_selection = multiselect_with_all("Добавить в план", plans)
    filtered_df = filtered_df[filtered_df["Добавить в план"].isin(plan_selection)]

if "Покупатель" in filtered_df.columns:
    buyers = sorted(filtered_df["Покупатель"].dropna().unique())
    buyer_selection = multiselect_with_all("Покупатель", buyers)
    filtered_df = filtered_df[filtered_df["Покупатель"].isin(buyer_selection)]

st.subheader("📋 Результаты")

# Столбцы для отображения
display_cols = ["Менеджер", "Покупатель", "Код", "ОП", "ОП План", "% ОП", "ВП", "ВП План", "% ВП"]
available_cols = [col for col in display_cols if col in filtered_df.columns]

# Функция подсветки
def highlight_percent(val):
    if pd.isna(val):
        return ""
    return "background-color: lightgreen" if val > 1 else "background-color: lightcoral" if val < 1 else ""

# Стилизация
styled_df = filtered_df[available_cols].style \
    .format({
        "ОП": "{:,.2f}",
        "ОП План": "{:,.2f}",
        "% ОП": "{:.0%}",
        "ВП": "{:,.2f}",
        "ВП План": "{:,.2f}",
        "% ВП": "{:.0%}"
    }) \
    .applymap(highlight_percent, subset=[col for col in ["% ОП", "% ВП"] if col in filtered_df.columns])

# Отображение таблицы без горизонтального скролла
st.dataframe(styled_df, use_container_width=True, height=min(700, 40 + 35 * len(filtered_df)))
