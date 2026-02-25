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

    def clean(x):
        if pd.isna(x) or str(x).strip() == "":
            return "-"
        return str(x).strip()


    for col in ["ОП", "ОП План", "ВП", "ВП План", "ОП_ПГ"]:
        if col in df.columns:
            df[col] = df[col].apply(clean_number)
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["Менеджер", "Покупатель","Регион","Добавить в план","Отдел","Канал","ИНН"]:
        if col in df.columns:
            df[col] = df[col].apply(clean)

            

    df = df[        
        (df["ОП План"] != 0) |
        (df["ОП"] != 0) |
        (df["ВП"] != 0) |        
         (df["ВП План"] != 0)
    ].copy()

    df["% ОП"] = df.apply(lambda row: row["ОП"] / row["ОП План"] if row["ОП План"] else None, axis=1)
    df["% ВП"] = df.apply(lambda row: row["ВП"] / row["ВП План"] if row["ВП План"] else None, axis=1)

    return df

# === CSS ===
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
        .scrollable-table-container {
            max-height: 80vh;
            overflow-y: auto;
            overflow-x: auto;
            border: 1px solid #ddd;
        }
        .scrollable-table-container table thead th {
            position: sticky;
            top: 0;
            background-color: #f1f1f1;
            z-index: 1;
        }
    </style>
""", unsafe_allow_html=True)

# === ЗАГОЛОВОК ===
st.title("Дашборд по продажам февраля 2026")

# === ЗАГРУЗКА ДАННЫХ ===
df = load_data()

# === ФИЛЬТРЫ ===
st.sidebar.header("Фильтрация")

def multiselect_with_all(label, options):
    all_label = "Все"
    selected = st.sidebar.multiselect(label, [all_label] + options, default=all_label)
    return options if all_label in selected else selected

filtered_df = df.copy()


if "Отдел" in filtered_df.columns:
    departments = sorted(filtered_df["Отдел"].dropna().unique())
    department_selection = multiselect_with_all("Отдел", departments)
    filtered_df = filtered_df[filtered_df["Отдел"].isin(department_selection)]

if "Канал" in filtered_df.columns:
    channels = sorted(filtered_df["Канал"].dropna().unique())
    channel_selection = multiselect_with_all("Канал", channels)
    filtered_df = filtered_df[filtered_df["Канал"].isin(channel_selection)]
    
if "Регион" in filtered_df.columns:
    regions = sorted(filtered_df["Регион"].dropna().unique())
    region_selection = multiselect_with_all("Регион", regions)
    filtered_df = filtered_df[filtered_df["Регион"].isin(region_selection)]

if "Добавить в план" in filtered_df.columns:
    plans = sorted(filtered_df["Добавить в план"].dropna().unique())
    plan_selection = multiselect_with_all("Добавить в план", plans)
    filtered_df = filtered_df[filtered_df["Добавить в план"].isin(plan_selection)]

if "Менеджер" in filtered_df.columns:
    managers = sorted(filtered_df["Менеджер"].dropna().unique())
    manager_selection = multiselect_with_all("Менеджер", managers)
    filtered_df = filtered_df[filtered_df["Менеджер"].isin(manager_selection)]

if "Покупатель" in filtered_df.columns:
    buyers = sorted(filtered_df["Покупатель"].dropna().unique())
    buyer_selection = multiselect_with_all("Покупатель", buyers)
    filtered_df = filtered_df[filtered_df["Покупатель"].isin(buyer_selection)]



# === ПОДСВЕТКА ПРОЦЕНТОВ ===
def highlight_percent_cols(df):
    styles = pd.DataFrame("", index=df.index, columns=df.columns)
    for col in ["% ОП", "% ВП"]:
        if col in df.columns:
            styles[col] = df[col].apply(
                lambda v: "background-color: lightgreen" if pd.notna(v) and v > 1
                else "background-color: lightcoral" if pd.notna(v) and v < 1
                else ""
            )
    return styles

# === ФОРМАТИРУЮЩИЕ ФУНКЦИИ ===
def safe_percent(x):
    return "{:.0%}".format(x) if pd.notna(x) else ""

def safe_number(x):
    return "{:,.0f}".format(x) if pd.notna(x) else ""

# === ТАБЛИЦА ===
if not filtered_df.empty:
    display_columns = ["Менеджер","Код", "Покупатель","ОП", "ОП План", "% ОП", "ВП", "ВП План", "% ВП", "ОП_ПГ"]#"Менеджер", "Покупатель"] # , ,"Добавить в план","Регион","Отдел","Канал"
    df_result = filtered_df[display_columns].copy()
    df_result.rename(columns={"ОП": "ОП Факт", "ВП": "ВП Факт"}, inplace=True)

    # Подсчёт итогов
    total_op = df_result["ОП Факт"].sum()
    total_op_plan = df_result["ОП План"].sum()
    total_vp = df_result["ВП Факт"].sum()
    total_vp_plan = df_result["ВП План"].sum()
    total_pg = df_result["ОП_ПГ"].sum()

    percent_op_total = total_op / total_op_plan if total_op_plan else None
    percent_vp_total = total_vp / total_vp_plan if total_vp_plan else None

    totals = {
        "Менеджер": "ИТОГО",
        "Покупатель": "",
        "Код": "",
        "ОП Факт": total_op,
        "ОП План": total_op_plan,
        "% ОП": percent_op_total,
        "ВП Факт": total_vp,
        "ВП План": total_vp_plan,
        "% ВП": percent_vp_total,
        "ОП_ПГ": total_pg
    }

    df_result = pd.concat([df_result, pd.DataFrame([totals])], ignore_index=True)

    # === ЗАГОЛОВОК С ИТОГАМИ В СТРОКУ + ЗАЛИВКА ===
    color_op = "lightgreen" if percent_op_total is not None and percent_op_total >= 1 else "lightcoral"
    color_vp = "lightgreen" if percent_vp_total is not None and percent_vp_total >= 1 else "lightcoral"

    summary_html = f"""
        <div style="font-weight:bold; margin-top:1em;">
            Итоги: &nbsp;
            ОП Факт:{safe_number(total_op)} &nbsp; | &nbsp;
            ОП План: {safe_number(total_op_plan)} &nbsp; | &nbsp;
            <span style="background-color:{color_op}; padding: 2px 6px; border-radius: 4px;">
                % ОП: {safe_percent(percent_op_total)}
            </span> &nbsp; | &nbsp;
            ВП Факт: {safe_number(total_vp)} &nbsp; | &nbsp;
            ВП План: {safe_number(total_vp_plan)} &nbsp; | &nbsp;
            <span style="background-color:{color_vp}; padding: 2px 6px; border-radius: 4px;">
                % ВП: {safe_percent(percent_vp_total)}
            </span> &nbsp; | &nbsp;
            ОП_ПГ: {safe_number(total_pg)}
        </div>
    """

    st.subheader("Результаты на 24.02.2026")
    st.markdown(summary_html, unsafe_allow_html=True)

    styled_html = df_result.style \
        .format({
            "ОП Факт": safe_number,
            "ОП План": safe_number,
            "% ОП": safe_percent,
            "ВП Факт": safe_number,
            "ВП План": safe_number,
            "% ВП": safe_percent,
            "ОП_ПГ": safe_number
        }) \
        .apply(highlight_percent_cols, axis=None) \
        .to_html()

    st.markdown(f"""
        <div class="scrollable-table-container">
            {styled_html}
        </div>
    """, unsafe_allow_html=True)

else:
    st.warning("⚠️ Нет данных для отображения — проверьте настройки фильтрации.")






























































































