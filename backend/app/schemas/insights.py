from marshmallow import Schema, fields, validate


class FactorSchema(Schema):
    feature = fields.String(required=True)
    label = fields.String(required=True)
    importance = fields.Float(required=True)
    student_score = fields.Float(allow_none=True)


class ReadinessSchema(Schema):
    id = fields.String(allow_none=True)
    readiness_percentage = fields.Float(required=True)
    headline = fields.String(required=True)
    top_factors = fields.List(fields.Nested(FactorSchema), required=True)
    inputs = fields.Dict(required=True)
    missing_inputs = fields.List(fields.String(), required=True)
    model_name = fields.String(required=True)
    comparison = fields.Dict(required=True)
    created_at = fields.DateTime(allow_none=True)


class HistoryPointSchema(Schema):
    id = fields.String(required=True)
    readiness_percentage = fields.Float(required=True)
    top_factors = fields.List(fields.Dict(), required=True)
    inputs = fields.Dict(required=True)
    created_at = fields.DateTime(required=True)


class ReadinessViewSchema(Schema):
    current = fields.Nested(ReadinessSchema, allow_none=True)
    history = fields.List(fields.Nested(HistoryPointSchema), required=True)


class WhatIfSchema(Schema):
    resume_ats = fields.Float(required=True, validate=validate.Range(min=0, max=100))
    interview_score = fields.Float(required=True, validate=validate.Range(min=0, max=100))
    coding_score = fields.Float(required=True, validate=validate.Range(min=0, max=100))
    communication_score = fields.Float(required=True, validate=validate.Range(min=0, max=100))


class ScoreCardSchema(Schema):
    category = fields.String(required=True)
    label = fields.String(required=True)
    score = fields.Float(allow_none=True)


class TimelinePointSchema(Schema):
    recorded_at = fields.DateTime(required=True)
    category = fields.String(required=True)
    label = fields.String(required=True)
    score = fields.Float(required=True)


class DomainScoreSchema(Schema):
    domain = fields.String(required=True)
    score = fields.Float(required=True)
    sessions = fields.Integer(required=True)


class GapSchema(Schema):
    base_gap = fields.Float(required=True)
    remaining_gap = fields.Float(required=True)
    completed_items = fields.Integer(required=True)
    total_items = fields.Integer(required=True)


class AnalyticsSchema(Schema):
    scores = fields.List(fields.Nested(ScoreCardSchema), required=True)
    timeline = fields.List(fields.Nested(TimelinePointSchema), required=True)
    domains = fields.List(fields.Nested(DomainScoreSchema), required=True)
    weak_areas = fields.List(fields.Nested(ScoreCardSchema), required=True)
    strong_areas = fields.List(fields.Nested(ScoreCardSchema), required=True)
    gap = fields.Nested(GapSchema, required=True)


class RoadmapItemSchema(Schema):
    id = fields.String(required=True)
    topic = fields.String(required=True)
    subtopic = fields.String(required=True)
    resource_title = fields.String(required=True)
    resource_link = fields.String(required=True)
    focus = fields.String(required=True)
    is_complete = fields.Boolean(required=True)
    created_at = fields.DateTime(required=True)


class RoadmapListSchema(Schema):
    items = fields.List(fields.Nested(RoadmapItemSchema), required=True)
    gap = fields.Nested(GapSchema, required=True)
    source = fields.String(allow_none=True)
    note = fields.String(allow_none=True)


class RoadmapUpdateSchema(Schema):
    is_complete = fields.Boolean(required=True)


class BranchAverageSchema(Schema):
    branch = fields.String(required=True)
    average_readiness = fields.Float(allow_none=True)
    student_count = fields.Integer(required=True)


class WeakCountSchema(Schema):
    area = fields.String(required=True)
    student_count = fields.Integer(required=True)


class InsightsSchema(Schema):
    student_count = fields.Integer(required=True)
    below_threshold_count = fields.Integer(required=True)
    threshold = fields.Integer(required=True)
    branch_averages = fields.List(fields.Nested(BranchAverageSchema), required=True)
    common_weak_areas = fields.List(fields.Nested(WeakCountSchema), required=True)


class StudentDetailSchema(Schema):
    id = fields.String(required=True)
    full_name = fields.String(required=True)
    email = fields.Email(required=True)
    roll_number = fields.String(required=True)
    branch = fields.String(required=True)
    graduation_year = fields.Integer(required=True)
    cgpa = fields.Float(allow_none=True)
    readiness_percentage = fields.Float(allow_none=True)
    headline = fields.String(allow_none=True)
    scores = fields.List(fields.Nested(ScoreCardSchema), required=True)
    weak_areas = fields.List(fields.Nested(ScoreCardSchema), required=True)
    strong_areas = fields.List(fields.Nested(ScoreCardSchema), required=True)
    domains = fields.List(fields.Nested(DomainScoreSchema), required=True)
