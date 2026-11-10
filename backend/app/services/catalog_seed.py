"""Curated campus-placement catalog. Inserted when missing, never overwritten."""

from sqlalchemy import func, select

from app.extensions import db
from app.models.catalog import CodingProblem, CodingTestCase, Company, CompanyQuestion
from app.services.company_bank import MORE_COMPANIES, extra_questions_for
from app.services.company_coding import COMPANY_CODING_PROBLEMS
from app.services.extra_problems import EXTRA_PROBLEMS

COMPANIES = [
    {
        "slug": "amazon",
        "name": "Amazon",
        "overview": "Campus interviews usually mix leadership principles with one coding or technical round.",
        "questions": [
            {
                "category": "hr",
                "topic": "Leadership",
                "difficulty": "intermediate",
                "prompt": "Tell me about a time you disagreed with a teammate and still delivered the work.",
                "preparation_tip": "Name the disagreement, your action, and the result. Do not only describe the team.",
            },
            {
                "category": "coding",
                "topic": "DSA",
                "difficulty": "intermediate",
                "prompt": "Given an array of integers, return the indices of two numbers that add up to a target.",
                "preparation_tip": "Say the brute-force approach, then a hash-map approach, and state both complexities.",
            },
        ],
    },
    {
        "slug": "tcs",
        "name": "TCS",
        "overview": "TCS campus rounds often start with HR and basics of programming, SQL, and projects.",
        "questions": [
            {
                "category": "hr",
                "topic": "Introduction",
                "difficulty": "beginner",
                "prompt": "Walk me through your final-year project and the part you built yourself.",
                "preparation_tip": "Separate your work from the team's work in the first two sentences.",
            },
            {
                "category": "technical",
                "topic": "SQL",
                "difficulty": "beginner",
                "prompt": "What is the difference between WHERE and HAVING?",
                "preparation_tip": "Give one query example for each clause.",
            },
        ],
    },
    {
        "slug": "infosys",
        "name": "Infosys",
        "overview": "Infosys placement screens commonly check communication, OOP basics, and a short coding task.",
        "questions": [
            {
                "category": "technical",
                "topic": "OOP",
                "difficulty": "beginner",
                "prompt": "Explain inheritance with an example from a project you have built.",
                "preparation_tip": "Use one parent class and one child class. Avoid a textbook-only definition.",
            },
            {
                "category": "coding",
                "topic": "Python",
                "difficulty": "beginner",
                "prompt": "Write a function that returns the number of vowels in a string.",
                "preparation_tip": "Mention the empty-string case before you write the loop.",
            },
        ],
    },
]

PROBLEMS = [
    {
        "slug_title": "Sum of two integers",
        "topic": "Python",
        "difficulty": "beginner",
        "statement": "Read two integers from stdin, separated by a space, and print their sum.",
        "company": "tcs",
        "starter": {
            "python": "a, b = map(int, input().split())\nprint(a + b)\n",
            "java": (
                "import java.util.Scanner;\n"
                "public class Main {\n"
                "    public static void main(String[] args) {\n"
                "        Scanner scanner = new Scanner(System.in);\n"
                "        int a = scanner.nextInt();\n"
                "        int b = scanner.nextInt();\n"
                "        System.out.println(a + b);\n"
                "    }\n"
                "}\n"
            ),
            "cpp": (
                "#include <iostream>\n"
                "int main() {\n"
                "    int a, b;\n"
                "    std::cin >> a >> b;\n"
                "    std::cout << a + b << std::endl;\n"
                "    return 0;\n"
                "}\n"
            ),
        },
        "tests": [
            ("2 3\n", "5\n", False),
            ("10 20\n", "30\n", True),
        ],
    },
    {
        "slug_title": "Count vowels",
        "topic": "Python",
        "difficulty": "beginner",
        "statement": "Read one line and print how many vowels (a, e, i, o, u) it contains. Matching is case-insensitive.",
        "company": "infosys",
        "starter": {
            "python": "text = input().lower()\nprint(sum(ch in 'aeiou' for ch in text))\n",
            "java": (
                "import java.util.Scanner;\n"
                "public class Main {\n"
                "    public static void main(String[] args) {\n"
                "        Scanner scanner = new Scanner(System.in);\n"
                "        String text = scanner.nextLine().toLowerCase();\n"
                "        int count = 0;\n"
                "        for (int i = 0; i < text.length(); i++) {\n"
                "            if (\"aeiou\".indexOf(text.charAt(i)) >= 0) count++;\n"
                "        }\n"
                "        System.out.println(count);\n"
                "    }\n"
                "}\n"
            ),
            "cpp": (
                "#include <cctype>\n#include <iostream>\n#include <string>\n"
                "int main() {\n"
                "    std::string text;\n"
                "    std::getline(std::cin, text);\n"
                "    int count = 0;\n"
                "    for (char ch : text) {\n"
                "        char lower = std::tolower(static_cast<unsigned char>(ch));\n"
                "        if (std::string(\"aeiou\").find(lower) != std::string::npos) count++;\n"
                "    }\n"
                "    std::cout << count << std::endl;\n"
                "    return 0;\n"
                "}\n"
            ),
        },
        "tests": [
            ("Interview\n", "4\n", False),
            ("Rhythm\n", "0\n", True),
        ],
    },
]


