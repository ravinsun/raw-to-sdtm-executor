import joblib

def load_model(model_path="models/sdtm_classifier.pkl"):
    return joblib.load(model_path)

def get_review_tier(confidence):
    if confidence >= 0.85:
        return "AUTO-ACCEPT"
    elif confidence >= 0.65:
        return "HUMAN-REVIEW"
    else:
        return "ESCALATE"

def predict_domain(variable_name: str, label: str, model=None) -> dict:
    if model is None:
        model = load_model()
    text = f"{variable_name} {label}"
    domain = model.predict([text])[0]
    proba = model.predict_proba([text])[0]
    confidence = round(max(proba), 3)
    classes = model.classes_.tolist()
    top3 = sorted(zip(classes, proba), key=lambda x: x[1], reverse=True)[:3]
    return {
        "variable_name": variable_name,
        "label": label,
        "predicted_domain": domain,
        "confidence": confidence,
        "review_tier": get_review_tier(confidence),
        "top3": [(d, round(p, 3)) for d, p in top3]
    }

if __name__ == "__main__":
    tests = [
        ("LBTEST",   "Lab Test Name"),
        ("AESEV",    "Severity of Adverse Event"),
        ("VSSTRESN", "Vital Signs Numeric Result"),
        ("EXDOSE",   "Dose per Administration"),
        ("MHTERM",   "Medical History Term"),
    ]
    model = load_model()
    print(f"{'VARIABLE':<15} {'DOMAIN':<8} {'CONF':<8} TIER")
    print("-" * 45)
    for var, lbl in tests:
        r = predict_domain(var, lbl, model)
        print(f"{r['variable_name']:<15} {r['predicted_domain']:<8} {r['confidence']:<8} {r['review_tier']}")
