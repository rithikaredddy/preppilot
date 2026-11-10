from sqlalchemy import func, select

from app.errors import ApiError
from app.extensions import db
from app.models.catalog import Company, CompanyQuestion
from app.services.catalog_seed import ensure_catalog
from app.services.llm import complete_json, require_text

CATEGORIES = ("hr", "technical", "coding")
DIFFICULTIES = ("beginner", "intermediate", "advanced")
QUESTION_INSTRUCTIONS = """
Write original campus-placement practice questions for one company.
Return JSON: {"questions": [{"prompt": "...", "topic": "...", "preparation_tip": "..."}]}.
prompts must be new questions, not copies of famous leaked interview transcripts.
Each preparation_tip is one specific action.
""".strip()


def list_companies() -> list[dict]:
    ensure_catalog()
    companies = list(db.session.scalars(select(Company).order_by(Company.name)))
    return [public_company(company) for company in companies]


def questions_for(slug: str, category: str, difficulty: str, source: str) -> dict:
    ensure_catalog()
    company = _company(slug)
    query = select(CompanyQuestion).where(CompanyQuestion.company_id == company.id)
    if category:
        query = query.where(CompanyQuestion.category == category)
    if difficulty:
        query = query.where(CompanyQuestion.difficulty == difficulty)
    if source:
        query = query.where(CompanyQuestion.source == source)
    rows = list(db.session.scalars(query.order_by(CompanyQuestion.created_at)))
    return {
        "company": public_company(company),
        "items": [public_question(row) for row in rows],
    }


def generate_questions(slug: str, category: str, difficulty: str, count: int) -> dict:
    if category not in CATEGORIES:
        raise ApiError(422, "validation_error", "Choose hr, technical, or coding.")
    if difficulty not in DIFFICULTIES:
        raise ApiError(422, "validation_error", "Choose beginner, intermediate, or advanced.")
    ensure_catalog()
    company = _company(slug)
    parsed, _provider, _model = complete_json(
        QUESTION_INSTRUCTIONS,
        {
            "company": company.name,
            "overview": company.overview,
            "category": category,
            "difficulty": difficulty,
            "count": count,
        },
    )
    questions = parsed.get("questions")
    if not isinstance(questions, list) or not questions:
        raise ApiError(502, "llm_response_invalid", "The model did not return practice questions.")
    stored = []
    for item in questions[:count]:
        if not isinstance(item, dict):
            continue
        row = CompanyQuestion(
            company_id=company.id,
            category=category,
            difficulty=difficulty,
            topic=require_text({**item}, "topic", max_length=80),
            prompt=require_text(item, "prompt", max_length=500),
            preparation_tip=require_text(item, "preparation_tip", max_length=300),
            source="ai_generated",
        )
        db.session.add(row)
        stored.append(row)
    if len(stored) < 1:
        raise ApiError(502, "llm_response_invalid", "The model did not return practice questions.")
    db.session.commit()
    return {"company": public_company(company), "items": [public_question(row) for row in stored]}


def public_company(company: Company) -> dict:
    count = db.session.scalar(
        select(func.count())
        .select_from(CompanyQuestion)
        .where(CompanyQuestion.company_id == company.id)
    )
    return {
        "id": str(company.id),
        "name": company.name,
        "slug": company.slug,
        "overview": company.overview,
        "question_count": int(count or 0),
    }


def public_question(question: CompanyQuestion) -> dict:
    return {
        "id": str(question.id),
        "category": question.category,
        "topic": question.topic,
        "difficulty": question.difficulty,
        "prompt": question.prompt,
        "preparation_tip": question.preparation_tip,
        "source": question.source,
        "created_at": question.created_at,
    }


def _company(slug: str) -> Company:
    company = db.session.scalar(select(Company).where(Company.slug == slug))
    if company is None:
        raise ApiError(404, "not_found", "That company was not found.")
    return company