def ensure_catalog() -> None:
    catalog = [*COMPANIES, *MORE_COMPANIES]
    if _catalog_complete(catalog):
        return
    for item in catalog:
        item = {**item, "questions": [*item["questions"], *extra_questions_for(item["slug"])]}
        company = db.session.scalar(select(Company).where(Company.slug == item["slug"]))
        if company is None:
            company = Company(name=item["name"], slug=item["slug"], overview=item["overview"])
            db.session.add(company)
            db.session.flush()
        existing_prompts = set(
            db.session.scalars(
                select(CompanyQuestion.prompt).where(CompanyQuestion.company_id == company.id)
            )
        )
        for question in item["questions"]:
            if question["prompt"] in existing_prompts:
                continue
            db.session.add(
                CompanyQuestion(
                    company_id=company.id,
                    source="curated",
                    **question,
                )
            )
    companies = {
        company.slug: company.id
        for company in db.session.scalars(select(Company))
    }
    for problem in [*PROBLEMS, *EXTRA_PROBLEMS, *COMPANY_CODING_PROBLEMS]:
        exists = db.session.scalar(
            select(CodingProblem).where(CodingProblem.title == problem["slug_title"])
        )
        if exists is not None:
            continue
        row = CodingProblem(
            company_id=companies.get(problem["company"]),
            title=problem["slug_title"],
            statement=problem["statement"],
            difficulty=problem["difficulty"],
            topic=problem["topic"],
            starter_code=problem["starter"],
            time_limit_ms=2000,
            memory_limit_kb=128000,
            source="curated",
        )
        db.session.add(row)
        db.session.flush()
        for stdin, expected, hidden in problem["tests"]:
            db.session.add(
                CodingTestCase(
                    problem_id=row.id,
                    stdin=stdin,
                    expected_stdout=expected,
                    is_hidden=hidden,
                    weight=1,
                )
            )
    db.session.commit()


def _catalog_complete(catalog: list[dict]) -> bool:
    """Skip the full seeding pass when every curated row is already stored."""
    problems = len(PROBLEMS) + len(EXTRA_PROBLEMS) + len(COMPANY_CODING_PROBLEMS)
    stored_companies = db.session.scalar(select(func.count()).select_from(Company)) or 0
    stored_problems = db.session.scalar(
        select(func.count()).select_from(CodingProblem).where(CodingProblem.source == "curated")
    ) or 0
    questions = sum(
        len(item["questions"]) + len(extra_questions_for(item["slug"])) for item in catalog
    )
    stored_questions = db.session.scalar(
        select(func.count()).select_from(CompanyQuestion).where(CompanyQuestion.source == "curated")
    ) or 0
    return (
        stored_companies >= len(catalog)
        and stored_problems >= problems
        and stored_questions >= questions
    )
