import streamlit as st
import pandas as pd
from io import StringIO

# ======================
# Page Config
# ======================
st.set_page_config(
    page_title="Weekly Class Comparison Tool",
    layout="wide"
)

st.title("📊 Weekly Class Comparison Tool")
st.caption("Compare current week vs last week by school & class type")

# ======================
# Mapping
# ======================
type_map = {
    1: "长期班",
    2: "短期班",
    3: "活动类",
    4: "诊断类",
    5: "其他"
}

school_map = {
    415: "US",
    4401: "UK",
    6501: "SG",
    103: "CA",
    6101: "AUS",
    6001: "MYS",
    85201: "HK",
    8201: "韩国",
    8101: "日本",
    3301: "法国",
    8601: "火星",
    6502: "国际竞赛"
}

COUNT_COL = "count(distinct class_id)"

# ======================
# Data Input Mode
# ======================
st.subheader("📥 Data Input Method | 数据输入方式")

data_mode = st.selectbox(
    "Choose data source",
    ["Upload Excel", "Paste Data"]
)

df_current = None
df_last = None

# ======================
# Upload Excel
# ======================
if data_mode == "Upload Excel":
    uploaded_file = st.file_uploader(
        "Upload Excel file (Sheet1 = Current Week, Sheet2 = Last Week)",
        type=["xlsx"]
    )

    if uploaded_file:
        df_current = pd.read_excel(uploaded_file, sheet_name="Sheet1")
        df_last = pd.read_excel(uploaded_file, sheet_name="Sheet2")

# ======================
# Paste Data 
# ======================
else:
    st.markdown("📋 Paste Current Week Data | 粘贴【本周】班级数量数据")
    current_text = st.text_area(
    label="Current Week Data",
    height=180,
    key="current_week_input"
    )

    st.markdown("📋 Paste Last Week Data | 粘贴【上周】班级数量数据")
    last_text = st.text_area(
    label="Last Week Data",
    height=180,
    key="last_week_input"
    )


    if current_text.strip() and last_text.strip():
        df_current = pd.read_csv(
            StringIO(current_text),
            sep=None,
            engine="python"
        )

        df_last = pd.read_csv(
            StringIO(last_text),
            sep=None,
            engine="python"
        )

# ======================
# Main Logic
# ======================
if df_current is not None and df_last is not None:
    try:
        # Clean column names
        df_current.columns = df_current.columns.str.strip()
        df_last.columns = df_last.columns.str.strip()

        # Drop date column if exists
        for df in (df_current, df_last):
            if "date" in df.columns:
                df.drop(columns=["date"], inplace=True)

        # Merge
        merged = df_last.merge(
            df_current,
            on=["school_code", "class_type"],
            how="outer",
            suffixes=("_last", "_current")
        )

        # Fill NA
        merged[f"{COUNT_COL}_last"] = merged[f"{COUNT_COL}_last"].fillna(0)
        merged[f"{COUNT_COL}_current"] = merged[f"{COUNT_COL}_current"].fillna(0)

        # Diff
        merged["diff"] = (
            merged[f"{COUNT_COL}_current"]
            - merged[f"{COUNT_COL}_last"]
        )

        # Mapping
        merged["class_type_name"] = merged["class_type"].map(type_map)
        merged["school_name"] = merged["school_code"].map(school_map).fillna(
            merged["school_code"].astype(str)
        )

        # Sidebar filters
        st.sidebar.header("🔎 Filters")

        school_options = ["All"] + sorted(merged["school_name"].unique())
        class_options = ["All"] + sorted(merged["class_type_name"].unique())

        selected_school = st.sidebar.selectbox("School", school_options)
        selected_class = st.sidebar.selectbox("Class Type", class_options)

        filtered = merged.copy()

        if selected_school != "All":
            filtered = filtered[filtered["school_name"] == selected_school]

        if selected_class != "All":
            filtered = filtered[filtered["class_type_name"] == selected_class]

        # Totals
        total_current = filtered[f"{COUNT_COL}_current"].sum()
        total_last = filtered[f"{COUNT_COL}_last"].sum()
        total_diff = total_current - total_last

        # Metrics
        st.subheader("📊 Weekly Totals | 周汇总")
        c1, c2, c3 = st.columns(3)
        c1.metric("Current Week | 本周", int(total_current))
        c2.metric("Last Week | 上周", int(total_last))
        c3.metric("Difference | 变化", int(total_diff), delta=int(total_diff))

        # Summary
        st.subheader("🤖 Auto Summary | 自动总结")
        if total_diff > 0:
            st.success(f"EN: Total classes increased by {int(total_diff)}.")
            st.success(f"CN: 课堂总数增加 {int(total_diff)} 节。")
        elif total_diff < 0:
            st.warning(f"EN: Total classes decreased by {int(-total_diff)}.")
            st.warning(f"CN: 课堂总数减少 {int(-total_diff)} 节。")
        else:
            st.info("EN: No change.")
            st.info("CN: 与上周持平。")

        # Table
        st.subheader("📋 Detailed Comparison | 明细对比")
        st.dataframe(
            filtered.sort_values("diff", ascending=False)[
                [
                    "school_name",
                    "school_code",
                    "class_type_name",
                    f"{COUNT_COL}_last",
                    f"{COUNT_COL}_current",
                    "diff",
                ]
            ],
            use_container_width=True
        )

    except Exception as e:
        st.error("❌ Failed to process data.")
        st.exception(e)

else:
    st.info("👆 Please upload Excel or paste data to start.")




