import streamlit as st
import pandas as pd

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
# Upload Excel
# ======================
uploaded_file = st.file_uploader(
    "Upload Excel file (Sheet1 = Current Week, Sheet2 = Last Week)",
    type=["xlsx"]
)

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
# Main Logic
# ======================
if uploaded_file:
    try:
        # Read data
        df_current = pd.read_excel(uploaded_file, sheet_name="Sheet1")
        df_last = pd.read_excel(uploaded_file, sheet_name="Sheet2")

        df_current.columns = df_current.columns.str.strip()
        df_last.columns = df_last.columns.str.strip()

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

        # Name mapping
        merged["class_type_name"] = merged["class_type"].map(type_map)
        merged["school_name"] = merged["school_code"].map(school_map).fillna(
            merged["school_code"].astype(str)
        )

        # ======================
        # Sidebar Filters 🆕
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
        # Totals (based on filter)
        # ======================
        total_diff = filtered["diff"].sum()

        # Self check
        st.subheader("🔍 Data Check")
        st.write({
            "Filtered diff sum": int(total_diff),
            "Row count": len(filtered)
        })

        # ======================
        # Bilingual Summary 🆕
        # ======================
        st.subheader("🤖 Auto Summary | 自动总结")

        # English
        if total_diff > 0:
            st.success(f"**EN:** Overall, **{int(total_diff)} more classes** than last week.")
            st.success(f"**CN:** 整体相比上一周 **增加了 {int(total_diff)} 节课**。")
        elif total_diff < 0:
            st.warning(f"**EN:** Overall, **{int(-total_diff)} fewer classes** than last week.")
            st.warning(f"**CN:** 整体相比上一周 **减少了 {int(-total_diff)} 节课**。")
        else:
            st.info("**EN:** Overall class count is unchanged.")
            st.info("**CN:** 整体课堂数量与上一周持平。")

        # ======================
        # Top Changes
        # ======================
        inc = filtered[filtered["diff"] > 0].sort_values("diff", ascending=False).head(3)
        dec = filtered[filtered["diff"] < 0].sort_values("diff").head(3)

        if not inc.empty:
            st.markdown("### 📈 Top Increases | 主要增幅来源")
            for _, row in inc.iterrows():
                st.markdown(
                    f"- **{row['school_name']}** ｜ {row['class_type_name']} ： "
                    f"+{int(row['diff'])}"
                )

        if not dec.empty:
            st.markdown("### 📉 Top Decreases | 主要下降来源")
            for _, row in dec.iterrows():
                st.markdown(
                    f"- **{row['school_name']}** ｜ {row['class_type_name']} ： "
                    f"{int(row['diff'])}"
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
        st.error("❌ Failed to process file. Please check format.")
        st.exception(e)

else:
    st.info("👆 Please upload an Excel file to start analysis.")
