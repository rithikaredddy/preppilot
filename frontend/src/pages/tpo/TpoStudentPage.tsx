import { useEffect, useState } from "react"
import { Link, useParams } from "react-router"
import { Alert, PageHeader, ScoreBar, Skeleton } from "../../components/ui"
import { ApiError, api } from "../../services/api"
import type { StudentDetail } from "../../types"

function BackLink() {
  return (
    <Link to="/tpo" className="text-sm font-medium text-brand hover:underline">
      ← Back to the batch
    </Link>
  )
}

export function TpoStudentPage() {
  const { studentId } = useParams()
  const [student, setStudent] = useState<StudentDetail | null>(null)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!studentId) return
    api<StudentDetail>(`/api/v1/tpo/students/${studentId}`)
      .then(setStudent)
      .catch((caught) => setError(caught instanceof ApiError ? caught.message : "That student could not be loaded."))
  }, [studentId])

  if (error) {
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <BackLink />
        <Alert>{error}</Alert>
      </div>
    )
  }
  if (!student) {
    return (
      <div className="mx-auto max-w-3xl space-y-4" role="status" aria-label="Loading the score breakdown">
        <BackLink />
        <Skeleton className="h-24" />
        <Skeleton className="h-40" />
      </div>
    )
  }

  const readiness = student.readiness_percentage
  const shown = readiness === null ? null : Math.round(readiness)
  const tone = shown === null ? "text-muted" : shown < 60 ? "text-clay" : shown >= 75 ? "text-pine" : "text-brand"

  return (
    <div className="mx-auto max-w-3xl">
      <BackLink />
      <div className="mt-4">
        <PageHeader
          kicker="Student breakdown"
          title={student.full_name}
          body={[
            student.roll_number,
            student.branch,
            `Class of ${student.graduation_year}`,
            student.cgpa === null ? null : `CGPA ${student.cgpa}`,
          ]
            .filter(Boolean)
            .join(" · ")}
        />
      </div>
      <section className="mt-6 rounded-2xl border border-line bg-foam shadow-card p-5">
        <p className="text-sm text-muted">Placement readiness</p>
        <p className={`mt-1 font-serif text-5xl ${tone}`}>{readiness === null ? "—" : `${Math.round(readiness)}%`}</p>
        <p className="mt-2 text-sm text-muted">{student.headline ?? "This student has no stored scores yet."}</p>
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          {student.scores.map((item) => (
            <ScoreBar key={item.category} label={item.label} value={item.score} />
          ))}
        </div>
      </section>
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <section className="rounded-2xl border border-line bg-foam shadow-card p-5">
          <h2 className="font-serif text-2xl">Weak areas</h2>
          {student.weak_areas.length === 0 ? (
            <p className="mt-2 text-sm text-muted">No score is below 60.</p>
          ) : (
            <ul className="mt-2 space-y-1 text-sm">
              {student.weak_areas.map((item) => (
                <li key={item.category} className="flex justify-between">
                  <span>{item.label}</span>
                  <span className="font-medium text-clay">{item.score === null ? "—" : Math.round(item.score)}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
        <section className="rounded-2xl border border-line bg-foam shadow-card p-5">
          <h2 className="font-serif text-2xl">Technical domains</h2>
          {student.domains.length === 0 ? (
            <p className="mt-2 text-sm text-muted">No technical interview yet.</p>
          ) : (
            <ul className="mt-2 space-y-1 text-sm">
              {student.domains.map((domain) => (
                <li key={domain.domain} className="flex justify-between gap-3">
                  <span>{domain.domain}</span>
                  <span className="text-muted">
                    <span className="font-medium text-ink">{Math.round(domain.score)}</span> · {domain.sessions} session
                    {domain.sessions === 1 ? "" : "s"}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
      <p className="mt-4 text-xs text-muted">Interview transcripts are private to the student and are not shown here.</p>
    </div>
  )
}
