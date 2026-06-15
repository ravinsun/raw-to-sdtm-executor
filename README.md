# SDTM Automation Pipeline 🧬
![Python](https://img.shields.io/badge/Python-3.14-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-UI-red) ![CDISC](https://img.shields.io/badge/CDISC-SDTM-green) ![ML](https://img.shields.io/badge/ML-95%25%20CV%20Accuracy-brightgreen) ![Stages](https://img.shields.io/badge/Pipeline-3%20Stages-orange)

End-to-end clinical data automation pipeline — Mapping Reuse + ML Classification + SDTM Mapping + Pinnacle 21-style Validation in one app.

## Pipeline Architecture
```
Raw EDC Variable List (CSV)
        |
[Stage 0 — Mapping Reuse Check]
  Exact match against prior study spec
  Known variables → domain at confidence 1.0 (AUTO-ACCEPT)
  Unknown variables → passed to Stage 1
        |
[Stage 1 — ML Domain Classification]
  Random Forest + TF-IDF (char + word n-grams)
  95% CV accuracy across 12 CDISC domains
  Three-tier review: AUTO-ACCEPT / HUMAN-REVIEW / ESCALATE
  Human reviews and overrides before mapping runs
        |
[Stage 2 — Mapping and Validation]
  Excel spec-driven ETL per domain
  Derivations: USUBJID concat, ISO 8601 dates, direct map
  Pinnacle 21-style validation checks
  Full traceability report per variable
        |
SDTM-compliant CSVs + Validation Report + Traceability Report
```

## Why Three Stages

This architecture directly answers the industry question of mapping reuse vs ML:

| Approach | Best For | Confidence |
|---|---|---|
| Stage 0 Reuse | Known variables from prior studies | 1.0 (exact match) |
| Stage 1 ML | New or unseen variables | 0.65-1.0 (pattern-based) |
| Hybrid (both) | Any study — known + unknown variables | Best of both |

Reuse wins for org-specific custom variables (e.g. BMRN_ENZY_LVL from a prior BioMarin study).
ML fills the gap for new variables the reuse lookup cannot find.

## Stage 0 — Mapping Reuse
- Exact match on variable name against prior study spec CSV
- Match found: domain assigned at confidence 1.0, skips ML entirely
- No match: passed to Stage 1 ML classifier
- Captures sponsor-specific custom variables not in CDISC standard
- Source study tracked in traceability report

## Stage 1 — SDTM Domain Classifier
- Random Forest + TF-IDF (character + word n-grams)
- 95% cross-validated accuracy across 12 CDISC domains
- Three-tier GxP review flagging:
  - AUTO-ACCEPT: confidence >= 85%
  - HUMAN-REVIEW: confidence 65-84%
  - ESCALATE: confidence < 65%
- Human-in-the-loop override before mapping runs
- Only runs on variables not resolved by Stage 0

## Stage 2 — Raw-to-SDTM Mapping Executor
- Excel spec-driven (Mapping sheet + Controlled_Terms sheet)
- Derivation rules: direct_map, format_date, concat_ids
- Domains: DM, LB, AE, VS
- Validation checks:
  - MISSING_REQUIRED: required SDTM variable is null
  - INVALID_CT: value not in CDISC controlled terminology
  - WRONG_DTYPE: numeric field contains non-numeric value
  - DATE_FORMAT: date not in ISO 8601 format

## Outputs
- SDTM-compliant CSV per domain (DM, LB, AE, VS)
- Pinnacle 21-style validation report
- Full traceability report showing:
  - variable_name, label
  - method (REUSE or ML)
  - source_study (for reused variables)
  - predicted_domain, final_domain
  - confidence, review_tier
  - overridden (Y/N — human changed ML prediction)

## Quick Start
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python src/train.py          # train ML model (Stage 1)
streamlit run app.py         # launch pipeline
```

## Time Savings vs Manual Process
| Step | Manual | With Pipeline | Savings |
|---|---|---|---|
| Domain assignment known vars | 3-4 hrs | Instant (reuse) | 99% |
| Domain assignment new vars | 3-4 hrs | 30 min (ML + review) | 80% |
| Mapping and derivations | 4-6 hrs | Automatic | 90% |
| Validation checks | 2-3 hrs | Seconds | 95% |
| Validation report | 1-2 hrs | Automatic | 100% |
| Total per study | 13-19 hrs | 1-2 hrs | ~88% |

## GxP Design Principles
- Human-in-the-loop review gate between Stage 1 and Stage 2
- Confidence-based three-tier flagging mirrors Pinnacle 21 severity levels
- Full traceability report for every domain assignment decision
- Audit trail shows method (REUSE vs ML), source, confidence, and override flag
- Spec-driven architecture — business rules in Excel, not hardcoded
- Models excluded from repo — retrain locally with python src/train.py

## Project Structure
```
data/
  sdtm_mapping_spec.xlsx       mapping spec (Mapping + Controlled_Terms sheets)
  prior_study_spec.csv         prior study variable catalog (Stage 0 lookup)
  raw_edc_dm.csv               raw EDC Demographics
  raw_edc_lb.csv               raw EDC Lab Results
  raw_edc_ae.csv               raw EDC Adverse Events
  raw_edc_vs.csv               raw EDC Vital Signs
src/
  reuse_checker.py             Stage 0 — mapping reuse lookup engine
  predict_domain.py            Stage 1 — ML domain classifier
  loader.py                    reads Excel spec and raw CSVs
  mapper.py                    applies mapping rules and derivations
  derivations.py               USUBJID concat, ISO 8601 date formatting
  validator.py                 Pinnacle 21-style validation checks
models/
  sdtm_classifier.pkl          trained Random Forest model (generated locally)
app.py                         Streamlit three-stage UI
output/                        generated SDTM CSVs + reports (gitignored)
```

## Domains Supported
DM · LB · AE · VS (Stage 2 mapping)
12 domains for classification: DM · AE · LB · VS · CM · EX · MH · DS · EG · PE · FA · SU

## Clinical AI Portfolio
- [SDTM Domain Classifier](https://github.com/ravinsun/sdtm-domain-classifier) — standalone ML classifier
- [ClinTranslate](https://github.com/ravinsun/clintranslate) — SAS-to-Python RAG Translator
- [ecrf-to-acrf](https://github.com/ravinsun/ecrf-to-acrf) — eCRF Annotation Engine

## Author
Ravinder Maramamula - github.com/ravinsun