from marshmallow import Schema, fields, validate


class PublicTestSchema(Schema):
    id = fields.String(required=True)
    stdin = fields.String(required=True)
    expected_stdout = fields.String(required=True)


class CodingProblemSummarySchema(Schema):
    id = fields.String(required=True)
    title = fields.String(required=True)
    difficulty = fields.String(required=True)
    topic = fields.String(required=True)
    source = fields.String(required=True)
    company_name = fields.String(allow_none=True)
    company_slug = fields.String(allow_none=True)


class CodingProblemListSchema(Schema):
    items = fields.List(fields.Nested(CodingProblemSummarySchema), required=True)


class CodingProblemSchema(CodingProblemSummarySchema):
    statement = fields.String(required=True)
    starter_code = fields.Dict(required=True)
    time_limit_ms = fields.Integer(required=True)
    memory_limit_kb = fields.Integer(required=True)
    public_tests = fields.List(fields.Nested(PublicTestSchema), required=True)
    hidden_test_count = fields.Integer(required=True)


class SubmitCodeSchema(Schema):
    language = fields.String(required=True, validate=validate.OneOf(["python", "java", "cpp"]))
    source_code = fields.String(required=True, validate=validate.Length(min=1, max=20000))


class CodeReviewSchema(Schema):
    summary = fields.String(required=True)
    issues = fields.List(fields.String(), required=True)
    suggestions = fields.List(fields.String(), required=True)
    time_complexity = fields.String(required=True)
    space_complexity = fields.String(required=True)
    provider = fields.String(required=True)
    model_name = fields.String(required=True)


class CodingResultSchema(Schema):
    id = fields.String(required=True)
    is_hidden = fields.Boolean(required=True)
    passed = fields.Boolean(required=True)
    status = fields.String(required=True)
    time_ms = fields.Integer(allow_none=True)
    memory_kb = fields.Integer(allow_none=True)
    stdin = fields.String()
    expected_stdout = fields.String()
    stdout = fields.String()
    stderr = fields.String()


class CodingSubmissionSchema(Schema):
    id = fields.String(required=True)
    problem_id = fields.String(required=True)
    problem_title = fields.String(required=True)
    language = fields.String(required=True)
    status = fields.String(required=True)
    passed_count = fields.Integer(required=True)
    total_count = fields.Integer(required=True)
    score = fields.Float(required=True)
    execution_time_ms = fields.Integer(allow_none=True)
    memory_kb = fields.Integer(allow_none=True)
    ai_review = fields.Nested(CodeReviewSchema, allow_none=True)
    review_error = fields.String(allow_none=True)
    created_at = fields.DateTime(required=True)
    source_code = fields.String()
    results = fields.List(fields.Nested(CodingResultSchema))


class RunCaseSchema(Schema):
    passed = fields.Boolean(required=True)
    status = fields.String(required=True)
    stdin = fields.String(required=True)
    expected_stdout = fields.String(required=True)
    stdout = fields.String(required=True)
    stderr = fields.String(required=True)


class RunResultSchema(Schema):
    passed_count = fields.Integer(required=True)
    total_count = fields.Integer(required=True)
    results = fields.List(fields.Nested(RunCaseSchema), required=True)


class CodingSubmissionListSchema(Schema):
    items = fields.List(fields.Nested(CodingSubmissionSchema), required=True)
    page = fields.Integer(required=True)
    page_size = fields.Integer(required=True)
    total = fields.Integer(required=True)


class CompanySchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    slug = fields.String(required=True)
    overview = fields.String(required=True)
    question_count = fields.Integer(required=True)


class CompanyListSchema(Schema):
    items = fields.List(fields.Nested(CompanySchema), required=True)


class CompanyQuestionSchema(Schema):
    id = fields.String(required=True)
    category = fields.String(required=True)
    topic = fields.String(required=True)
    difficulty = fields.String(required=True)
    prompt = fields.String(required=True)
    preparation_tip = fields.String(required=True)
    source = fields.String(required=True)
    created_at = fields.DateTime(required=True)


class CompanyQuestionListSchema(Schema):
    company = fields.Nested(CompanySchema, required=True)
    items = fields.List(fields.Nested(CompanyQuestionSchema), required=True)


class CompanyQuestionQuerySchema(Schema):
    category = fields.String(
        load_default="", validate=validate.OneOf(["", "hr", "technical", "coding"])
    )
    difficulty = fields.String(
        load_default="", validate=validate.OneOf(["", "beginner", "intermediate", "advanced"])
    )
    source = fields.String(load_default="", validate=validate.OneOf(["", "curated", "ai_generated"]))


class GenerateQuestionsSchema(Schema):
    category = fields.String(required=True, validate=validate.OneOf(["hr", "technical", "coding"]))
    difficulty = fields.String(
        required=True, validate=validate.OneOf(["beginner", "intermediate", "advanced"])
    )
    count = fields.Integer(load_default=2, validate=validate.Range(min=1, max=5))


class CommunicationAnalysisSchema(Schema):
    id = fields.String(required=True)
    session_id = fields.String(allow_none=True)
    turn_id = fields.String(allow_none=True)
    transcript = fields.String(required=True)
    duration_seconds = fields.Float(required=True)
    words_per_minute = fields.Float(required=True)
    filler_count = fields.Integer(required=True)
    filler_words = fields.Dict(required=True)
    pause_count = fields.Integer(allow_none=True)
    clarity_feedback = fields.String(required=True)
    communication_score = fields.Float(required=True)
    created_at = fields.DateTime(required=True)


class CommunicationListSchema(Schema):
    items = fields.List(fields.Nested(CommunicationAnalysisSchema), required=True)
