from decimal import Decimal

from sqlalchemy import func, select

from app.errors import ApiError
from app.extensions import db
from app.models.catalog import (
    CodingProblem,
    CodingSubmission,
    CodingSubmissionResult,
    CodingTestCase,
    Company,
)
from app.models.user import User
from app.services import judge0, scoring
from app.services.catalog_seed import ensure_catalog
from app.services.llm import complete_json, require_string_list, require_text

LANGUAGES = ("python", "java", "cpp")
REVIEW_INSTRUCTIONS = """
Review this student program after it ran in a sandbox.
Use only the source, the public tests, and the pass counts. Do not invent hidden inputs.
Return JSON with keys summary, issues, suggestions, time_complexity, space_complexity.
summary is two sentences.
issues and suggestions are arrays of short strings.
time_complexity and space_complexity are big-O estimates such as O(n), or "not applicable" when the program does not run.
""".strip()


def list_problems() -> list[dict]:
    ensure_catalog()
    problems = list(db.session.scalars(select(CodingProblem).order_by(CodingProblem.title)))
    return [problem_card(problem) for problem in problems]


def problem_card(problem: CodingProblem) -> dict:
    company = _company(problem.company_id)
    return {
        "id": str(problem.id),
        "title": problem.title,
        "difficulty": problem.difficulty,
        "topic": problem.topic,
        "source": problem.source,
        "company_name": None if company is None else company.name,
        "company_slug": None if company is None else company.slug,
    }


def get_problem(problem_id) -> CodingProblem:
    ensure_catalog()
    problem = db.session.get(CodingProblem, problem_id)
    if problem is None:
        raise ApiError(404, "not_found", "That problem was not found.")
    return problem


def submit(student: User, problem: CodingProblem, language: str, source_code: str) -> CodingSubmission:
    if language not in LANGUAGES:
        raise ApiError(422, "validation_error", "Choose Python, Java, or C++.")
    code = source_code.strip()
    if not code:
        raise ApiError(422, "validation_error", "The editor is empty.")
    if len(code) > 20000:
        raise ApiError(422, "validation_error", "Keep the program under 20,000 characters.")
    cases = list(
        db.session.scalars(select(CodingTestCase).where(CodingTestCase.problem_id == problem.id))
    )
    runs = [
        _run_case(code, language, problem, case)
        for case in cases
    ]
    passed_weight = sum(case.weight for case, run in zip(cases, runs, strict=True) if run["passed"])
    total_weight = sum(case.weight for case in cases) or 1
    score = round(100 * passed_weight / total_weight, 2)
    passed_count = sum(1 for run in runs if run["passed"])
    status = _submission_status(runs)
    times = [run["time_ms"] for run in runs if run["time_ms"] is not None]
    memories = [run["memory_kb"] for run in runs if run["memory_kb"] is not None]
    review, review_error = _review(problem, code, language, cases, runs, status)
    submission = CodingSubmission(
        student_id=student.id,
        problem_id=problem.id,
        language=language,
        source_code=code,
        status=status,
        passed_count=passed_count,
        total_count=len(cases),
        score=Decimal(f"{score:.2f}"),
        execution_time_ms=max(times) if times else None,
        memory_kb=max(memories) if memories else None,
        ai_review=review,
    )
    db.session.add(submission)
    db.session.flush()
    for case, run in zip(cases, runs, strict=True):
        db.session.add(
            CodingSubmissionResult(
                submission_id=submission.id,
                test_case_id=case.id,
                passed=run["passed"],
                time_ms=run["time_ms"],
                memory_kb=run["memory_kb"],
                stdout=run["stdout"],
                stderr=run["stderr"],
                status=run["status"],
            )
        )
    scoring.record_score(
        student.id,
        "coding",
        score,
        "coding_submission",
        submission.id,
        (review or {}).get("suggestions", [])[:3],
        (review or {}).get("issues", [])[:3],
    )
    db.session.commit()
    submission.review_error = review_error  # type: ignore[attr-defined]
    return submission


def run_public(problem: CodingProblem, language: str, source_code: str) -> dict:
    """Execute public tests only. Nothing is stored."""
    if language not in LANGUAGES:
        raise ApiError(422, "validation_error", "Choose Python, Java, or C++.")
    code = source_code.strip()
    if not code:
        raise ApiError(422, "validation_error", "The editor is empty.")
    cases = [
        case
        for case in db.session.scalars(
            select(CodingTestCase).where(CodingTestCase.problem_id == problem.id)
        )
        if not case.is_hidden
    ]
    results = []
    for case in cases:
        run = _run_case(code, language, problem, case)
        results.append(
            {
                "passed": run["passed"],
                "status": run["status"],
                "stdin": case.stdin,
                "expected_stdout": case.expected_stdout,
                "stdout": run["stdout"],
                "stderr": run["stderr"],
            }
        )
    return {
        "passed_count": sum(1 for result in results if result["passed"]),
        "total_count": len(results),
        "results": results,
    }


