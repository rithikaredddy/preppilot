import CodeMirror, { type Extension } from "@uiw/react-codemirror"
import { useEffect, useMemo, useRef, useState } from "react"
import { Link, useSearchParams } from "react-router"
import { Alert, Badge, Button, EmptyState, LoadingLine, PageHeader, Skeleton } from "../../components/ui"
import { readStorage, statusLabel, statusTone, writeStorage } from "../../lib/format"
import { ApiError, api } from "../../services/api"
import type { CodingProblem, CodingProblemSummary, Company, RunResult, Submission } from "../../types"

// Each grammar is downloaded only when its language is first selected.
const languages = {
  python: {
    label: "Python 3",
    file: "solution.py",
    load: () => import("@codemirror/lang-python").then((module) => module.python()),
  },
  java: { label: "Java", file: "Main.java", load: () => import("@codemirror/lang-java").then((module) => module.java()) },
  cpp: { label: "C++", file: "solution.cpp", load: () => import("@codemirror/lang-cpp").then((module) => module.cpp()) },
} as const

type Language = keyof typeof languages

const difficultyTone: Record<string, string> = {
  easy: "text-pine",
  beginner: "text-pine",
  medium: "text-navy",
  intermediate: "text-navy",
  hard: "text-clay",
  advanced: "text-clay",
}

function draftKey(problemId: string, language: Language) {
  return `coding-draft:${problemId}:${language}`
}

function initialCode(problem: CodingProblem, language: Language) {
  return readStorage(draftKey(problem.id, language)) ?? problem.starter_code[language] ?? ""
}

