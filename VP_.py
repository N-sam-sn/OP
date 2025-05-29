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
    df = pd.read_csv(BytesIO(response.content), encoding="utf-8-sig", sep=";")
    df.columns = df.columns.str.replace('\ufeff', '').str.strip()

    def clean_number(x):
        if pd.isna(x):
            return None
        return str(x).replace(" ", "").replace(",", ".").replace("–", "0").strip()

    for col in ["ОП", "ОП План", "ВП", "ВП План"]:
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

# === ЗАГРУЗКА ДАННЫХ ===
df = load_data()

# === СТИЛИ ДЛЯ ШИРИНЫ И ВЫСОТЫ ===
st.markdown("""
    <style>
        .main, .block-container {
            max-width: 2000px !important;
            padding-left: 2rem;
            padding-right: 2rem;
        }
        .dataframe th, .dataframe td {
            white-space: nowrap;
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

# === ЗАГОЛОВОК ===
st.title("📊 Дашборд по продажам")

# === ФИЛЬТРАЦИЯ ===
st.sidebar.header("🔎 Фильтрация")

def multiselect_with_all(label, options):
    all_label = "Все"
    selected = st.sidebar.multiselect(label, [all_label] + options, default=all_label)
    return options if all_label in selected else selected

filtered_df = df.copy()

if "Регион" in filtered_df.columns:
    regions = sorted(filtered_df["Регион"].dropna().unique())
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

# === ФОРМИРУЕМ ТАБЛИЦУ ===
display_columns = ["Менеджер", "Покупатель", "Код", "ОП", "ОП План", "% ОП", "ВП", "ВП План", "% ВП"]
df_result = filtered_df[display_columns].copy()

# === ДОБАВЛЕНИЕ ИТОГОВ ===
totals = {
    "Менеджер": "ИТОГО",
    "Покупатель": "",
    "Код": "",
    "ОП": df_result["ОП"].sum(),
    "ОП План": df_result["ОП План"].sum(),
    "% ОП": df_result["ОП"].sum() / df_result["ОП План"].sum() if df_result["ОП План"].sum() != 0 else None,
    "ВП": df_result["ВП"].sum(),
    "ВП План": df_result["ВП План"].sum(),
    "% ВП": df_result["ВП"].sum() / df_result["ВП План"].sum() if df_result["ВП План"].sum() != 0 else None,
}
df_result = pd.concat([df_result, pd.DataFrame([totals])], ignore_index=True)

# === ПОДСВЕТКА ===
def highlight_percent(val):
    if pd.isna(val):
        return ""
    return "background-color: lightgreen" if val > 1 else "background-color: lightcoral" if val < 1 else ""

# === HTML-ТАБЛИЦА ДЛЯ РАСШИРЕННОЙ ВЫСОТЫ ===
styled_html = df_result.style \
    .format({
        "ОП": "{:,.2f}",
        "ОП План": "{:,.2f}",
        "% ОП": "{:.0%}",
        "ВП": "{:,.2f}",
        "ВП План": "{:,.2f}",
        "% ВП": "{:.0%}"
    }) \
    .applymap(highlight_percent, subset=["% ОП", "% ВП"]) \
    .to_html()

st.subheader("📋 Результаты")
st.markdown(f"""
    <div style="min-height: 90vh; overflow-x: auto;">
        {styled_html}
    </div>
""", unsafe_allow_html=True)
