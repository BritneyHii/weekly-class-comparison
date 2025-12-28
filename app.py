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

data_mode = st.radio(
    "Choose data source",
    ["Upload Excel", "Paste Data"],
    horizontal=True
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
    st.markdown("### 📋 Paste Current Week Data (CSV)")
    current_text = st.text_area(
        "Current Week",
        height=160,
        placeholder="school_code,class_type,count(distinct class_id)\n415,1,120"
    )

    st.markdown("### 📋 Paste Last Week Data (CSV)")
    last_text = st.text_area(
        "Last Week",
        height=160,
        placeholder="school_code,class_type,count(distinct class_id)\n415,1,110"
    )

    if current_text and last_text:
        df_current = pd.read_csv(StringIO(current_text))
        df_last = pd.read_csv(StringIO(last_text))

# ======================
# Main Logic
# ======================
if df_current is not None and df_last is not None:
    try:
        # ----------------------
        # Clean columns
        # ----------------------
        df_current.columns = df_current.columns.str.strip()
        df_last.columns = df_last.columns.str.strip()

        # ----------------------
        # Merge
        # ----------------------
        merged = df_last.merge(
            df_current,
            on=["school_code", "class_type"],
            how="outer",
            suffixes=("_last", "_current")
        )

        # ----------------------
        # Fill NA
        # ----------------------
        merged[f"{COUNT_COL}_last"] = merged[f"{COUNT_COL}_last"].fillna(0)
        merged[f"{COUNT_COL}_current"] = merged[f"{COUNT_COL}_current"].fillna(0)

        # ----------------------
        # Diff
        # ----------------------
        merged["diff"] = (
            merged[f"{COUNT_COL}_current"]
            - merged[f"{COUNT_COL}_last"]
        )

        # ----------------------
        # Name mapping
        # ----------------------
        merged["class_type_name"] = merged["class_type"].map(type_map)
        merged["school_name"] = merged["school_code"].map(school_map).fillna(
            merged["school_code"].astype(str)
        )

        # ======================
        # Sidebar Filters
        # ======================
        st.sidebar.header("🔎 Filters")

        school_options = ["All"] + sorted(merged["school_name"].unique().tolist())
        class_options = ["All"] + sorted(merged["class_type_name"].unique().tolist())

        selected_school = st.sidebar.selectbox("School", school_options)
        selected_class = st.sidebar.selectbox("Class Type", class_options)

        filtered = merged.copy()

        if selected_school != "All":
            filtered = filtered[filtered["school_name"] == selected_school]

        if selected_class != "All":
            filtered = filtered[filtered["class_type_name"] == selected_class]

        # ======================
        # Totals
        # ======================
        total_current = filtered[f"{COUNT_COL}_current"].sum()
        total_last = filtered[f"{COUNT_COL}_last"].sum()
        total_diff = total_current - total_last

        # ======================
        # Weekly Totals
        # ======================
        st.subheader("📊 Weekly Totals | 周汇总")

        col1, col2, col3 = st.columns(3)

        col1.metric("Current Week | 本周", int(total_current))
        col2.metric("Last Week | 上周", int(total_last))
        col3.metric(
            "Difference | 变化",
            int(total_diff),
            delta=int(total_diff)
        )

        # ======================
        # Bilingual Summary
        # ======================
        st.subheader("🤖 Auto Summary | 自动总结")

        if total_diff > 0:
            st.success(
                f"**EN:** Total classes increased by **{int(total_diff)}** "
                f"(from {int(total_last)} to {int(total_current)})."
            )
            st.success(
                f"**CN:** 课堂总数相比上一周 **增加了 {int(total_diff)} 节**，"
                f"由 {int(total_last)} 节增长至 {int(total_current)} 节。"
            )
        elif total_diff < 0:
            st.warning(
                f"**EN:** Total classes decreased by **{int(-total_diff)}** "
                f"(from {int(total_last)} to {int(total_current)})."
            )
            st.warning(
                f"**CN:** 课堂总数相比上一周 **减少了 {int(-total_diff)} 节**，"
                f"由 {int(total_last)} 节降至 {int(total_current)} 节。"
            )
        else:
            st.info("**EN:** Total class count remains unchanged.")
            st.info("**CN:** 课堂总数与上一周保持一致。")

        # ======================
        # Top Changes
        # ======================
        inc = filtered[filtered["diff"] > 0].sort_values("diff", ascending=False).head(3)
        dec = filtered[filtered["diff"] < 0].sort_values("diff").head(3)

        if not inc.empty:
            st.markdown("### 📈 Top Increases | 主要增幅来源")
            for _, row in inc.iterrows():
                st.markdown(
                    f"- **{row['school_name']}** ｜ {row['class_type_name']} ： +{int(row['diff'])}"
                )

        if not dec.empty:
            st.markdown("### 📉 Top Decreases | 主要下降来源")
            for _, row in dec.iterrows():
                st.markdown(
                    f"- **{row['school_name']}** ｜ {row['class_type_name']} ： {int(row['diff'])}"
                )

        # ======================
        # Table
        # ======================
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
        st.error("❌ Failed to process data. Please check format.")
        st.exception(e)

else:
    st.info("👆 Please upload an Excel file or paste data to start analysis.")