def list_submissions(student: User, page: int, page_size: int) -> dict:
    query = select(CodingSubmission).where(CodingSubmission.student_id == student.id)
    total = db.session.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.session.scalars(
        query.order_by(CodingSubmission.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    return {
        "items": [public_submission(row, include_results=False) for row in rows],
        "page": page,
        "page_size": page_size,
        "total": int(total or 0),
    }


def get_submission(student: User, submission_id) -> CodingSubmission:
    submission = db.session.get(CodingSubmission, submission_id)
    if submission is None or submission.student_id != student.id:
        raise ApiError(404, "not_found", "That submission was not found.")
    return submission


def public_problem(problem: CodingProblem) -> dict:
    card = problem_card(problem)
    return {
        **card,
        "statement": problem.statement,
        "difficulty": problem.difficulty,
        "topic": problem.topic,
        "starter_code": problem.starter_code,
        "time_limit_ms": problem.time_limit_ms,
        "memory_limit_kb": problem.memory_limit_kb,
        "source": problem.source,
        "public_tests": [
            {"id": str(case.id), "stdin": case.stdin, "expected_stdout": case.expected_stdout}
            for case in problem.tests
            if not case.is_hidden
        ],
        "hidden_test_count": sum(1 for case in problem.tests if case.is_hidden),
    }


def public_submission(submission: CodingSubmission, *, include_results: bool) -> dict:
    problem = db.session.get(CodingProblem, submission.problem_id)
    payload = {
        "id": str(submission.id),
        "problem_id": str(submission.problem_id),
        "problem_title": problem.title if problem else "",
        "language": submission.language,
        "status": submission.status,
        "passed_count": submission.passed_count,
        "total_count": submission.total_count,
        "score": float(submission.score),
        "execution_time_ms": submission.execution_time_ms,
        "memory_kb": submission.memory_kb,
        "ai_review": submission.ai_review,
        "review_error": getattr(submission, "review_error", None),
        "created_at": submission.created_at,
    }
    if include_results:
        payload["source_code"] = submission.source_code
        payload["results"] = [_public_result(result) for result in submission.results]
    return payload


def _run_case(code: str, language: str, problem: CodingProblem, case: CodingTestCase) -> dict:
    outcome = judge0.execute(
        code, language, case.stdin, problem.time_limit_ms, problem.memory_limit_kb
    )
    expected = _normalize(case.expected_stdout)
    actual = _normalize(outcome.get("stdout") or "")
    passed = outcome.get("status") == "accepted" and actual == expected
    status = "accepted" if passed else outcome.get("status") or "wrong_answer"
    if outcome.get("status") == "accepted" and actual != expected:
        status = "wrong_answer"
    return {
        "passed": passed,
        "status": status,
        "stdout": outcome.get("stdout") or "",
        "stderr": outcome.get("stderr") or "",
        "time_ms": outcome.get("time_ms"),
        "memory_kb": outcome.get("memory_kb"),
    }


def _review(problem, code, language, cases, runs, status) -> tuple[dict | None, str | None]:
    public = [
        {"stdin": case.stdin, "expected_stdout": case.expected_stdout, "status": run["status"]}
        for case, run in zip(cases, runs, strict=True)
        if not case.is_hidden
    ]
    hidden_passed = sum(1 for case, run in zip(cases, runs, strict=True) if case.is_hidden and run["passed"])
    hidden_total = sum(1 for case in cases if case.is_hidden)
    try:
        parsed, provider, model = complete_json(
            REVIEW_INSTRUCTIONS,
            {
                "title": problem.title,
                "statement": problem.statement,
                "language": language,
                "source_code": code[:8000],
                "run_status": status,
                "public_tests": public,
                "hidden_passed": hidden_passed,
                "hidden_total": hidden_total,
            },
        )
    except ApiError as exc:
        return None, exc.description
    return {
        "summary": require_text(parsed, "summary"),
        "issues": require_string_list(parsed, "issues"),
        "suggestions": require_string_list(parsed, "suggestions", min_items=1, max_items=5),
        "time_complexity": require_text(parsed, "time_complexity", max_length=40),
        "space_complexity": require_text(parsed, "space_complexity", max_length=40),
        "provider": provider,
        "model_name": model,
    }, None


def _public_result(result: CodingSubmissionResult) -> dict:
    case = result.test_case
    hidden = bool(case and case.is_hidden)
    payload = {
        "id": str(result.id),
        "is_hidden": hidden,
        "passed": result.passed,
        "status": result.status,
        "time_ms": result.time_ms,
        "memory_kb": result.memory_kb,
    }
    if hidden:
        payload["stderr"] = (result.stderr or "")[:200]
        payload["stdout"] = "" if result.passed else (result.stdout or "")[:120]
    else:
        payload["stdin"] = case.stdin if case else ""
        payload["expected_stdout"] = case.expected_stdout if case else ""
        payload["stdout"] = result.stdout or ""
        payload["stderr"] = result.stderr or ""
    return payload


def _submission_status(runs: list[dict]) -> str:
    if runs and all(run["passed"] for run in runs):
        return "accepted"
    for name in ("compilation_error", "runtime_error", "time_limit"):
        if any(run["status"] == name for run in runs):
            return name
    return "wrong_answer"


def _company(company_id):
    if company_id is None:
        return None
    return db.session.get(Company, company_id)


def _normalize(value: str) -> str:
    return "\n".join(line.rstrip() for line in value.strip().splitlines())
