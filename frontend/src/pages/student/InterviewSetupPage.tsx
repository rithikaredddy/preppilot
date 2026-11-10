import { useEffect, useState, type FormEvent } from "react"
import { Link, useNavigate } from "react-router"
import { Alert, Button, LoadingLine, PageHeader, SelectField } from "../../components/ui"
import { errorMessage } from "../../lib/format"
import { api } from "../../services/api"
import type { InterviewSession, ResumeItem } from "../../types"

const topics = ["Java", "Python", "SQL", "DBMS", "OS", "Computer Networks", "OOP", "DSA", "ML"]
const difficulties = ["beginner", "intermediate", "advanced"]

export function HrInterviewPage() {
  return (
    <InterviewSetup
      kind="hr"
      kicker="HR interview"
      title="Practice an HR round"
      body="Answer behavioural questions by typing or speaking. Press Read question aloud whenever you want to hear a question. Confidence-related language scores how specific and definite the wording is. It does not judge your voice or emotion."
    />
  )
}

export function TechnicalInterviewPage() {
  return (
    <InterviewSetup
      kind="technical"
      kicker="Technical interview"
      title="Practice a technical round"
      body="Questions alternate between a short coding task and a concept question. You can type the code or speak it. Scores cover correctness, depth, clarity, and relevance."
    />
  )
}

function InterviewSetup({
  kind,
  kicker,
  title,
  body,
}: {
  kind: "hr" | "technical"
  kicker: string
  title: string
  body: string
}) {
  const navigate = useNavigate()
  const [topic, setTopic] = useState("SQL")
  const [difficulty, setDifficulty] = useState("beginner")
  const [resumeId, setResumeId] = useState("")
  const [resumes, setResumes] = useState<ResumeItem[]>([])
  const [pending, setPending] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    api<{ items: ResumeItem[] }>("/api/v1/resumes")
      .then((response) => setResumes(response.items))
      .catch(() => setResumes([]))
  }, [])

  async function start(event: FormEvent) {
    event.preventDefault()
    setError("")
    setPending(true)
    try {
      const session = await api<InterviewSession>("/api/v1/interviews", {
        method: "POST",
        body: JSON.stringify({
          kind,
          topic: kind === "technical" ? topic : null,
          difficulty: kind === "technical" ? difficulty : null,
          resume_id: resumeId || null,
        }),
      })
      navigate(`/app/interview/${session.id}`)
    } catch (caught) {
      setError(errorMessage(caught, "The interview could not be started."))
      setPending(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader kicker={kicker} title={title} body={body} />
      <form onSubmit={start} className="mt-8 grid gap-4 rounded-lg border border-line bg-foam p-5" aria-busy={pending}>
        {error ? <Alert>{error}</Alert> : null}
        {kind === "technical" ? (
          <>
            <SelectField id="topic" label="Topic" value={topic} onChange={(event) => setTopic(event.target.value)}>
              {topics.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </SelectField>
            <SelectField
              id="difficulty"
              label="Difficulty"
              value={difficulty}
              onChange={(event) => setDifficulty(event.target.value)}
            >
              {difficulties.map((item) => (
                <option key={item} value={item}>
                  {item.charAt(0).toUpperCase() + item.slice(1)}
                </option>
              ))}
            </SelectField>
          </>
        ) : null}
        <SelectField id="resume" label="Saved resume" value={resumeId} onChange={(event) => setResumeId(event.target.value)}>
          <option value="">No resume</option>
          {resumes.map((resume) => (
            <option key={resume.id} value={resume.id}>
              {resume.original_filename}
            </option>
          ))}
        </SelectField>
        <p className="text-sm leading-relaxed text-muted">
          {resumes.length > 0 ? (
            "Choose a saved resume so the interviewer can ask about your own projects, or leave No resume."
          ) : (
            <>
              No resume is saved yet. You can start without one, or{" "}
              <Link to="/app/resume" className="font-medium text-navy underline-offset-2 hover:underline">
                upload a resume first
              </Link>
              .
            </>
          )}
        </p>
        {pending ? <LoadingLine label="Preparing your first question…" detail="This can take a few seconds." /> : null}
        <div>
          <Button type="submit" pending={pending} pendingLabel="Starting…">
            Start interview
          </Button>
        </div>
      </form>
    </div>
  )
}
