export type Role = "student" | "tpo"

export type User = {
  id: string
  email: string
  role: Role
  full_name: string
  roll_number: string | null
  branch: string | null
  graduation_year: number | null
  cgpa: number | null
  backlogs: number | null
  internship_count: number | null
  certification_count: number | null
  project_count: number | null
  phone: string | null
  target_companies: string | null
  department: string | null
  designation: string | null
}

export type AuthResponse = {
  access_token: string
  refresh_token: string
  user: User
}

export type DashboardSummary = {
  resume_score: number | null
  hr_score: number | null
  technical_score: number | null
  coding_score: number | null
  communication_score: number | null
  completed_sessions: number
}

export type StudentListItem = {
  id: string
  full_name: string
  email: string
  roll_number: string
  branch: string
  graduation_year: number
  readiness_percentage: number | null
  top_factor: string | null
}

export type StudentList = {
  items: StudentListItem[]
  page: number
  page_size: number
  total: number
}

export type ResumeAnalysis = {
  id: string
  resume_id: string
  target_role: string
  job_description: string
  ats_score: number
  skill_match_percentage: number
  skills: string[]
  education: string[]
  projects: string[]
  experience: string[]
  certifications: string[]
  missing_skills: string[]
  formatting_issues: string[]
  suggestions: string[]
  provider: string
  model_name: string
  created_at: string
}

export type ResumeItem = {
  id: string
  original_filename: string
  file_size_bytes: number
  created_at: string
  latest_analysis: ResumeAnalysis | null
  extracted_preview?: string
  character_count?: number
}

export type InterviewTurn = {
  id: string
  turn_index: number
  question_text: string
  answer_text: string | null
  is_follow_up: boolean
  evaluation: { scores: Record<string, number>; feedback: string } | null
}

export type InterviewSession = {
  id: string
  kind: "hr" | "technical"
  topic: string | null
  difficulty: string | null
  resume_id: string | null
  status: "in_progress" | "completed" | "abandoned"
  overall_score: number | null
  dimension_scores: Record<string, number> | null
  strengths: string[] | null
  improvements: string[] | null
  weak_areas: string[] | null
  started_at: string
  completed_at: string | null
  turn_count: number
  answered_count: number
  can_finish: boolean
  turns?: InterviewTurn[]
}

export type InterviewList = {
  items: InterviewSession[]
  page: number
  page_size: number
  total: number
}

export type ScoreCard = {
  category: string
  label: string
  score: number | null
}

export type Analytics = {
  scores: ScoreCard[]
  timeline: { recorded_at: string; category: string; label: string; score: number }[]
  domains: { domain: string; score: number; sessions: number }[]
  weak_areas: ScoreCard[]
  strong_areas: ScoreCard[]
  gap: {
    base_gap: number
    remaining_gap: number
    completed_items: number
    total_items: number
  }
}

export type ReadinessFactor = {
  feature: string
  label: string
  importance: number
  student_score: number | null
}

export type Readiness = {
  readiness_percentage: number
  headline: string
  top_factors: ReadinessFactor[]
  inputs: {
    resume_ats: number | null
    interview_score: number | null
    coding_score: number | null
    communication_score: number | null
  }
  missing_inputs: string[]
}

export type ReadinessView = {
  current: Readiness | null
  history: { id: string; readiness_percentage: number; created_at: string }[]
}

export type CodingProblemSummary = {
  id: string
  title: string
  difficulty: string
  topic: string
  source: string
  company_name: string | null
  company_slug: string | null
}

export type CodingProblem = CodingProblemSummary & {
  statement: string
  starter_code: Record<string, string>
  time_limit_ms: number
  memory_limit_kb: number
  public_tests: { id: string; stdin: string; expected_stdout: string }[]
  hidden_test_count: number
}

export type RunCase = {
  passed: boolean
  status: string
  stdin: string
  expected_stdout: string
  stdout: string
  stderr: string
}

export type RunResult = {
  passed_count: number
  total_count: number
  results: RunCase[]
}

export type Submission = {
  id: string
  problem_title: string
  status: string
  passed_count: number
  total_count: number
  score: number
  ai_review: {
    summary: string
    issues: string[]
    suggestions: string[]
    time_complexity: string
    space_complexity: string
  } | null
  review_error: string | null
  results?: {
    passed: boolean
    status: string
    is_hidden: boolean
    stdin?: string
    expected_stdout?: string
    stdout?: string
    stderr?: string
  }[]
}

export type RoadmapItem = {
  id: string
  topic: string
  subtopic: string
  resource_title: string
  resource_link: string
  focus: string
  is_complete: boolean
}

export type RoadmapList = {
  items: RoadmapItem[]
  gap: Analytics["gap"]
  source: string | null
  note: string | null
}

export type Company = {
  id: string
  name: string
  slug: string
  overview: string
  question_count: number
}

export type CompanyQuestion = {
  id: string
  category: string
  topic: string
  difficulty: string
  prompt: string
  preparation_tip: string
  source: string
}

export type BatchInsights = {
  student_count: number
  below_threshold_count: number
  threshold: number
  branch_averages: { branch: string; average_readiness: number | null; student_count: number }[]
  common_weak_areas: { area: string; student_count: number }[]
}

export type StudentDetail = {
  id: string
  full_name: string
  roll_number: string
  branch: string
  graduation_year: number
  cgpa: number | null
  readiness_percentage: number | null
  headline: string | null
  scores: ScoreCard[]
  weak_areas: ScoreCard[]
  strong_areas: ScoreCard[]
  domains: { domain: string; score: number; sessions: number }[]
}
