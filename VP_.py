import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# === Загрузка данных с GitHub ===
FILE_URL = "https://github.com/N-sam-sn/OP/raw/main/Result.xlsx"

@st.cache_data
def load_data():
    response = requests.get(FILE_URL)
    df = pd.read_excel(BytesIO(response.content))
    df.columns = df.columns.str.strip()
    for col in ["ОП", "ОП План", "ВП", "ВП План"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["% ОП"] = df["ОП"] / df["ОП План"].replace(0, pd.NA)
    df["% ВП"] = df["ВП"] / df["ВП План"].replace(0, pd.NA)
    return df

df = load_data()

# === Заголовок ===
st.title("📊 Дашборд по продажам")

# === Фильтры ===
st.sidebar.header("🔎 Фильтрация")

def multiselect_with_all(label, options):
    all_label = "Все"
    selected = st.sidebar.multiselect(label, [all_label] + options, default=all_label)
    if all_label in selected:
        return options
    return selected

regions = sorted(df["Регион"].dropna().unique())
region_selection = multiselect_with_all("Регион", regions)

filtered_df = df[df["Регион"].isin(region_selection)]

managers = sorted(filtered_df["Менеджер"].dropna().unique())
manager_selection = multiselect_with_all("Менеджер", managers)

filtered_df = filtered_df[filtered_df["Менеджер"].isin(manager_selection)]

plans = sorted(filtered_df["Добавить в план"].dropna().unique())
plan_selection = multiselect_with_all("Добавить в план", plans)

filtered_df = filtered_df[filtered_df["Добавить в план"].isin(plan_selection)]

buyers = sorted(filtered_df["Покупатель"].dropna().unique())
buyer_selection = multiselect_with_all("Покупатель", buyers)

filtered_df = filtered_df[filtered_df["Покупатель"].isin(buyer_selection)]

# === Таблица результатов ===
st.subheader("📋 Результаты")
display_cols = ["Менеджер", "Покупатель", "Код", "ОП", "ОП План", "% ОП", "ВП", "ВП План", "% ВП"]

def highlight_percent(val):
    if pd.isna(val):
        return ""
    if val > 1:
        return "background-color: lightgreen"
    elif val < 1:
        return "background-color: lightcoral"
    return ""

styled_df = filtered_df[display_cols].style \
    .format({
        "ОП": "{:,.2f}",
        "ОП План": "{:,.2f}",
        "% ОП": "{:.0%}",
        "ВП": "{:,.2f}",
        "ВП План": "{:,.2f}",
        "% ВП": "{:.0%}"
    }) \
    .applymap(highlight_percent, subset=["% ОП", "% ВП"])

st.dataframe(styled_df, use_container_width=True)
