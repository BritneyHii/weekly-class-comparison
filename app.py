import streamlit as st
import pandas as pd

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

# Class type mapping
type_map = {
    1: "长期班",
    2: "短期班",
    3: "活动类",
    4: "诊断类",
    5: "其他"
}

COUNT_COL = "count(distinct class_id)"

if uploaded_file:
    try:
        # Read sheets
        df_current = pd.read_excel(uploaded_file, sheet_name="Sheet1")
        df_last = pd.read_excel(uploaded_file, sheet_name="Sheet2")

        # Clean columns
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

        # Diff (Current - Last)
        merged["diff"] = (
            merged[f"{COUNT_COL}_current"]
            - merged[f"{COUNT_COL}_last"]
        )

        merged["class_type_name"] = merged["class_type"].map(type_map)

        # Totals
        total_current = df_current[COUNT_COL].sum()
        total_last = df_last[COUNT_COL].sum()
        total_diff = total_current - total_last

        # Self-check
        st.subheader("🔍 Data Check")
        st.write({
            "Sum of diff": int(merged["diff"].sum()),
            "Total diff (current - last)": int(total_diff)
        })

        # Summary
        st.subheader("🤖 Auto Summary")

        if total_diff > 0:
            st.success(f"Overall, **{int(total_diff)} more classes** than last week.")
        elif total_diff < 0:
            st.warning(f"Overall, **{int(-total_diff)} fewer classes** than last week.")
        else:
            st.info("Overall class count is **unchanged** from last week.")

        # Top increases
        inc = merged[merged["diff"] > 0].sort_values("diff", ascending=False).head(3)
        if not inc.empty:
            st.markdown("**📈 Top Increases**")
            for _, row in inc.iterrows():
                st.markdown(
                    f"- School `{row['school_code']}` | "
                    f"**{row['class_type_name']}**: +{int(row['diff'])}"
                )

        # Top decreases
        dec = merged[merged["diff"] < 0].sort_values("diff").head(3)
        if not dec.empty:
            st.markdown("**📉 Top Decreases**")
            for _, row in dec.iterrows():
                st.markdown(
                    f"- School `{row['school_code']}` | "
                    f"**{row['class_type_name']}**: {int(row['diff'])}"
                )

        # Table
        st.subheader("📋 Detailed Comparison")
        st.dataframe(
            merged.sort_values("diff", ascending=False)[
                [
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
