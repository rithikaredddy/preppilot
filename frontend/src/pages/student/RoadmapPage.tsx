import { useEffect, useState } from "react"
import { Link } from "react-router"
import { Alert, Button, EmptyState, LoadingLine, Notice, PageHeader, Skeleton } from "../../components/ui"
import { errorMessage } from "../../lib/format"
import { ApiError, api } from "../../services/api"
import type { RoadmapList, RoadmapItem } from "../../types"

let roadmapRequest: Promise<RoadmapList> | null = null

function loadRoadmap() {
  return api<RoadmapList>("/api/v1/roadmap").then((existing) => {
    if (existing.items.length > 0) return existing
    if (!roadmapRequest) {
      roadmapRequest = api<RoadmapList>("/api/v1/roadmap", { method: "POST" }).finally(() => {
        roadmapRequest = null
      })
    }
    return roadmapRequest
  })
}

export function RoadmapPage() {
  const [plan, setPlan] = useState<RoadmapList | null>(null)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(true)
  const [pending, setPending] = useState(false)
  const [savingId, setSavingId] = useState("")

  useEffect(() => {
    let cancelled = false
    api<RoadmapList>("/api/v1/roadmap")
      .then(async (existing) => {
        if (cancelled) return
        const daily = existing.items.some((item) => /^Day \d+$/.test(item.topic))
        if (existing.items.length > 0 && daily) {
          setPlan(existing)
          return
        }
        try {
          const created =
            existing.items.length > 0
              ? await api<RoadmapList>("/api/v1/roadmap", { method: "POST" })
              : await loadRoadmap()
          if (!cancelled) setPlan(created)
        } catch (caught) {
          if (cancelled) return
          if (caught instanceof ApiError && caught.status === 429) {
            setPlan(await api<RoadmapList>("/api/v1/roadmap"))
            return
          }
          setPlan(existing)
          if (!(caught instanceof ApiError) || caught.code !== "not_enough_activity") {
            setError(caught instanceof ApiError ? caught.message : "A roadmap could not be generated.")
          }
        }
      })
      .catch((caught) => {
        if (!cancelled) setError(caught instanceof ApiError ? caught.message : "The roadmap could not be loaded.")
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  async function generate() {
    const done = plan?.items.filter((item) => item.is_complete).length ?? 0
    if (
      plan?.items.length &&
      !window.confirm(
        done > 0
          ? `A new plan replaces the current one, and the ${done} day${done === 1 ? "" : "s"} you checked off will be cleared. Continue?`
          : "A new plan replaces the current one. Continue?",
      )
    ) {
      return
    }
    setPending(true)
    setError("")
    try {
      setPlan(await api<RoadmapList>("/api/v1/roadmap", { method: "POST" }))
    } catch (caught) {
      setError(errorMessage(caught, "A roadmap could not be generated."))
    } finally {
      setPending(false)
    }
  }

  async function toggle(item: RoadmapItem) {
    setSavingId(item.id)
    setError("")
    try {
      await api<RoadmapItem>(`/api/v1/roadmap/${item.id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_complete: !item.is_complete }),
      })
      // The server owns the gap formula, so read the plan back instead of recomputing it here.
      setPlan(await api<RoadmapList>("/api/v1/roadmap"))
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "That item could not be updated.")
    } finally {
      setSavingId("")
    }
  }

  const completed = plan?.items.filter((item) => item.is_complete).length ?? 0
  const total = plan?.items.length ?? 0

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        kicker="Roadmap"
        title="Your 7-day plan"
        body="The AI reads your resume, interview, and coding scores, then assigns one session to each day. The weakest score gets more days. Check a day off when you finish it."
        actions={
          <Button
            variant={plan?.items.length ? "secondary" : "primary"}
            pending={pending}
            pendingLabel="Building plan…"
            disabled={loading}
            onClick={generate}
          >
            {plan?.items.length ? "Generate a new plan" : "Build my 7-day plan"}
          </Button>
        }
      />
      {pending ? (
        <div className="mt-4">
          <LoadingLine label="Writing your 7-day plan…" detail="This usually takes 5 to 20 seconds." />
        </div>
      ) : null}
      {plan && total > 0 ? (
        <section className="mt-6 grid gap-3 sm:grid-cols-2">
          <div className="rounded-2xl border border-line bg-foam shadow-card p-4">
            <p className="text-sm text-muted">Progress</p>
            <p className="mt-1 font-serif text-3xl">
              {completed}/{total} days
            </p>
            <div className="mt-2 h-2 rounded-full bg-line">
              <div className="h-2 rounded-full bg-pine transition-all" style={{ width: `${(completed / total) * 100}%` }} />
            </div>
          </div>
          <div className="rounded-2xl border border-line bg-foam shadow-card p-4">
            <p className="text-sm text-muted">Preparation gap</p>
            <p className="mt-1 font-serif text-3xl">{Math.round(plan.gap.remaining_gap)}</p>
            <p className="mt-1 text-xs text-muted">
              {plan.gap.base_gap > 0
                ? `Down from ${Math.round(plan.gap.base_gap)}. Each finished day lowers it.`
                : "No gap right now: none of your scored areas is below the target."}
            </p>
          </div>
        </section>
      ) : null}
      {error ? (
        <div className="mt-4">
          <Alert>{error}</Alert>
        </div>
      ) : null}
      {plan?.note ? (
        <div className="mt-4">
          <Notice>{plan.note}</Notice>
        </div>
      ) : null}
      {loading ? (
        <div className="mt-6 space-y-3" role="status" aria-label="Loading your plan">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
      ) : null}
      {!loading && plan && plan.items.length === 0 ? (
        <div className="mt-6">
          <EmptyState
            title="No scores to plan from yet"
            body="Finish a resume review, interview, or coding problem. The roadmap is written from those scores."
          >
            <Link to="/app/coding" className="rounded-xl bg-navy px-4 py-2.5 text-sm font-semibold text-onbrand">
              Solve a coding problem
            </Link>
            <Link to="/app/resume" className="rounded-xl border border-line bg-foam px-4 py-2.5 text-sm font-semibold">
              Analyze a resume
            </Link>
          </EmptyState>
        </div>
      ) : null}
      {plan && plan.items.length > 0 ? (
        <ol className="mt-6 space-y-3">
          {plan.items.map((item) => (
            <li
              key={item.id}
              className={`rounded-xl border bg-foam p-4 transition ${item.is_complete ? "border-pine/30" : "border-line"}`}
            >
              <label className="flex cursor-pointer items-start gap-3">
                <input
                  type="checkbox"
                  className="mt-1 h-4 w-4 accent-[var(--color-navy)]"
                  checked={item.is_complete}
                  disabled={savingId === item.id}
                  onChange={() => toggle(item)}
                />
                <span className="min-w-0">
                  <span className="text-xs font-semibold tracking-wide text-brand uppercase">{item.topic}</span>
                  <span className={`mt-1 block leading-relaxed ${item.is_complete ? "text-muted line-through" : ""}`}>
                    {item.subtopic}
                  </span>
                  {item.resource_link ? (
                    <a
                      href={item.resource_link}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-2 inline-block text-sm font-medium text-brand hover:underline"
                    >
                      {item.resource_title} ↗<span className="sr-only"> (opens in a new tab)</span>
                    </a>
                  ) : null}
                </span>
              </label>
            </li>
          ))}
        </ol>
      ) : null}

    </div>
  )
}
