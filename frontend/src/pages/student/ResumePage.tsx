import { useEffect, useRef, useState, type FormEvent } from "react"
import { api, ApiError, downloadAuthenticated } from "../../services/api"
import type { ResumeAnalysis, ResumeItem } from "../../types"
import {
  Alert,
  Badge,
  Button,
  EmptyState,
  Field,
  LoadingLine,
  Notice,
  PageHeader,
  ScoreBar,
  Skeleton,
  TextArea,
} from "../../components/ui"
import { errorMessage, formatDate } from "../../lib/format"

type Busy = { kind: "upload" | "analyze" | "open"; resumeId?: string } | null

function sizeLabel(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function ResumePage() {
  const [resumes, setResumes] = useState<ResumeItem[] | null>(null)
  const [loadError, setLoadError] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const [targetRole, setTargetRole] = useState("")
  const [jobDescription, setJobDescription] = useState("")
  const [busy, setBusy] = useState<Busy>(null)
  const [formError, setFormError] = useState("")
  const [notice, setNotice] = useState("")
  const [analysis, setAnalysis] = useState<ResumeAnalysis | null>(null)
  const [downloading, setDownloading] = useState(false)
  const fileInput = useRef<HTMLInputElement>(null)
  const resultRef = useRef<HTMLElement>(null)

  useEffect(() => {
    api<{ items: ResumeItem[] }>("/api/v1/resumes")
      .then((response) => setResumes(response.items))
      .catch(() => setLoadError("Your saved resumes could not be loaded."))
  }, [])

  function upsertResume(next: ResumeItem) {
    setResumes((current) => [next, ...(current ?? []).filter((item) => item.id !== next.id)])
  }

  function showAnalysis(result: ResumeAnalysis) {
    setAnalysis(result)
    window.requestAnimationFrame(() => resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }))
  }

  function validateRole() {
    if (targetRole.trim().length < 2) {
      setFormError("Enter the role you are preparing for, for example Data analyst.")
      return false
    }
    return true
  }

  async function runAnalysis(resume: ResumeItem) {
    const result = await api<ResumeAnalysis>(`/api/v1/resumes/${resume.id}/analyze`, {
      method: "POST",
      body: JSON.stringify({ target_role: targetRole.trim(), job_description: jobDescription.trim() }),
    })
    upsertResume({ ...resume, latest_analysis: result })
    showAnalysis(result)
    setNotice("The analysis was saved to your account.")
  }

  async function uploadAndAnalyze(event: FormEvent) {
    event.preventDefault()
    setFormError("")
    setNotice("")
    if (!file) {
      setFormError("Choose a PDF or DOCX file.")
      return
    }
    if (!validateRole()) return
    let uploaded: ResumeItem | null = null
    try {
      setBusy({ kind: "upload" })
      const body = new FormData()
      body.set("file", file)
      uploaded = await api<ResumeItem>("/api/v1/resumes", { method: "POST", body })
      upsertResume(uploaded)
      setFile(null)
      if (fileInput.current) fileInput.current.value = ""
      setBusy({ kind: "analyze", resumeId: uploaded.id })
      await runAnalysis(uploaded)
    } catch (error) {
      const message = errorMessage(error, "The resume could not be analyzed.")
      setFormError(
        uploaded
          ? `${message} The file was saved, so you can use Analyze on it below without uploading again.`
          : message,
      )
    } finally {
      setBusy(null)
    }
  }

  async function analyzeExisting(item: ResumeItem) {
    setFormError("")
    setNotice("")
    if (!validateRole()) {
      document.getElementById("target-role")?.focus()
      return
    }
    setBusy({ kind: "analyze", resumeId: item.id })
    try {
      await runAnalysis(item)
    } catch (error) {
      setFormError(errorMessage(error, "The resume could not be analyzed."))
    } finally {
      setBusy(null)
    }
  }

  async function openAnalysis(item: ResumeItem) {
    if (!item.latest_analysis) return
    setFormError("")
    setNotice("")
    setBusy({ kind: "open", resumeId: item.id })
    try {
      const result = await api<ResumeAnalysis>(`/api/v1/resume-analyses/${item.latest_analysis.id}`)
      showAnalysis(result)
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "The analysis could not be loaded.")
    } finally {
      setBusy(null)
    }
  }

  async function downloadReport() {
    if (!analysis) return
    setDownloading(true)
    setFormError("")
    try {
      await downloadAuthenticated(`/api/v1/resume-analyses/${analysis.id}/report`, "resume-analysis.pdf")
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "The report could not be downloaded.")
    } finally {
      setDownloading(false)
    }
  }

  const working = busy !== null

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        kicker="Resume analyzer"
        title="Check a resume against a role"
        body="Upload a PDF or DOCX file and name the role you want. You get an ATS-style score, a skill match against the job description, and specific suggestions. Nothing is invented when the AI service is unavailable."
      />

      <div className="mt-8 grid gap-8 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <form onSubmit={uploadAndAnalyze} className="grid content-start gap-4" aria-busy={working}>
          {formError ? <Alert>{formError}</Alert> : null}
          {notice ? <Notice>{notice}</Notice> : null}
          <div className="text-sm">
            <label htmlFor="resume-file" className="mb-1.5 block font-medium">
              Resume file
            </label>
            <label
              htmlFor="resume-file"
              className="flex cursor-pointer flex-wrap items-center gap-3 rounded-xl border border-dashed border-line bg-foam px-4 py-4 transition hover:border-brand/40 focus-within:border-navy"
            >
              <span className="rounded-xl bg-navy px-3 py-1.5 text-xs font-semibold text-onbrand">Choose file</span>
              <span className={file ? "font-medium" : "text-muted"}>
                {file ? `${file.name} · ${sizeLabel(file.size)}` : "PDF or DOCX, up to 5 MB"}
              </span>
              <input
                ref={fileInput}
                id="resume-file"
                type="file"
                className="sr-only"
                disabled={working}
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              />
            </label>
          </div>
          <Field
            id="target-role"
            label="Target role"
            value={targetRole}
            disabled={working}
            onChange={(event) => setTargetRole(event.target.value)}
            placeholder="Data analyst"
            hint="Also used when you press Analyze on a saved resume."
          />
          <TextArea
            id="job-description"
            label="Job description (optional)"
            value={jobDescription}
            disabled={working}
            onChange={(event) => setJobDescription(event.target.value)}
            placeholder="Paste a job description. Leave this empty to match against a campus placement skill list."
          />
          {busy?.kind === "upload" ? <LoadingLine label="Uploading and reading your file…" /> : null}
          {busy?.kind === "analyze" ? (
            <LoadingLine
              label="Analyzing your resume…"
              detail="The AI reviewer is reading every section. This usually takes 10 to 30 seconds."
            />
          ) : null}
          <div>
            <Button type="submit" pending={busy?.kind === "upload"} pendingLabel="Uploading…" disabled={working}>
              Upload and analyze
            </Button>
          </div>
        </form>

        <aside className="content-start">
          <h2 className="font-serif text-2xl">Saved resumes</h2>
          {loadError ? (
            <div className="mt-3">
              <Alert>{loadError}</Alert>
            </div>
          ) : null}
          {resumes === null && !loadError ? (
            <div className="mt-3 space-y-2">
              <Skeleton className="h-16" />
              <Skeleton className="h-16" />
            </div>
          ) : null}
          {resumes?.length === 0 ? (
            <p className="mt-3 rounded-2xl border border-dashed border-line bg-foam px-4 py-5 text-sm text-muted">
              No resume yet. Your uploads appear here so you can re-run or reopen an analysis.
            </p>
          ) : null}
          {resumes && resumes.length > 0 ? (
            <ul className="mt-3 divide-y divide-line rounded-2xl border border-line bg-foam shadow-card">
              {resumes.map((item) => {
                const isBusy = busy?.resumeId === item.id
                return (
                  <li key={item.id} className="px-4 py-3">
                    <p className="truncate text-sm font-medium" title={item.original_filename}>
                      {item.original_filename}
                    </p>
                    <p className="mt-0.5 text-xs text-muted">
                      {formatDate(item.created_at)} · {sizeLabel(item.file_size_bytes)}
                    </p>
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      {item.latest_analysis ? (
                        <Badge className="border-line bg-paper text-ink">
                          {item.latest_analysis.target_role} · {Math.round(item.latest_analysis.ats_score)}
                        </Badge>
                      ) : (
                        <Badge className="border-gold/30 bg-gold/10 text-gold">Not analyzed</Badge>
                      )}
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {item.latest_analysis ? (
                        <Button
                          variant="secondary"
                          className="px-3 py-1.5 text-xs"
                          pending={isBusy && busy?.kind === "open"}
                          pendingLabel="Opening…"
                          disabled={working}
                          onClick={() => openAnalysis(item)}
                        >
                          View analysis
                        </Button>
                      ) : null}
                      <Button
                        variant={item.latest_analysis ? "secondary" : "primary"}
                        className="px-3 py-1.5 text-xs"
                        pending={isBusy && busy?.kind === "analyze"}
                        pendingLabel="Analyzing…"
                        disabled={working}
                        onClick={() => analyzeExisting(item)}
                      >
                        {item.latest_analysis ? "Re-analyze" : "Analyze"}
                      </Button>
                    </div>
                  </li>
                )
              })}
            </ul>
          ) : null}
        </aside>
      </div>

      {analysis ? (
        <section ref={resultRef} className="mt-10 scroll-mt-6 rounded-2xl border border-line bg-foam shadow-card p-5 sm:p-6">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="text-xs font-semibold tracking-wider text-muted uppercase">Analysis</p>
              <h2 className="mt-1 font-serif text-3xl">{analysis.target_role}</h2>
              <p className="mt-1 text-xs text-muted">Saved {formatDate(analysis.created_at)}</p>
            </div>
            <Button variant="secondary" pending={downloading} pendingLabel="Preparing PDF…" onClick={downloadReport}>
              Download PDF report
            </Button>
          </div>
          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            <ScoreBar label="ATS-style score" value={analysis.ats_score} />
            <ScoreBar label="Skill match" value={analysis.skill_match_percentage} />
          </div>
          <p className="mt-3 text-xs leading-relaxed text-muted">
            The ATS-style score checks contact details, headings, length, and bullets, then subtracts points for
            formatting issues. It is not a commercial ATS score. Skill match is the overlap between skills in the resume
            and skills requested by the job description.
          </p>
          <div className="mt-2 grid gap-x-8 md:grid-cols-2">
            <ResultList title="Missing skills" items={analysis.missing_skills} empty="No missing skills were found." />
            <ResultList title="Suggestions" items={analysis.suggestions} empty="No suggestions were returned." />
            <ResultList title="Skills found" items={analysis.skills} empty="No skills were extracted." />
            <ResultList title="Formatting issues" items={analysis.formatting_issues} empty="No formatting issues were reported." />
            <ResultList title="Education" items={analysis.education} empty="No education entries were extracted." />
            <ResultList title="Projects" items={analysis.projects} empty="No projects were extracted." />
            <ResultList title="Experience" items={analysis.experience} empty="No experience was extracted." />
            <ResultList title="Certifications" items={analysis.certifications} empty="No certifications were extracted." />
          </div>
        </section>
      ) : resumes && resumes.length === 0 ? (
        <div className="mt-10">
          <EmptyState
            title="Your analysis will appear here"
            body="Upload a resume above. You will see the ATS-style score, skill match, missing skills, and suggestions, and you can download it as a PDF."
          />
        </div>
      ) : null}
    </div>
  )
}

function ResultList({ title, items, empty }: { title: string; items: string[]; empty: string }) {
  return (
    <div className="mt-6">
      <h3 className="font-medium">{title}</h3>
      {items.length === 0 ? <p className="mt-1 text-sm text-muted">{empty}</p> : null}
      {items.length > 0 ? (
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-relaxed">
          {items.map((item, index) => (
            <li key={`${index}-${item}`}>{item}</li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}
