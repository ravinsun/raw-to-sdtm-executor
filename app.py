import streamlit as st
import pandas as pd
import os
from src.predict_domain import load_model, predict_domain, get_review_tier
from src.mapper import map_domain
from src.validator import validate_domain

st.set_page_config(page_title="SDTM Pipeline", page_icon="🧬", layout="wide")
st.title("🧬 SDTM Automation Pipeline")
st.caption("Stage 1: Domain Classification → Stage 2: Mapping & Validation")

os.makedirs("output", exist_ok=True)

TIER_COLOR = {
    "AUTO-ACCEPT":  "🟢",
    "HUMAN-REVIEW": "🟡",
    "ESCALATE":     "🔴",
}

TIER_INFO = {
    "AUTO-ACCEPT":  "Confidence >= 0.85",
    "HUMAN-REVIEW": "Confidence 0.65-0.84",
    "ESCALATE":     "Confidence < 0.65",
}

DOMAINS = ["DM", "LB", "AE", "VS", "CM", "EX", "MH", "DS", "EG", "PE", "FA", "SU"]

@st.cache_resource
def get_model():
    return load_model("models/sdtm_classifier.pkl")

model = get_model()

# Shared state
if "classified_df" not in st.session_state:
    st.session_state.classified_df = None
if "confirmed" not in st.session_state:
    st.session_state.confirmed = False

tab1, tab2 = st.tabs(["Stage 1 — Domain Classification", "Stage 2 — Mapping & Validation"])

# ── TAB 1 ──────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Upload Variable List")
    st.write("Upload a CSV with columns: `variable_name`, `label`")

    uploaded = st.file_uploader("Choose CSV", type="csv", key="stage1")

    if uploaded:
        df = pd.read_csv(uploaded)
        if "variable_name" in df.columns and "label" in df.columns:
            results = []
            for _, row in df.iterrows():
                r = predict_domain(row["variable_name"], row["label"], model)
                results.append({
                    "variable_name":    r["variable_name"],
                    "label":            r["label"],
                    "predicted_domain": r["predicted_domain"],
                    "confidence":       r["confidence"],
                    "review_tier":      r["review_tier"],
                    "tier_icon":        TIER_COLOR[r["review_tier"]],
                })
            result_df = pd.DataFrame(results)

            # Summary metrics
            total    = len(result_df)
            auto     = len(result_df[result_df["review_tier"] == "AUTO-ACCEPT"])
            review   = len(result_df[result_df["review_tier"] == "HUMAN-REVIEW"])
            escalate = len(result_df[result_df["review_tier"] == "ESCALATE"])

            st.subheader("Classification Summary")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Variables", total)
            c2.metric("🟢 Auto-Accept",  f"{auto} ({auto/total:.0%})")
            c3.metric("🟡 Human Review", f"{review} ({review/total:.0%})")
            c4.metric("🔴 Escalate",     f"{escalate} ({escalate/total:.0%})")

            st.subheader("Review & Confirm Predictions")
            st.info("Review predictions below. Override any domain using the dropdown, then click Confirm.")

            edited_rows = []
            for _, row in result_df.iterrows():
                col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 2])
                col1.write(f"**{row['variable_name']}**")
                col2.write(row["label"])
                override = col3.selectbox(
                    "Domain",
                    DOMAINS,
                    index=DOMAINS.index(row["predicted_domain"]) if row["predicted_domain"] in DOMAINS else 0,
                    key=f"domain_{row['variable_name']}"
                )
                col4.write(f"{row['confidence']:.1%}")
                col5.write(f"{row['tier_icon']} {row['review_tier']}")
                edited_rows.append({
                    "variable_name":    row["variable_name"],
                    "label":            row["label"],
                    "predicted_domain": row["predicted_domain"],
                    "final_domain":     override,
                    "confidence":       row["confidence"],
                    "review_tier":      row["review_tier"],
                    "overridden":       override != row["predicted_domain"],
                })

            if st.button("✅ Confirm Domain Assignments — Proceed to Stage 2", type="primary"):
                st.session_state.classified_df = pd.DataFrame(edited_rows)
                st.session_state.confirmed = True
                overrides = sum(1 for r in edited_rows if r["overridden"])
                st.success(f"Confirmed {len(edited_rows)} variables — {overrides} overridden. Switch to Stage 2 tab.")
        else:
            st.error("CSV must have columns: variable_name, label")

    if not uploaded:
        st.markdown("""
        **How Stage 1 works:**
        - ML model predicts SDTM domain from variable name + label
        - 95% cross-validated accuracy across 12 CDISC domains
        - Three-tier review: 🟢 Auto-Accept · 🟡 Human Review · 🔴 Escalate
        - Override any prediction before passing to Stage 2
        """)

