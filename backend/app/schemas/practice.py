from marshmallow import Schema, ValidationError, fields, validate, validates_schema

from app.services.interview_service import DIFFICULTIES, TECHNICAL_TOPICS


class AnalyzeResumeSchema(Schema):
    target_role = fields.String(required=True, validate=validate.Length(min=2, max=120))
    job_description = fields.String(load_default="", validate=validate.Length(max=30000))


class ResumeAnalysisSchema(Schema):
    id = fields.String(required=True)
    resume_id = fields.String(required=True)
    target_role = fields.String(required=True)
    job_description = fields.String(required=True)
    ats_score = fields.Float(required=True)
    skill_match_percentage = fields.Float(required=True)
    skills = fields.List(fields.String(), required=True)
    education = fields.List(fields.String(), required=True)
    projects = fields.List(fields.String(), required=True)
    experience = fields.List(fields.String(), required=True)
    certifications = fields.List(fields.String(), required=True)
    missing_skills = fields.List(fields.String(), required=True)
    formatting_issues = fields.List(fields.String(), required=True)
    suggestions = fields.List(fields.String(), required=True)
    provider = fields.String(required=True)
    model_name = fields.String(required=True)
    created_at = fields.DateTime(required=True)


class ResumeSchema(Schema):
    id = fields.String(required=True)
    original_filename = fields.String(required=True)
    file_size_bytes = fields.Integer(required=True)
    created_at = fields.DateTime(required=True)
    latest_analysis = fields.Nested(ResumeAnalysisSchema, allow_none=True)
    extracted_preview = fields.String()
    character_count = fields.Integer()


class ResumeListSchema(Schema):
    items = fields.List(fields.Nested(ResumeSchema), required=True)


class StartInterviewSchema(Schema):
    kind = fields.String(required=True, validate=validate.OneOf(["hr", "technical"]))
    topic = fields.String(required=False, allow_none=True, validate=validate.Length(max=80))
    difficulty = fields.String(required=False, allow_none=True, validate=validate.Length(max=16))
    resume_id = fields.UUID(required=False, allow_none=True)

    @validates_schema
    def check_technical(self, data, **_kwargs):
        if data.get("kind") != "technical":
            return
        errors = {}
        if data.get("topic") not in TECHNICAL_TOPICS:
            errors["topic"] = ["Choose one of the placement topics."]
        if data.get("difficulty") not in DIFFICULTIES:
            errors["difficulty"] = ["Choose beginner, intermediate, or advanced."]
        if errors:
            raise ValidationError(errors)


class AnswerSchema(Schema):
    answer = fields.String(required=True, validate=validate.Length(min=1, max=4000))


class PageQuerySchema(Schema):
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    page_size = fields.Integer(load_default=20, validate=validate.Range(min=1, max=50))


class InterviewTurnSchema(Schema):
    id = fields.String(required=True)
    turn_index = fields.Integer(required=True)
    question_text = fields.String(required=True)
    answer_text = fields.String(allow_none=True)
    is_follow_up = fields.Boolean(required=True)
    evaluation = fields.Raw(allow_none=True)


class InterviewSchema(Schema):
    id = fields.String(required=True)
    kind = fields.String(required=True)
    topic = fields.String(allow_none=True)
    difficulty = fields.String(allow_none=True)
    resume_id = fields.String(allow_none=True)
    status = fields.String(required=True)
    overall_score = fields.Float(allow_none=True)
    dimension_scores = fields.Raw(allow_none=True)
    strengths = fields.Raw(allow_none=True)
    improvements = fields.Raw(allow_none=True)
    weak_areas = fields.Raw(allow_none=True)
    started_at = fields.DateTime(required=True)
    completed_at = fields.DateTime(allow_none=True)
    turn_count = fields.Integer(required=True)
    answered_count = fields.Integer(required=True)
    can_finish = fields.Boolean(required=True)
    turns = fields.List(fields.Nested(InterviewTurnSchema))


class InterviewListSchema(Schema):
    items = fields.List(fields.Nested(InterviewSchema), required=True)
    page = fields.Integer(required=True)
    page_size = fields.Integer(required=True)
    total = fields.Integer(required=True)