export function CodingPage() {
  const [params, setParams] = useSearchParams()
  const companyFilter = params.get("company") ?? "all"
  const [problems, setProblems] = useState<CodingProblemSummary[] | null>(null)
  const [companies, setCompanies] = useState<Company[]>([])
  const [selectedId, setSelectedId] = useState("")
  const [problem, setProblem] = useState<CodingProblem | null>(null)
  const [language, setLanguage] = useState<Language>("python")
  const languageRef = useRef<Language>("python")
  const [code, setCode] = useState("")
  const [runResult, setRunResult] = useState<{ problemId: string; data: RunResult } | null>(null)
  const [submission, setSubmission] = useState<{ problemId: string; data: Submission } | null>(null)
  const [error, setError] = useState("")
  const [running, setRunning] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [activeCase, setActiveCase] = useState(0)
  const [grammar, setGrammar] = useState<{ language: Language; extension: Extension } | null>(null)

  useEffect(() => {
    let cancelled = false
    languages[language]
      .load()
      .then((extension) => {
        if (!cancelled) setGrammar({ language, extension })
      })
      .catch(() => {
        // Without the grammar the editor still works, just without highlighting.
      })
    return () => {
      cancelled = true
    }
  }, [language])

  useEffect(() => {
    Promise.all([
      api<{ items: CodingProblemSummary[] }>("/api/v1/coding/problems"),
      api<{ items: Company[] }>("/api/v1/companies"),
    ])
      .then(([problemList, companyList]) => {
        setProblems(problemList.items)
        setCompanies(companyList.items)
      })
      .catch(() => setError("The problem list could not be loaded."))
  }, [])

  const visible = useMemo(() => {
    const items = problems ?? []
    if (companyFilter === "all") return items
    return items.filter((item) => item.company_slug === companyFilter)
  }, [problems, companyFilter])

  // The selected problem falls back to the first visible one when the filter hides it.
  const activeId = visible.some((item) => item.id === selectedId) ? selectedId : (visible[0]?.id ?? "")

  useEffect(() => {
    if (!activeId) return
    let cancelled = false
    api<CodingProblem>(`/api/v1/coding/problems/${activeId}`)
      .then((detail) => {
        if (cancelled) return
        setProblem(detail)
        setCode(initialCode(detail, languageRef.current))
      })
      .catch(() => {
        if (!cancelled) setError("That problem could not be loaded.")
      })
    return () => {
      cancelled = true
    }
  }, [activeId])

  const current = problem && problem.id === activeId ? problem : null
  const run = runResult && current && runResult.problemId === current.id ? runResult.data : null
  const submitted = submission && current && submission.problemId === current.id ? submission.data : null

  function chooseCompany(slug: string) {
    const next = new URLSearchParams(params)
    if (slug === "all") next.delete("company")
    else next.set("company", slug)
    setParams(next)
  }

  function chooseProblem(id: string) {
    setSelectedId(id)
    setActiveCase(0)
    setError("")
  }

  function changeLanguage(next: Language) {
    languageRef.current = next
    setLanguage(next)
    if (current) setCode(initialCode(current, next))
    setRunResult(null)
    setSubmission(null)
  }

  function editCode(value: string) {
    setCode(value)
    if (current) writeStorage(draftKey(current.id, language), value)
  }

  function resetCode() {
    if (!current) return
    if (!window.confirm("Replace your code with the starter template? Your current draft for this language will be lost.")) {
      return
    }
    writeStorage(draftKey(current.id, language), null)
    setCode(current.starter_code[language] ?? "")
  }

  async function runCode() {
    if (!current) return
    setRunning(true)
    setError("")
    try {
      const result = await api<RunResult>(`/api/v1/coding/problems/${current.id}/run`, {
        method: "POST",
        body: JSON.stringify({ language, source_code: code }),
      })
      setRunResult({ problemId: current.id, data: result })
      setActiveCase(0)
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "The program could not be run.")
    } finally {
      setRunning(false)
    }
  }

  async function submitCode() {
    if (!current) return
    setSubmitting(true)
    setError("")
    try {
      const result = await api<Submission>(`/api/v1/coding/problems/${current.id}/submit`, {
        method: "POST",
        body: JSON.stringify({ language, source_code: code }),
      })
      setSubmission({ problemId: current.id, data: result })
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "The submission could not be saved.")
    } finally {
      setSubmitting(false)
    }
  }

  const extensions = useMemo(
    () => (grammar && grammar.language === language ? [grammar.extension] : []),
    [grammar, language],
  )
  const shownCases = run?.results ?? []
  const currentCase = shownCases[activeCase]
  const busy = running || submitting

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader
        kicker="Coding assessment"
        title="Practice"
        body="Pick a company, then one of its coding questions. Write a solution in Python, Java, or C++, run it against the examples, and submit to run the hidden tests and get an AI code review."
      />

      <div className="mt-5 flex gap-2 overflow-x-auto pb-1" role="group" aria-label="Filter by company">
        <FilterChip active={companyFilter === "all"} onClick={() => chooseCompany("all")} label="All companies" />
        {companies.map((company) => (
          <FilterChip
            key={company.slug}
            active={companyFilter === company.slug}
            onClick={() => chooseCompany(company.slug)}
            label={company.name}
          />
        ))}
      </div>

      {error ? (
        <div className="mt-4">
          <Alert>{error}</Alert>
        </div>
      ) : null}

      {visible.length > 0 ? (
        <label className="mt-4 block text-sm lg:hidden" htmlFor="problem-select">
          <span className="mb-1.5 block font-medium">Problem</span>
          <select
            id="problem-select"
            value={activeId}
            onChange={(event) => chooseProblem(event.target.value)}
            className="w-full rounded-md border border-line bg-foam px-3 py-2.5"
          >
            {visible.map((item, index) => (
              <option key={item.id} value={item.id}>
                {index + 1}. {item.title} ({item.difficulty})
              </option>
            ))}
          </select>
        </label>
      ) : null}

      <div className="mt-4 grid items-start gap-4 lg:grid-cols-[17rem_minmax(0,1fr)]">
        <nav
          aria-label="Problems"
          className="hidden max-h-[44rem] space-y-1 overflow-y-auto rounded-xl border border-line bg-foam p-2 lg:sticky lg:top-6 lg:block"
        >
          {problems === null ? (
            <div className="space-y-2 p-1">
              <Skeleton className="h-14" />
              <Skeleton className="h-14" />
              <Skeleton className="h-14" />
            </div>
          ) : null}
          {problems && visible.length === 0 ? (
            <p className="px-3 py-6 text-sm text-muted">No coding questions are loaded for this company yet.</p>
          ) : null}
          {visible.map((item, index) => {
            const active = item.id === activeId
            return (
              <button
                key={item.id}
                type="button"
                aria-current={active ? "true" : undefined}
                onClick={() => chooseProblem(item.id)}
                className={`block w-full rounded-lg px-3 py-2.5 text-left transition ${active ? "bg-navy text-foam" : "hover:bg-paper"}`}
              >
                <span className="text-xs opacity-70">{index + 1}.</span>
                <span className="mt-0.5 block text-sm font-medium">{item.title}</span>
                <span
                  className={`mt-1 block text-xs capitalize ${active ? "text-foam/80" : (difficultyTone[item.difficulty] ?? "text-muted")}`}
                >
                  {item.difficulty}
                  {item.company_name ? ` · ${item.company_name}` : ""}
                </span>
              </button>
            )
          })}
        </nav>

        {current ? (
          <section className="min-w-0 space-y-3">
            <article className="rounded-xl border border-line bg-foam p-4 sm:p-5">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="mr-1 font-serif text-2xl sm:text-3xl">{current.title}</h2>
                <span
                  className={`rounded-full bg-paper px-2.5 py-1 text-xs font-semibold capitalize ${difficultyTone[current.difficulty] ?? "text-muted"}`}
                >
                  {current.difficulty}
                </span>
                {current.company_name ? (
                  <Link
                    to={`/app/companies/${current.company_slug}`}
                    className="rounded-full bg-paper px-2.5 py-1 text-xs font-medium text-navy hover:underline"
                  >
                    {current.company_name}
                  </Link>
                ) : null}
                <span className="rounded-full bg-paper px-2.5 py-1 text-xs text-muted">{current.topic}</span>
              </div>
              <p className="mt-4 text-sm leading-7 whitespace-pre-wrap">{current.statement}</p>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                {current.public_tests.map((test, index) => (
                  <div key={test.id} className="rounded-lg bg-paper px-3 py-2 text-sm">
                    <p className="font-medium">Example {index + 1}</p>
                    <p className="mt-1 font-mono text-xs whitespace-pre-wrap text-muted">Input: {test.stdin || "(empty)"}</p>
                    <p className="font-mono text-xs whitespace-pre-wrap text-muted">Output: {test.expected_stdout}</p>
                  </div>
                ))}
              </div>
              <p className="mt-3 text-xs text-muted">
                {current.hidden_test_count} hidden test{current.hidden_test_count === 1 ? "" : "s"} run on submit · time
                limit {current.time_limit_ms} ms
              </p>
            </article>

            <div className="overflow-hidden rounded-xl border border-line bg-white">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-3 py-2 text-xs font-medium text-muted">
                <span className="font-mono">{languages[language].file}</span>
                <div className="flex items-center gap-2">
                  <button type="button" onClick={resetCode} className="rounded px-2 py-1 hover:bg-paper hover:text-ink">
                    Reset
                  </button>
                  <label className="flex items-center gap-1.5" htmlFor="language">
                    <span className="sr-only">Language</span>
                    <select
                      id="language"
                      value={language}
                      onChange={(event) => changeLanguage(event.target.value as Language)}
                      className="rounded-md border border-line bg-paper px-2 py-1 text-xs text-ink"
                    >
                      {(Object.keys(languages) as Language[]).map((value) => (
                        <option key={value} value={value}>
                          {languages[value].label}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
              </div>
              <CodeMirror
                value={code}
                height="320px"
                extensions={extensions}
                onChange={editCode}
                basicSetup={{ lineNumbers: true }}
                aria-label={`Code editor, ${languages[language].label}`}
              />
              <p className="border-t border-line px-3 py-1.5 text-xs text-muted">
                Your draft is kept in this browser for each problem and language.
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button variant="secondary" pending={running} pendingLabel="Running…" disabled={busy} onClick={runCode}>
                Run examples
              </Button>
              <Button pending={submitting} pendingLabel="Submitting…" disabled={busy} onClick={submitCode}>
                Submit
              </Button>
            </div>

            {running ? <LoadingLine label="Running your code against the examples…" /> : null}
            {submitting ? (
              <LoadingLine
                label="Running hidden tests and asking the AI reviewer…"
                detail="The review usually takes 5 to 20 seconds."
              />
            ) : null}

            {shownCases.length > 0 && run ? (
              <article className="rounded-xl border border-line bg-foam p-4" aria-live="polite">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3 className="font-serif text-xl">
                    Examples · {run.passed_count}/{run.total_count} passed
                  </h3>
                  <div className="flex flex-wrap gap-1" role="tablist" aria-label="Test cases">
                    {shownCases.map((item, index) => (
                      <button
                        key={`${item.stdin}-${index}`}
                        type="button"
                        role="tab"
                        aria-selected={index === activeCase}
                        onClick={() => setActiveCase(index)}
                        className={`rounded-md px-2.5 py-1 text-xs font-semibold ${
                          index === activeCase
                            ? "bg-navy text-foam"
                            : item.passed
                              ? "bg-pine/10 text-pine"
                              : "bg-clay/10 text-clay"
                        }`}
                      >
                        {item.passed ? "✓" : "✗"} Case {index + 1}
                      </button>
                    ))}
                  </div>
                </div>
                {currentCase ? (
                  <div className="mt-3 space-y-2 text-sm">
                    <Badge className={statusTone(currentCase.passed ? "accepted" : currentCase.status)}>
                      {currentCase.passed ? "Accepted" : statusLabel(currentCase.status)}
                    </Badge>
                    <div className="grid gap-2 md:grid-cols-3">
                      <OutputBlock title="Input" value={currentCase.stdin || "(empty)"} />
                      <OutputBlock title="Expected" value={currentCase.expected_stdout} />
                      <OutputBlock title="Your output" value={currentCase.stdout || "(empty)"} />
                    </div>
                    {currentCase.stderr ? (
                      <pre className="overflow-x-auto rounded-lg bg-clay/10 p-3 font-mono text-xs whitespace-pre-wrap text-clay">
                        {currentCase.stderr}
                      </pre>
                    ) : null}
                  </div>
                ) : null}
              </article>
            ) : null}

            {submitted ? <SubmissionCard submission={submitted} /> : null}
          </section>
        ) : problems && visible.length === 0 ? (
          <EmptyState title="No coding questions yet" body="Choose another company. Each company lists its own coding tasks here." />
        ) : (
          <div className="space-y-3">
            <Skeleton className="h-56" />
            <Skeleton className="h-80" />
          </div>
        )}
      </div>
    </div>
  )
}

function OutputBlock({ title, value }: { title: string; value: string }) {
  return (
    <div className="min-w-0 rounded-lg bg-paper p-3">
      <p className="text-xs font-semibold text-muted">{title}</p>
      <pre className="mt-1 overflow-x-auto font-mono text-xs whitespace-pre-wrap">{value}</pre>
    </div>
  )
}

function SubmissionCard({ submission }: { submission: Submission }) {
  const results = submission.results ?? []
  return (
    <article className="rounded-xl border border-line bg-foam p-4" aria-live="polite">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-serif text-xl">Submission result</h3>
        <Badge className={statusTone(submission.status)}>{statusLabel(submission.status)}</Badge>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
        <Stat label="Tests passed" value={`${submission.passed_count}/${submission.total_count}`} />
        <Stat label="Score" value={`${Math.round(submission.score)}`} />
      </div>
      {results.length > 0 ? (
        <ul className="mt-4 flex flex-wrap gap-1.5" aria-label="Test results">
          {results.map((item, index) => {
            const number = results.slice(0, index + 1).filter((row) => row.is_hidden === item.is_hidden).length
            return (
              <li
                key={index}
                className={`rounded-md px-2 py-1 text-xs font-medium ${item.passed ? "bg-pine/10 text-pine" : "bg-clay/10 text-clay"}`}
                title={statusLabel(item.passed ? "accepted" : item.status)}
              >
                {item.passed ? "✓" : "✗"} {item.is_hidden ? `Hidden ${number}` : `Example ${number}`}
                {item.passed ? "" : ` · ${statusLabel(item.status)}`}
              </li>
            )
          })}
        </ul>
      ) : null}
      {submission.review_error ? <p className="mt-3 text-sm text-clay">{submission.review_error}</p> : null}
      {submission.ai_review ? (
        <div className="mt-4 space-y-3 border-t border-line pt-4 text-sm leading-relaxed">
          <p className="text-xs font-semibold tracking-wider text-muted uppercase">AI code review</p>
          <p>{submission.ai_review.summary}</p>
          <div className="flex flex-wrap gap-2">
            <Badge className="border-line bg-paper text-ink">Time {submission.ai_review.time_complexity}</Badge>
            <Badge className="border-line bg-paper text-ink">Space {submission.ai_review.space_complexity}</Badge>
          </div>
          {submission.ai_review.issues.length > 0 ? (
            <div>
              <p className="font-medium">Issues</p>
              <ul className="mt-1 list-disc pl-5">
                {submission.ai_review.issues.map((line, index) => (
                  <li key={`${index}-${line}`}>{line}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {submission.ai_review.suggestions.length > 0 ? (
            <div>
              <p className="font-medium">Suggestions</p>
              <ul className="mt-1 list-disc pl-5">
                {submission.ai_review.suggestions.map((line, index) => (
                  <li key={`${index}-${line}`}>{line}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </article>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-paper px-3 py-2">
      <p className="text-xs text-muted">{label}</p>
      <p className="font-serif text-2xl">{value}</p>
    </div>
  )
}

function FilterChip({ active, label, onClick }: { active: boolean; label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={`shrink-0 rounded-full px-3 py-1.5 text-sm font-medium transition ${
        active ? "bg-navy text-foam" : "border border-line bg-foam text-ink hover:bg-paper"
      }`}
    >
      {label}
    </button>
  )
}
