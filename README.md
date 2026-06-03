# Raw-to-SDTM Mapping Executor
![Python](https://img.shields.io/badge/Python-3.14-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-UI-red) ![CDISC](https://img.shields.io/badge/CDISC-SDTM-green)

Automates transformation of raw EDC clinical trial data into CDISC SDTM-compliant datasets with Pinnacle 21-style validation reporting.

## Domains Supported
DM, LB, AE, VS

## Validation Checks
- MISSING_REQUIRED: Required SDTM variable is null or empty
- INVALID_CT: Value not in CDISC controlled terminology
- WRONG_DTYPE: Numeric field contains non-numeric value
- DATE_FORMAT: Date not in ISO 8601 format (YYYY-MM-DD)

## Quick Start
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Project Structure
```
data/sdtm_mapping_spec.xlsx   - mapping spec
data/raw_edc_*.csv            - raw EDC data per domain
src/loader.py                 - reads spec and raw CSVs
src/mapper.py                 - applies mapping rules
src/derivations.py            - USUBJID concat, date formatting
src/validator.py              - Pinnacle 21-style validation
app.py                        - Streamlit UI
output/                       - generated SDTM CSVs + validation report
```

## Time Savings
| Step | Manual | With Tool | Savings |
|---|---|---|---|
| Domain mapping 400 variables | 6-8 hrs | 30 min | 80% |
| Validation checks | 2-3 hrs | Seconds | 95% |
| Validation report | 1-2 hrs | Automatic | 100% |

## Clinical AI Portfolio
- [SDTM Domain Classifier](https://github.com/ravinsun/sdtm-domain-classifier)
- [ClinTranslate](https://github.com/ravinsun/clintranslate)
- [ecrf-to-acrf](https://github.com/ravinsun/ecrf-to-acrf)

## Author
Ravinder Maramamula - github.com/ravinsun