"""Placement readiness prediction.

Training data is a realistically generated synthetic dataset with correlated
features, not independent random noise. Real institutional placement outcomes
are not available. This is a proof-of-concept prediction pipeline, not a
production-accuracy model.
"""

from decimal import Decimal
from functools import lru_cache
from uuid import UUID

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sqlalchemy import select

from app.extensions import db
from app.models.insights import ReadinessHistory
from app.models.practice import PerformanceSummary

FEATURES = ("resume_ats", "interview_score", "coding_score", "communication_score")
LABELS = {
    "resume_ats": "Resume ATS score",
    "interview_score": "Interview performance",
    "coding_score": "Coding performance",
    "communication_score": "Communication",
}


@lru_cache(maxsize=1)
def trained_models() -> dict:
    """Fit Random Forest and Logistic Regression on the same synthetic set.

    The served percentage comes from the forest's class probability. Feature
    importances also come from the forest. Logistic regression is kept so the
    comparison can be shown in the API and the project report.
    """
    rng = np.random.default_rng(7)
    count = 900
    resume = np.clip(rng.normal(68, 14, count), 15, 100)
    interview = np.clip(resume * 0.35 + rng.normal(38, 12, count), 10, 100)
    coding = np.clip(resume * 0.2 + rng.normal(42, 16, count), 5, 100)
    communication = np.clip(interview * 0.55 + rng.normal(22, 10, count), 10, 100)
    latent = 0.18 * resume + 0.24 * interview + 0.42 * coding + 0.16 * communication
    placed = (latent + rng.normal(0, 5.5, count)) >= 63
    matrix = np.column_stack([resume, interview, coding, communication])

    forest = RandomForestClassifier(
        n_estimators=160, max_depth=6, min_samples_leaf=8, random_state=7
    )
    logistic = LogisticRegression(max_iter=400)
    forest_scores = cross_val_score(forest, matrix, placed, cv=5, scoring="accuracy")
    logistic_scores = cross_val_score(logistic, matrix, placed, cv=5, scoring="accuracy")
    forest.fit(matrix, placed)
    logistic.fit(matrix, placed)
    importances = sorted(
        (
            {"feature": name, "importance": round(float(value), 4)}
            for name, value in zip(FEATURES, forest.feature_importances_, strict=True)
        ),
        key=lambda item: item["importance"],
        reverse=True,
    )
    return {
        "forest": forest,
        "importances": importances,
        "comparison": {
            "random_forest_accuracy": round(float(forest_scores.mean()), 3),
            "logistic_regression_accuracy": round(float(logistic_scores.mean()), 3),
            "selected": "random_forest",
        },
    }


def collect_features(student_id: UUID) -> dict | None:
    summary = db.session.get(PerformanceSummary, student_id)
    if summary is None:
        return None
    resume = _float(summary.resume_score)
    hr = _float(summary.hr_score)
    technical = _float(summary.technical_score)
    coding = _float(summary.coding_score)
    communication = _float(summary.communication_score)
    interview_parts = [value for value in (hr, technical) if value is not None]
    interview = round(sum(interview_parts) / len(interview_parts), 2) if interview_parts else None
    measured = {
        "resume_ats": resume,
        "interview_score": interview,
        "coding_score": coding,
        "communication_score": communication,
    }
    if all(value is None for value in measured.values()):
        return None
    return {
        "measured": measured,
        "vector": [50.0 if value is None else float(value) for value in (measured[name] for name in FEATURES)],
        "missing": [name for name in FEATURES if measured[name] is None],
    }


def explain(vector: list[float], measured: dict | None = None) -> dict:
    bundle = trained_models()
    matrix = np.array([vector], dtype=float)
    probability = float(bundle["forest"].predict_proba(matrix)[0][1])
    percentage = round(probability * 100, 2)
    factors = []
    for item in bundle["importances"]:
        score = None if measured is None else measured.get(item["feature"])
        factors.append(
            {
                "feature": item["feature"],
                "label": LABELS[item["feature"]],
                "importance": item["importance"],
                "student_score": score,
            }
        )
    lead = factors[0]["label"]
    return {
        "readiness_percentage": percentage,
        "headline": f"{lead} is currently your biggest factor.",
        "top_factors": factors,
        "model_name": "random_forest",
        "comparison": bundle["comparison"],
    }


def live_snapshot(student_id: UUID) -> dict | None:
    features = collect_features(student_id)
    if features is None:
        return None
    result = explain(features["vector"], features["measured"])
    result["inputs"] = features["measured"]
    result["missing_inputs"] = features["missing"]
    return result


def predict_and_store(student_id: UUID) -> dict:
    snapshot = live_snapshot(student_id)
    if snapshot is None:
        return {"current": None, "history": history(student_id)}
    latest = db.session.scalar(
        select(ReadinessHistory)
        .where(ReadinessHistory.student_id == student_id)
        .order_by(ReadinessHistory.created_at.desc())
    )
    changed = latest is None or _changed(latest, snapshot)
    if changed:
        row = ReadinessHistory(
            student_id=student_id,
            readiness_percentage=Decimal(f"{snapshot['readiness_percentage']:.2f}"),
            top_factors=snapshot["top_factors"],
            inputs=snapshot["inputs"],
        )
        db.session.add(row)
        db.session.commit()
        db.session.refresh(row)
        snapshot["id"] = str(row.id)
        snapshot["created_at"] = row.created_at
    else:
        snapshot["id"] = str(latest.id)
        snapshot["created_at"] = latest.created_at
    return {"current": snapshot, "history": history(student_id)}


def what_if(payload: dict) -> dict:
    vector = [float(payload[name]) for name in FEATURES]
    measured = {name: round(float(payload[name]), 2) for name in FEATURES}
    result = explain(vector, measured)
    result["inputs"] = measured
    result["missing_inputs"] = []
    result["id"] = None
    result["created_at"] = None
    return result


def history(student_id: UUID) -> list[dict]:
    rows = db.session.scalars(
        select(ReadinessHistory)
        .where(ReadinessHistory.student_id == student_id)
        .order_by(ReadinessHistory.created_at.asc())
    )
    return [
        {
            "id": str(row.id),
            "readiness_percentage": float(row.readiness_percentage),
            "top_factors": row.top_factors,
            "inputs": row.inputs,
            "created_at": row.created_at,
        }
        for row in rows
    ]


def _changed(latest: ReadinessHistory, snapshot: dict) -> bool:
    if abs(float(latest.readiness_percentage) - snapshot["readiness_percentage"]) >= 0.5:
        return True
    stored = latest.inputs or {}
    return any(stored.get(name) != snapshot["inputs"].get(name) for name in FEATURES)


def _float(value) -> float | None:
    if value is None:
        return None
    return float(value)
