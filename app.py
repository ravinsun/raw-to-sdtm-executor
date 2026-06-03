import streamlit as st
import pandas as pd
import os
from src.mapper import map_all_domains
from src.validator import validate_all

st.set_page_config(page_title="Raw-to-SDTM Executor", page_icon="🧬", layout="wide")
st.title("🧬 Raw-to-SDTM Mapping Executor")
st.caption("Simulates SDTM domain mapping and Pinnacle 21-style validation")

os.makedirs("output", exist_ok=True)

if st.button("▶ Run Full Pipeline", type="primary"):
    with st.spinner("Mapping all domains..."):
        results = map_all_domains()

    with st.spinner("Validating..."):
        report = validate_all(results)

    st.success(f"Pipeline complete — {sum(len(df) for df in results.values())} total records mapped")

    # Save outputs
    for domain, df in results.items():
        df.to_csv(f"output/sdtm_{domain.lower()}.csv", index=False)
    report.to_csv("output/validation_report.csv", index=False)

    # Show mapped datasets
    st.subheader("📋 Mapped SDTM Datasets")
    tabs = st.tabs(list(results.keys()))
    for tab, (domain, df) in zip(tabs, results.items()):
        with tab:
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False)
            st.download_button(f"Download {domain}.csv", csv,
                f"sdtm_{domain.lower()}.csv", "text/csv")

    # Validation report
    st.subheader("⚠️ Validation Report (Pinnacle 21-style)")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Issues", len(report))
    col2.metric("Domains with Issues",
        len(report[report["check_id"] != ""]["domain"].unique()) if len(report) > 0 else 0)
    col3.metric("Records Mapped",
        sum(len(df) for df in results.values()))

    if len(report) > 0:
        # Color coding by check type
        check_colors = {
            "MISSING_REQUIRED": "🔴",
            "INVALID_CT":       "🟠",
            "WRONG_DTYPE":      "🟡",
            "DATE_FORMAT":      "🟡",
        }
        report["type"] = report["check_id"].map(check_colors).fillna("⚪")
        st.dataframe(report[["type","check_id","domain","variable","row","severity","message"]],
            use_container_width=True)
        csv = report.to_csv(index=False)
        st.download_button("Download Validation Report", csv,
            "validation_report.csv", "text/csv")
    else:
        st.success("No validation issues found!")

    st.info("Output files saved to output/ folder")

else:
    st.info("Click **Run Full Pipeline** to map raw EDC data to SDTM and validate.")
    st.markdown("""
    **Pipeline steps:**
    1. Load Excel mapping spec (28 variable mappings across DM, LB, AE, VS)
    2. Apply derivation rules (direct map, date formatting, USUBJID concatenation)
    3. Run Pinnacle 21-style validation checks (missing required, invalid CT, wrong dtype, date format)
    4. Output SDTM CSVs + validation report
    """)
