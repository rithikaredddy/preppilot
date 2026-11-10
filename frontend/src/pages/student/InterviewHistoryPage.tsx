import { useEffect, useState } from "react"
import { Link } from "react-router"
import { Alert, Badge, Button, EmptyState, PageHeader, Skeleton } from "../../components/ui"
import { formatDateTime, statusLabel, statusTone } from "../../lib/format"
import { api } from "../../services/api"
import type { InterviewSession, Submission } from "../../types"

type SubmissionRow = Submission & { language: string; created_at: string }

const PAGE_SIZE = 10

export function InterviewHistoryPage() {
  const [tab, setTab] = useState<"interviews" | "coding">("interviews")

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        kicker="History"
        title="Your practice record"
        body="Every finished interview keeps its questions, your answers, the turn scores, and the overall result. Coding submissions keep the test results and the AI review."
      />
      <div className="mt-6 inline-flex rounded-2xl border border-line bg-foam shadow-card p-1" role="tablist" aria-label="History type">
        {(
          [
            ["interviews", "Interviews"],
            ["coding", "Coding submissions"],
          ] as const
        ).map(([value, label]) => (
          <button
            key={value}
            type="button"
            role="tab"
            aria-selected={tab === value}
            onClick={() => setTab(value)}
            className={`rounded-xl px-4 py-1.5 text-sm font-medium transition ${tab === value ? "bg-navy text-onbrand" : "text-ink hover:bg-paper"}`}
          >
            {label}
          </button>
        ))}
      </div>
      <div className="mt-4">{tab === "interviews" ? <InterviewHistory /> : <CodingHistory />}</div>
    </div>
  )
}

function usePaged<T>(path: string) {
  const [items, setItems] = useState<T[] | null>(null)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [error, setError] = useState("")
  const [loadingMore, setLoadingMore] = useState(false)

  useEffect(() => {
    let cancelled = false
    api<{ items: T[]; total: number }>(`${path}?page=1&page_size=${PAGE_SIZE}`)
      .then((result) => {
        if (cancelled) return
        setItems(result.items)
        setTotal(result.total)
      })
      .catch(() => {
        if (!cancelled) setError("Your history could not be loaded.")
      })
    return () => {
      cancelled = true
    }
  }, [path])

  async function loadMore() {
    const next = page + 1
    setLoadingMore(true)
    try {
      const result = await api<{ items: T[]; total: number }>(`${path}?page=${next}&page_size=${PAGE_SIZE}`)
      setItems((current) => [...(current ?? []), ...result.items])
      setTotal(result.total)
      setPage(next)
    } catch {
      setError("More results could not be loaded.")
    } finally {
      setLoadingMore(false)
    }
  }

  return { items, total, error, loadingMore, loadMore, hasMore: items !== null && items.length < total }
}

function LoadingRows() {
  return (
    <div className="space-y-2" role="status" aria-label="Loading">
      <Skeleton className="h-16" />
      <Skeleton className="h-16" />
      <Skeleton className="h-16" />
    </div>
  )
}

function InterviewHistory() {
  const { items, total, error, loadingMore, loadMore, hasMore } = usePaged<InterviewSession>("/api/v1/interviews")

  if (error && items === null) return <Alert>{error}</Alert>
  if (items === null) return <LoadingRows />
  if (items.length === 0) {
    return (
      <EmptyState
        title="No interviews yet"
        body="Start an HR or technical interview. The result appears here after you finish the session."
      >
        <Link to="/app/interview/hr" className="rounded-xl bg-navy px-4 py-2.5 text-sm font-semibold text-onbrand">
          Start an HR interview
        </Link>
        <Link to="/app/interview/technical" className="rounded-xl border border-line bg-foam px-4 py-2.5 text-sm font-semibold">
          Start a technical interview
        </Link>
      </EmptyState>
    )
  }

  return (
    <>
      {error ? <Alert>{error}</Alert> : null}
      <ul className="divide-y divide-line rounded-2xl border border-line bg-foam shadow-card">
        {items.map((session) => (
          <li key={session.id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
            <div className="min-w-0">
              <p className="font-medium">{session.kind === "hr" ? "HR interview" : `Technical · ${session.topic}`}</p>
              <p className="mt-0.5 text-xs text-muted">
                {formatDateTime(session.completed_at ?? session.started_at)}
                {session.difficulty ? ` · ${session.difficulty}` : ""}
                {` · ${session.answered_count} answered`}
              </p>
            </div>
            <div className="flex items-center gap-3">
              {session.status === "completed" ? (
                <ScorePill score={session.overall_score} />
              ) : (
                <Badge className="border-brand/20 bg-brand/5 text-brand">In progress</Badge>
              )}
              <Link to={`/app/interview/${session.id}`} className="text-sm font-semibold text-brand hover:underline">
                {session.status === "completed" ? "View result" : "Continue"}
              </Link>
            </div>
          </li>
        ))}
      </ul>
      <Footer shown={items.length} total={total} hasMore={hasMore} loadingMore={loadingMore} onMore={loadMore} />
    </>
  )
}

function CodingHistory() {
  const { items, total, error, loadingMore, loadMore, hasMore } = usePaged<SubmissionRow>("/api/v1/coding/submissions")

  if (error && items === null) return <Alert>{error}</Alert>
  if (items === null) return <LoadingRows />
  if (items.length === 0) {
    return (
      <EmptyState title="No submissions yet" body="Submit a solution on the coding page. Each submission is listed here with its result.">
        <Link to="/app/coding" className="rounded-xl bg-navy px-4 py-2.5 text-sm font-semibold text-onbrand">
          Open coding practice
        </Link>
      </EmptyState>
    )
  }

  return (
    <>
      {error ? <Alert>{error}</Alert> : null}
      <ul className="divide-y divide-line rounded-2xl border border-line bg-foam shadow-card">
        {items.map((item) => (
          <li key={item.id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
            <div className="min-w-0">
              <p className="font-medium">{item.problem_title}</p>
              <p className="mt-0.5 text-xs text-muted">
                {formatDateTime(item.created_at)} · {item.language === "cpp" ? "C++" : item.language === "java" ? "Java" : "Python"}
                {` · ${item.passed_count}/${item.total_count} tests`}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Badge className={statusTone(item.status)}>{statusLabel(item.status)}</Badge>
              <ScorePill score={item.score} />
            </div>
          </li>
        ))}
      </ul>
      <Footer shown={items.length} total={total} hasMore={hasMore} loadingMore={loadingMore} onMore={loadMore} />
    </>
  )
}

function ScorePill({ score }: { score: number | null }) {
  if (score === null) return <span className="text-sm text-muted">—</span>
  const tone = score >= 75 ? "text-pine" : score < 60 ? "text-clay" : "text-ink"
  return <span className={`font-serif text-2xl ${tone}`}>{Math.round(score)}</span>
}

function Footer({
  shown,
  total,
  hasMore,
  loadingMore,
  onMore,
}: {
  shown: number
  total: number
  hasMore: boolean
  loadingMore: boolean
  onMore: () => void
}) {
  return (
    <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-sm text-muted">
      <p>
        Showing {shown} of {total}
      </p>
      {hasMore ? (
        <Button variant="secondary" pending={loadingMore} pendingLabel="Loading…" onClick={onMore}>
          Load more
        </Button>
      ) : null}
    </div>
  )
}
