# SDTM Automation Pipeline 🧬
![Python](https://img.shields.io/badge/Python-3.14-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-UI-red) ![CDISC](https://img.shields.io/badge/CDISC-SDTM-green) ![ML](https://img.shields.io/badge/ML-95%25%20CV%20Accuracy-brightgreen)

End-to-end clinical data automation pipeline combining ML-based domain classification with CDISC SDTM mapping and Pinnacle 21-style validation.

## Pipeline Architecture
```
Raw EDC Variable List (CSV)
        |
[Stage 1 — Domain Classification]
  ML predicts SDTM domain + confidence + review tier
  Human reviews and confirms (with override capability)
        |
[Stage 2 — Mapping and Validation]
  Excel spec-driven ETL per domain
  Derivations: USUBJID concat, ISO 8601 dates, direct map
  Pinnacle 21-style validation checks
        |
SDTM-compliant CSVs + Validation Report + Traceability Report
```

## Stage 1 — SDTM Domain Classifier
- Random Forest + TF-IDF (character + word n-grams)
- 95% cross-validated accuracy across 12 CDISC domains
- Three-tier GxP review flagging:
  - AUTO-ACCEPT: confidence >= 85%
  - HUMAN-REVIEW: confidence 65-84%
  - ESCALATE: confidence < 65%
- Human-in-the-loop override before mapping runs

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
- Traceability report (predicted domain, final domain, confidence, overridden flag)

## Quick Start
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Time Savings vs Manual Process
| Step | Manual | With Pipeline | Savings |
|---|---|---|---|
| Domain assignment 400 variables | 6-8 hrs | 30 min | 80% |
| Mapping and derivations | 4-6 hrs | Automatic | 90% |
| Validation checks | 2-3 hrs | Seconds | 95% |
| Validation report | 1-2 hrs | Automatic | 100% |

## GxP Design Principles
- Human-in-the-loop review gate between Stage 1 and Stage 2
- Confidence-based three-tier flagging mirrors Pinnacle 21 severity levels
- Full traceability report for every domain assignment decision
- Spec-driven architecture — business rules in Excel, not hardcoded

## Project Structure
```
data/
  sdtm_mapping_spec.xlsx     mapping spec (Mapping + Controlled_Terms sheets)
  raw_edc_dm.csv             raw EDC Demographics
  raw_edc_lb.csv             raw EDC Lab Results
  raw_edc_ae.csv             raw EDC Adverse Events
  raw_edc_vs.csv             raw EDC Vital Signs
src/
  loader.py                  reads Excel spec and raw CSVs
  mapper.py                  applies mapping rules and derivations
  derivations.py             USUBJID concat, ISO 8601 date formatting
  validator.py               Pinnacle 21-style validation checks
  predict_domain.py          ML domain classifier (Stage 1)
models/
  sdtm_classifier.pkl        trained Random Forest model (generated locally)
app.py                       Streamlit two-stage UI
output/                      generated SDTM CSVs + reports (gitignored)
```

## Clinical AI Portfolio
- [SDTM Domain Classifier](https://github.com/ravinsun/sdtm-domain-classifier) — standalone ML classifier
- [ClinTranslate](https://github.com/ravinsun/clintranslate) — SAS-to-Python RAG Translator
- [ecrf-to-acrf](https://github.com/ravinsun/ecrf-to-acrf) — eCRF Annotation Engine

## Author
Ravinder Maramamula - github.com/ravinsun