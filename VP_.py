import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# === ССЫЛКА НА CSV ===
FILE_URL = "https://raw.githubusercontent.com/N-sam-sn/OP/main/Result.csv"

@st.cache_data
def load_data():
    response = requests.get(FILE_URL)
    response.raise_for_status()

    try:
        df = pd.read_csv(BytesIO(response.content), encoding="utf-8-sig", sep=";")
    except Exception as e:
        st.error(f"Ошибка при чтении CSV: {e}")
        st.stop()

    df.columns = df.columns.str.replace('\ufeff', '').str.strip()

    def clean_number(x):
        if pd.isna(x):
            return None
        return str(x).replace(" ", "").replace(",", ".").replace("–", "0").strip()

    numeric_cols = ["ОП", "ОП План", "ВП", "ВП План"]
    for col in numeric_cols:
        df[col] = df[col].apply(clean_number)
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df[
        (df["ОП"] > 0) |
        (df["ОП План"] > 0) |
        (df["ВП"] > 0) |
        (df["ВП План"] > 0)
    ].copy()

    df["% ОП"] = df.apply(lambda row: row["ОП"] / row["ОП План"] if row["ОП План"] != 0 else None, axis=1)
    df["% ВП"] = df.apply(lambda row: row["ВП"] / row["ВП План"] if row["ВП План"] != 0 else None, axis=1)

    return df

df = load_data()

# === Заголовок ===
st.title("📊 Дашборд по продажам")

# === Фильтрация ===
st.sidebar.header("🔎 Фильтрация")

def multiselect_with_all(label, options):
    all_label = "Все"
    selected = st.sidebar.multiselect(label, [all_label] + options, default=all_label)
    return options if all_label in selected else selected

filtered_df = df.copy()

# Фильтр по Региону
if "Регион" in filtered_df.columns:
    regions = sorted(filtered_df["Регион"].dropna().unique())
    region_selection = multiselect_with_all("Регион", regions)
    filtered_df = filtered_df[filtered_df["Регион"].isin(region_selection)]

# Фильтр по Менеджеру
if "Менеджер" in filtered_df.columns:
    managers = sorted(filtered_df["Менеджер"].dropna().unique())
    manager_selection = multiselect_with_all("Менеджер", managers)
    filtered_df = filtered_df[filtered_df["Менеджер"].isin(manager_selection)]

# Фильтр по полю "Добавить в план"
if "Добавить в план" in filtered_df.columns:
    plans = sorted(filtered_df["Добавить в план"].dropna().unique())
    plan_selection = multiselect_with_all("Добавить в план", plans)
    filtered_df = filtered_df[filtered_df["Добавить в план"].isin(plan_selection)]

# Фильтр по Покупателю
if "Покупатель" in filtered_df.columns:
    buyers = sorted(filtered_df["Покупатель"].dropna().unique())
    buyer_selection = multiselect_with_all("Покупатель", buyers)
    filtered_df = filtered_df[filtered_df["Покупатель"].isin(buyer_selection)]

# === Отображение таблицы ===
st.subheader("📋 Результаты")

display_columns = ["Менеджер", "Покупатель", "Код", "ОП", "ОП План", "% ОП", "ВП", "ВП План", "% ВП"]
available_cols = [col for col in display_columns if col in filtered_df.columns]

def highlight_percent(val):
    if pd.isna(val):
        return ""
    return "background-color: lightgreen" if val > 1 else "background-color: lightcoral" if val < 1 else ""

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

st.dataframe(styled_df, use_container_width=True)
