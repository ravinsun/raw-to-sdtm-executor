import streamlit as st
import pandas as pd
import os
from src.predict_domain import load_model, predict_domain, get_review_tier
from src.reuse_checker import load_prior_spec, run_reuse_check
from src.mapper import map_domain
from src.validator import validate_domain

st.set_page_config(page_title="SDTM Pipeline", page_icon="🧬", layout="wide")
st.title("🧬 SDTM Automation Pipeline")
st.caption("Stage 0: Mapping Reuse → Stage 1: ML Classification → Stage 2: Mapping & Validation")

os.makedirs("output", exist_ok=True)

TIER_COLOR = {
    "AUTO-ACCEPT":  "🟢",
    "HUMAN-REVIEW": "🟡",
    "ESCALATE":     "🔴",
}

METHOD_COLOR = {
    "REUSE":    "🔵",
    "ML":       "🟣",
    "NO_MATCH": "⚪",
}

DOMAINS = ["DM","LB","AE","VS","CM","EX","MH","DS","EG","PE","FA","SU"]

@st.cache_resource
def get_model():
    return load_model("models/sdtm_classifier.pkl")

@st.cache_resource
def get_prior_spec():
    return load_prior_spec()

model      = get_model()
prior_spec = get_prior_spec()

if "stage0_df"   not in st.session_state: st.session_state.stage0_df   = None
if "stage1_df"   not in st.session_state: st.session_state.stage1_df   = None
if "confirmed"   not in st.session_state: st.session_state.confirmed   = False

tab0, tab1, tab2 = st.tabs([
    "Stage 0 — Mapping Reuse",
    "Stage 1 — ML Classification",
    "Stage 2 — Mapping & Validation"
])

# ── STAGE 0 ────────────────────────────────────────────────────────────────
with tab0:
    st.subheader("Stage 0 — Mapping Reuse Check")
    st.write("Upload variable list. Known variables reuse prior study mappings at confidence 1.0.")

    col1, col2 = st.columns(2)
    col1.metric("Prior Study Variables", len(prior_spec))
    col2.metric("Source Studies", prior_spec["source_study"].nunique())

    with st.expander("View Prior Study Spec"):
        st.dataframe(prior_spec, use_container_width=True)

    uploaded = st.file_uploader("Upload variable list CSV", type="csv", key="stage0")

    if uploaded:
        df = pd.read_csv(uploaded)
        if "variable_name" in df.columns and "label" in df.columns:
            reuse_results = run_reuse_check(df, prior_spec)

            reused   = reuse_results[reuse_results["method"] == "REUSE"]
            no_match = reuse_results[reuse_results["method"] == "NO_MATCH"]

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Variables",    len(reuse_results))
            c2.metric("🔵 Reused",          f"{len(reused)} ({len(reused)/len(reuse_results):.0%})")
            c3.metric("🟣 Needs ML",        f"{len(no_match)} ({len(no_match)/len(reuse_results):.0%})")

            st.subheader("Reuse Results")
            reuse_results["method_icon"] = reuse_results["method"].map(METHOD_COLOR)
            st.dataframe(
                reuse_results[["method_icon","variable_name","label",
                               "predicted_domain","confidence","source_study"]],
                use_container_width=True
            )

            if st.button("▶ Pass to Stage 1 — Run ML on unmatched variables", type="primary"):
                st.session_state.stage0_df = reuse_results
                st.success(f"{len(reused)} variables reused · {len(no_match)} passing to ML · Switch to Stage 1 tab")
        else:
            st.error("CSV must have columns: variable_name, label")

    if not uploaded:
        st.markdown("""
        **How Stage 0 works:**
        - Exact match on variable name against prior study spec
        - Match found → domain assigned at confidence 1.0 (AUTO-ACCEPT)
        - No match → passed to Stage 1 ML classifier
        - Custom sponsor variables (e.g. BMRN_ENZY_LVL) reused from prior studies
        """)

