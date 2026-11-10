from flask import request, send_file
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.errors import ApiError
from app.schemas.practice import (
    AnalyzeResumeSchema,
    ResumeAnalysisSchema,
    ResumeListSchema,
    ResumeSchema,
)
from app.services import resume_service
from app.services.access import require_student

blp = Blueprint("resumes", __name__, url_prefix="/api/v1", description="Resume analyzer")


@blp.route("/resumes")
class Resumes(MethodView):
    @jwt_required()
    @blp.response(200, ResumeListSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def get(self):
        """List the signed-in student's resumes."""
        student = require_student()
        return {
            "items": [
                resume_service.public_resume(resume)
                for resume in resume_service.list_resumes(student)
            ]
        }

    @jwt_required()
    @blp.response(201, ResumeSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def post(self):
        """Store a PDF or DOCX resume and its extracted text."""
        student = require_student()
        upload = request.files.get("file")
        if upload is None:
            raise ApiError(400, "file_required", "Choose a PDF or DOCX resume.")
        resume = resume_service.save_upload(student, upload)
        return resume_service.public_resume(resume)


@blp.route("/resumes/<uuid:resume_id>")
class ResumeDetail(MethodView):
    @jwt_required()
    @blp.response(200, ResumeSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def get(self, resume_id):
        """Return one resume, including a text preview."""
        student = require_student()
        resume = resume_service.get_resume(student, resume_id)
        return resume_service.public_resume(resume, preview=True)


@blp.route("/resumes/<uuid:resume_id>/analyze")
class AnalyzeResume(MethodView):
    @jwt_required()
    @blp.arguments(AnalyzeResumeSchema)
    @blp.response(201, ResumeAnalysisSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def post(self, data, resume_id):
        """Analyze a stored resume with the configured language model."""
        student = require_student()
        resume = resume_service.get_resume(student, resume_id)
        analysis = resume_service.analyze(
            student, resume, data["target_role"], data.get("job_description", "")
        )
        return resume_service.public_analysis(analysis)


@blp.route("/resume-analyses/<uuid:analysis_id>")
class AnalysisDetail(MethodView):
    @jwt_required()
    @blp.response(200, ResumeAnalysisSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def get(self, analysis_id):
        """Return one stored resume analysis."""
        student = require_student()
        return resume_service.public_analysis(resume_service.get_analysis(student, analysis_id))


@blp.route("/resume-analyses/<uuid:analysis_id>/report")
class AnalysisReport(MethodView):
    @jwt_required()
    @blp.doc(security=[{"bearerAuth": []}])
    def get(self, analysis_id):
        """Download the stored analysis as a PDF."""
        student = require_student()
        analysis = resume_service.get_analysis(student, analysis_id)
        return send_file(
            resume_service.build_report(analysis),
            mimetype="application/pdf",
            as_attachment=True,
            download_name="resume-analysis.pdf",
        )
