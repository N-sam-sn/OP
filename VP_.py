import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# === ССЫЛКА НА CSV ===
FILE_URL = "https://raw.githubusercontent.com/N-sam-sn/OP/main/Result.csv"

@st.cache_data
def load_data():
    # Загружаем файл
    response = requests.get(FILE_URL)
    response.raise_for_status()

    try:
        # Читаем CSV с разделителем `;`
        df = pd.read_csv(BytesIO(response.content), encoding="utf-8-sig", sep=";")
    except Exception as e:
        st.error(f"Ошибка при чтении CSV: {e}")
        st.stop()

    # Очистка названий колонок
    df.columns = df.columns.str.replace('\ufeff', '').str.strip()

    # Очистка и конвертация числовых колонок
    def clean_number(x):
        if pd.isna(x):
            return None
        return str(x).replace(" ", "").replace(",", ".").replace("–", "0").strip()

    numeric_cols = ["ОП", "ОП План", "ВП", "ВП План"]
    for col in numeric_cols:
        df[col] = df[col].apply(clean_number)
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Отфильтруем строки с ненулевыми значениями
    df = df[
        (df["ОП"] > 0) |
        (df["ОП План"] > 0) |
        (df["ВП"] > 0) |
        (df["ВП План"] > 0)
    ].copy()

    # Расчет % ОП и % ВП
    df["% ОП"] = df.apply(lambda row: row["ОП"] / row["ОП План"] if row["ОП План"] != 0 else None, axis=1)
    df["% ВП"] = df.apply(lambda row: row["ВП"] / row["ВП План"] if row["ВП План"] != 0 else None, axis=1)

    return df

df = load_data()

# === Заголовок ===
st.title("📊 Дашборд по продажам")

# === Отображение таблицы ===
st.subheader("📋 Результаты")

display_columns = ["Менеджер", "Покупатель", "Код", "ОП", "ОП План", "% ОП", "ВП", "ВП План", "% ВП"]
df_to_display = df[display_columns].copy()

# Форматирование и подсветка
def highlight_percent(val):
    if pd.isna(val):
        return ""
    return "background-color: lightgreen" if val > 1 else "background-color: lightcoral" if val < 1 else ""

styled_df = df_to_display.style \
    .format({
        "ОП": "{:,.2f}",
        "ОП План": "{:,.2f}",
        "% ОП": "{:.0%}",
        "ВП": "{:,.2f}",
        "ВП План": "{:,.2f}",
        "% ВП": "{:.0%}"
    }) \
    .applymap(highlight_percent, subset=["% ОП", "% ВП"])

# Вывод таблицы без горизонтального скролла
st.dataframe(styled_df, use_container_width=True)