# ── TAB 2 ──────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("SDTM Mapping & Validation")

    if not st.session_state.confirmed or st.session_state.classified_df is None:
        st.warning("Complete Stage 1 first — upload a variable list and confirm domain assignments.")
    else:
        classified_df = st.session_state.classified_df
        overrides = classified_df[classified_df["overridden"] == True]

        st.success(f"Received {len(classified_df)} variables from Stage 1 — {len(overrides)} overridden by reviewer")

        if st.button("▶ Run Mapping & Validation", type="primary"):
            with st.spinner("Mapping all domains..."):
                results = {}
                for domain in ["dm", "lb", "ae", "vs"]:
                    try:
                        results[domain.upper()] = map_domain(domain)
                    except Exception as e:
                        st.error(f"Mapping failed for {domain.upper()}: {e}")

            with st.spinner("Validating..."):
                from src.validator import validate_all
                report = validate_all(results)

            total_records = sum(len(df) for df in results.values())
            st.success(f"Pipeline complete — {total_records} records mapped across {len(results)} domains")

            # Save outputs
            for domain, df in results.items():
                df.to_csv(f"output/sdtm_{domain.lower()}.csv", index=False)
            report.to_csv("output/validation_report.csv", index=False)

            # Mapped datasets
            st.subheader("📋 Mapped SDTM Datasets")
            tabs = st.tabs(list(results.keys()))
            for tab, (domain, df) in zip(tabs, results.items()):
                with tab:
                    st.dataframe(df, use_container_width=True)
                    st.download_button(
                        f"Download {domain}.csv",
                        df.to_csv(index=False),
                        f"sdtm_{domain.lower()}.csv",
                        "text/csv"
                    )

            # Validation report
            st.subheader("⚠️ Validation Report (Pinnacle 21-style)")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Issues", len(report))
            c2.metric("Domains with Issues",
                len(report["domain"].unique()) if len(report) > 0 else 0)
            c3.metric("Records Mapped", total_records)

            if len(report) > 0:
                check_icons = {
                    "MISSING_REQUIRED": "🔴",
                    "INVALID_CT":       "🟠",
                    "WRONG_DTYPE":      "🟡",
                    "DATE_FORMAT":      "🟡",
                }
                report["icon"] = report["check_id"].map(check_icons).fillna("⚪")
                st.dataframe(
                    report[["icon","check_id","domain","variable","row","severity","message"]],
                    use_container_width=True
                )
                st.download_button(
                    "Download Validation Report",
                    report.to_csv(index=False),
                    "validation_report.csv",
                    "text/csv"
                )
            else:
                st.success("No validation issues found!")

            # Stage 1 → Stage 2 traceability
            st.subheader("🔗 Stage 1 → Stage 2 Traceability")
            st.dataframe(
                classified_df[["variable_name","label","predicted_domain",
                               "final_domain","confidence","review_tier","overridden"]],
                use_container_width=True
            )
            st.download_button(
                "Download Full Traceability Report",
                classified_df.to_csv(index=False),
                "traceability_report.csv",
                "text/csv"
            )