# ── STAGE 1 ────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Stage 1 — ML Domain Classification")

    if st.session_state.stage0_df is None:
        st.warning("Complete Stage 0 first — upload a variable list and pass to Stage 1.")
    else:
        stage0_df = st.session_state.stage0_df
        no_match  = stage0_df[stage0_df["method"] == "NO_MATCH"]
        reused    = stage0_df[stage0_df["method"] == "REUSE"]

        st.info(f"{len(reused)} variables already assigned via reuse · Running ML on {len(no_match)} unmatched variables")

        if len(no_match) == 0:
            st.success("All variables matched in prior spec — no ML needed!")
            ml_results = pd.DataFrame()
        else:
            ml_rows = []
            for _, row in no_match.iterrows():
                r = predict_domain(row["variable_name"], row["label"], model)
                ml_rows.append({
                    "variable_name":    r["variable_name"],
                    "label":            r["label"],
                    "predicted_domain": r["predicted_domain"],
                    "confidence":       r["confidence"],
                    "review_tier":      r["review_tier"],
                    "method":           "ML",
                    "source_study":     "—",
                })
            ml_results = pd.DataFrame(ml_rows)

            total    = len(ml_results)
            auto     = len(ml_results[ml_results["review_tier"] == "AUTO-ACCEPT"])
            review   = len(ml_results[ml_results["review_tier"] == "HUMAN-REVIEW"])
            escalate = len(ml_results[ml_results["review_tier"] == "ESCALATE"])

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("ML Predictions",     total)
            c2.metric("🟢 Auto-Accept",     f"{auto} ({auto/total:.0%})")
            c3.metric("🟡 Human Review",    f"{review} ({review/total:.0%})")
            c4.metric("🔴 Escalate",        f"{escalate} ({escalate/total:.0%})")

            st.subheader("Review & Override ML Predictions")
            edited_rows = []
            for _, row in ml_results.iterrows():
                c1, c2, c3, c4, c5 = st.columns([2,3,2,2,2])
                c1.write(f"**{row['variable_name']}**")
                c2.write(row["label"])
                override = c3.selectbox(
                    "Domain",
                    DOMAINS,
                    index=DOMAINS.index(row["predicted_domain"]) if row["predicted_domain"] in DOMAINS else 0,
                    key=f"ml_{row['variable_name']}"
                )
                c4.write(f"{row['confidence']:.1%}")
                c5.write(f"{TIER_COLOR.get(row['review_tier'],'')} {row['review_tier']}")
                edited_rows.append({
                    "variable_name":    row["variable_name"],
                    "label":            row["label"],
                    "predicted_domain": row["predicted_domain"],
                    "final_domain":     override,
                    "confidence":       row["confidence"],
                    "review_tier":      row["review_tier"],
                    "method":           "ML",
                    "source_study":     "—",
                    "overridden":       override != row["predicted_domain"],
                })

        # Combine reuse + ML results
        reuse_rows = []
        for _, row in reused.iterrows():
            reuse_rows.append({
                "variable_name":    row["variable_name"],
                "label":            row["label"],
                "predicted_domain": row["predicted_domain"],
                "final_domain":     row["predicted_domain"],
                "confidence":       1.0,
                "review_tier":      "AUTO-ACCEPT",
                "method":           "REUSE",
                "source_study":     row["source_study"],
                "overridden":       False,
            })

        if st.button("✅ Confirm All — Proceed to Stage 2", type="primary"):
            combined = reuse_rows + (edited_rows if len(no_match) > 0 else [])
            st.session_state.stage1_df = pd.DataFrame(combined)
            st.session_state.confirmed = True
            overrides = sum(1 for r in (edited_rows if len(no_match) > 0 else []) if r["overridden"])
            st.success(f"Confirmed {len(combined)} variables · {len(reuse_rows)} reused · {overrides} ML overridden · Switch to Stage 2")

# ── STAGE 2 ────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Stage 2 — SDTM Mapping & Validation")

    if not st.session_state.confirmed or st.session_state.stage1_df is None:
        st.warning("Complete Stage 0 and Stage 1 first.")
    else:
        stage1_df = st.session_state.stage1_df
        reused_count   = len(stage1_df[stage1_df["method"] == "REUSE"])
        ml_count       = len(stage1_df[stage1_df["method"] == "ML"])
        override_count = len(stage1_df[stage1_df["overridden"] == True])

        st.success(f"Received {len(stage1_df)} variables · 🔵 {reused_count} reused · 🟣 {ml_count} ML · {override_count} overridden")

        if st.button("▶ Run Mapping & Validation", type="primary"):
            with st.spinner("Mapping all domains..."):
                results = {}
                for domain in ["dm","lb","ae","vs"]:
                    try:
                        results[domain.upper()] = map_domain(domain)
                    except Exception as e:
                        st.error(f"Mapping failed for {domain.upper()}: {e}")

            with st.spinner("Validating..."):
                from src.validator import validate_all
                report = validate_all(results)

            total_records = sum(len(df) for df in results.values())
            st.success(f"Pipeline complete — {total_records} records mapped across {len(results)} domains")

            for domain, df in results.items():
                df.to_csv(f"output/sdtm_{domain.lower()}.csv", index=False)
            report.to_csv("output/validation_report.csv", index=False)
            stage1_df.to_csv("output/traceability_report.csv", index=False)

            st.subheader("📋 Mapped SDTM Datasets")
            tabs = st.tabs(list(results.keys()))
            for tab, (domain, df) in zip(tabs, results.items()):
                with tab:
                    st.dataframe(df, use_container_width=True)
                    st.download_button(f"Download {domain}.csv",
                        df.to_csv(index=False), f"sdtm_{domain.lower()}.csv", "text/csv")

            st.subheader("⚠️ Validation Report")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Issues", len(report))
            c2.metric("Domains with Issues",
                len(report["domain"].unique()) if len(report) > 0 else 0)
            c3.metric("Records Mapped", total_records)

            if len(report) > 0:
                check_icons = {"MISSING_REQUIRED":"🔴","INVALID_CT":"🟠",
                               "WRONG_DTYPE":"🟡","DATE_FORMAT":"🟡"}
                report["icon"] = report["check_id"].map(check_icons).fillna("⚪")
                st.dataframe(
                    report[["icon","check_id","domain","variable","row","severity","message"]],
                    use_container_width=True)
                st.download_button("Download Validation Report",
                    report.to_csv(index=False), "validation_report.csv", "text/csv")
            else:
                st.success("No validation issues found!")

            st.subheader("🔗 Full Traceability Report")
            st.dataframe(
                stage1_df[["variable_name","label","method","source_study",
                           "predicted_domain","final_domain","confidence",
                           "review_tier","overridden"]],
                use_container_width=True)
            st.download_button("Download Traceability Report",
                stage1_df.to_csv(index=False), "traceability_report.csv", "text/csv")
