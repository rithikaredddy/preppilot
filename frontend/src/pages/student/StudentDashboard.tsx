import { useEffect, useMemo, useState } from "react"
import { Link } from "react-router"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { Alert, Button, EmptyState, PageHeader, Skeleton } from "../../components/ui"
import { useAuth } from "../../context/auth"
import { formatDate, formatShortDate } from "../../lib/format"
import { ApiError, api, downloadAuthenticated } from "../../services/api"
import type { Analytics, ReadinessView, ScoreCard } from "../../types"

const navy = "#1a3348"
const clay = "#8c3d32"
const pine = "#1f6b4a"
const amber = "#b7791f"

const quickStart = [
  {
    to: "/app/coding",
    title: "Solve a coding problem",
    body: "Runs on the server right away. A submission adds your first coding score.",
  },
  {
    to: "/app/resume",
    title: "Analyze your resume",
    body: "Get an ATS-style score, matched skills, and suggestions for a role.",
  },
  {
    to: "/app/interview/hr",
    title: "Practice an HR round",
    body: "Answer a few questions by typing or speaking and get feedback on each one.",
  },
  {
    to: "/app/companies",
    title: "Browse company questions",
    body: "See what recruiters commonly ask, grouped by HR, technical, and coding.",
  },
]

export function StudentDashboard() {
  const { user } = useAuth()
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [readiness, setReadiness] = useState<ReadinessView | null>(null)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(true)
  const [reportError, setReportError] = useState("")
  const [downloading, setDownloading] = useState(false)
  const [hypothetical, setHypothetical] = useState<number | null>(null)
  const [sliders, setSliders] = useState({
    resume_ats: 50,
    interview_score: 50,
    coding_score: 50,
    communication_score: 50,
  })

  useEffect(() => {
    Promise.all([api<Analytics>("/api/v1/dashboard/analytics"), api<ReadinessView>("/api/v1/readiness")])
      .then(([nextAnalytics, nextReadiness]) => {
        setAnalytics(nextAnalytics)
        setReadiness(nextReadiness)
        const inputs = nextReadiness.current?.inputs
        if (inputs) {
          setSliders({
            resume_ats: inputs.resume_ats ?? 50,
            interview_score: inputs.interview_score ?? 50,
            coding_score: inputs.coding_score ?? 50,
            communication_score: inputs.communication_score ?? 50,
          })
        }
      })
      .catch((caught) =>
        setError(caught instanceof ApiError ? caught.message : "The dashboard could not be loaded."),
      )
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!readiness?.current) return
    const handle = window.setTimeout(() => {
      api<{ readiness_percentage: number }>("/api/v1/readiness/what-if", {
        method: "POST",
        body: JSON.stringify(sliders),
      })
        .then((result) => setHypothetical(result.readiness_percentage))
        .catch(() => setHypothetical(null))
    }, 280)
    return () => window.clearTimeout(handle)
  }, [sliders, readiness])

  const measured = analytics?.scores.filter((item) => item.score !== null) ?? []
  const lineData = useMemo(() => {
    const points = analytics?.timeline ?? []
    return points.map((point, index) => ({
      name: formatShortDate(point.recorded_at) || `${index + 1}`,
      score: Math.round(point.score),
      label: point.label,
    }))
  }, [analytics])

  async function downloadReport() {
    setDownloading(true)
    setReportError("")
    try {
      await downloadAuthenticated("/api/v1/reports/performance", "placement-report.pdf")
    } catch (caught) {
      setReportError(caught instanceof ApiError ? caught.message : "The report could not be downloaded.")
    } finally {
      setDownloading(false)
    }
  }

  const strongWeak = analytics
    ? [
        { name: "Strong", value: analytics.strong_areas.length, fill: pine },
        { name: "Weak", value: analytics.weak_areas.length, fill: clay },
      ].filter((item) => item.value > 0)
    : []
  const firstName = user?.full_name?.split(/\s+/)[0] ?? "there"
  const profileLine = [user?.roll_number, user?.branch, user?.graduation_year ? `Class of ${user.graduation_year}` : null]
    .filter(Boolean)
    .join(" · ")

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader
        kicker="Student overview"
        title={`Hello, ${firstName}`}
        body={profileLine || "Complete your profile so the placement office sees the right details."}
        actions={
          measured.length > 0 ? (
            <Button variant="secondary" pending={downloading} pendingLabel="Preparing PDF…" onClick={downloadReport}>
              Download PDF report
            </Button>
          ) : null
        }
      />
      {error ? (
        <div className="mt-6">
          <Alert>{error}</Alert>
        </div>
      ) : null}
      {loading ? <DashboardSkeleton /> : null}
      {!loading && analytics && measured.length === 0 ? (
        <div className="mt-8">
          <EmptyState
            title="Let's get your first score"
            body="Your dashboard fills in after any activity below. Every chart here uses your own saved results, never sample data."
          />
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {quickStart.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className="group rounded-lg border border-line bg-foam p-4 transition hover:-translate-y-0.5 hover:border-navy/40"
              >
                <p className="font-medium group-hover:text-navy">{item.title} →</p>
                <p className="mt-1 text-sm leading-relaxed text-muted">{item.body}</p>
              </Link>
            ))}
          </div>
        </div>
      ) : null}
      {!loading && analytics && measured.length > 0 ? (
        <>
          <section className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {analytics.scores.map((item) => (
              <ScoreTile key={item.category} item={item} />
            ))}
            <article className="rounded-lg border border-navy/20 bg-navy p-4 text-foam">
              <p className="text-sm text-foam/70">Placement readiness</p>
              <p className="mt-2 font-serif text-4xl">
                {readiness?.current ? `${Math.round(readiness.current.readiness_percentage)}%` : "—"}
              </p>
              <p className="mt-2 text-sm leading-relaxed text-foam/80">
                {readiness?.current?.headline ?? "Finish one more activity to estimate readiness."}
              </p>
            </article>
          </section>

          <section className="mt-6 grid gap-4 lg:grid-cols-[1.4fr_0.8fr]">
            <article className="rounded-lg border border-line bg-foam p-4">
              <h2 className="font-serif text-2xl">Scores over time</h2>
              {lineData.length === 0 ? (
                <p className="mt-4 text-sm text-muted">Scores will plot here after your first saved activity.</p>
              ) : (
                <div className="mt-4 h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={lineData}>
                      <CartesianGrid stroke="#e3dbcd" vertical={false} />
                      <XAxis dataKey="name" tick={{ fill: "#5f584e", fontSize: 12 }} minTickGap={16} />
                      <YAxis domain={[0, 100]} tick={{ fill: "#5f584e", fontSize: 12 }} width={32} />
                      <Tooltip
                        formatter={(value) => [value, "Score"]}
                        labelFormatter={(label, payload) => {
                          const item = payload?.[0]?.payload as { label?: string } | undefined
                          return item?.label ? `${label} · ${item.label}` : String(label)
                        }}
                      />
                      <Line type="monotone" dataKey="score" stroke={navy} strokeWidth={2} dot={{ r: 3 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </article>
            <article className="rounded-lg border border-line bg-foam p-4">
              <h2 className="font-serif text-2xl">Strong and weak</h2>
              {strongWeak.length === 0 ? (
                <p className="mt-4 text-sm text-muted">Areas appear once a score is 75 or above, or below 60.</p>
              ) : (
                <>
                  <div className="mt-2 h-52">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={strongWeak} dataKey="value" nameKey="name" innerRadius={48} outerRadius={80}>
                          {strongWeak.map((item) => (
                            <Cell key={item.name} fill={item.fill} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <ul className="flex justify-center gap-4 text-sm">
                    {strongWeak.map((item) => (
                      <li key={item.name} className="flex items-center gap-1.5">
                        <span className="h-2.5 w-2.5 rounded-full" style={{ background: item.fill }} aria-hidden="true" />
                        {item.name}: {item.value}
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </article>
          </section>

          <section className="mt-4 rounded-lg border border-line bg-foam p-4">
            <h2 className="font-serif text-2xl">Category breakdown</h2>
            <div className="mt-4 h-64 overflow-x-auto">
              <div className="h-full min-w-[28rem]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analytics.scores.map((item) => ({ name: item.label, score: Math.round(item.score ?? 0) }))}>
                    <CartesianGrid stroke="#e3dbcd" vertical={false} />
                    <XAxis dataKey="name" tick={{ fill: "#5f584e", fontSize: 12 }} interval={0} />
                    <YAxis domain={[0, 100]} tick={{ fill: "#5f584e", fontSize: 12 }} width={32} />
                    <Tooltip formatter={(value) => [value, "Score"]} />
                    <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                      {analytics.scores.map((item) => (
                        <Cell
                          key={item.category}
                          fill={item.score === null ? "#e3dbcd" : item.score >= 75 ? pine : item.score < 60 ? amber : navy}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>

          <section className="mt-4 grid gap-4 md:grid-cols-2">
            <AreaList title="Weak areas" empty="Nothing is below 60 yet." items={analytics.weak_areas} />
            <AreaList title="Strong areas" empty="Nothing is at 75 or above yet." items={analytics.strong_areas} />
          </section>

          <section className="mt-4 rounded-lg border border-line bg-foam p-5">
            <div className="flex flex-wrap items-end justify-between gap-3">
              <div>
                <h2 className="font-serif text-2xl">What if you improve?</h2>
                <p className="mt-1 max-w-xl text-sm text-muted">
                  Drag a score. The number on the right is a fresh estimate and is not saved to your trend.
                </p>
              </div>
              <p className="font-serif text-4xl text-navy">
                {hypothetical === null ? "…" : `${Math.round(hypothetical)}%`}
              </p>
            </div>
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              {(
                [
                  ["resume_ats", "Resume"],
                  ["interview_score", "Interview"],
                  ["coding_score", "Coding"],
                  ["communication_score", "Communication"],
                ] as const
              ).map(([key, label]) => (
                <label key={key} className="text-sm">
                  <span className="mb-1 flex justify-between font-medium">
                    {label}
                    <span>{Math.round(sliders[key])}</span>
                  </span>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={sliders[key]}
                    onChange={(event) =>
                      setSliders((current) => ({ ...current, [key]: Number(event.target.value) }))
                    }
                    className="w-full accent-navy"
                  />
                </label>
              ))}
            </div>
          </section>

          <section className="mt-4 flex flex-wrap items-center justify-between gap-4 rounded-lg border border-line bg-foam p-5">
            <div>
              <h2 className="font-serif text-2xl">Preparation gap</h2>
              <p className="mt-1 text-sm text-muted">
                {analytics.gap.total_items === 0
                  ? "Generate a roadmap from your weak areas. Checking items off lowers this gap."
                  : `${analytics.gap.completed_items} of ${analytics.gap.total_items} roadmap items done.`}
              </p>
              <p className="mt-3 font-serif text-3xl">{Math.round(analytics.gap.remaining_gap)}</p>
            </div>
            <Link to="/app/roadmap" className="rounded-md bg-navy px-4 py-2.5 text-sm font-semibold text-foam hover:bg-navy-soft">
              Open roadmap
            </Link>
          </section>
          {reportError ? (
            <div className="mt-3">
              <Alert>{reportError}</Alert>
            </div>
          ) : null}
          {readiness && readiness.history.length > 1 ? (
            <section className="mt-4 rounded-lg border border-line bg-foam p-4">
              <h2 className="font-serif text-2xl">Readiness trend</h2>
              <div className="mt-4 h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={readiness.history.map((point, index) => ({
                      name: formatShortDate(point.created_at) || `${index + 1}`,
                      readiness: Math.round(point.readiness_percentage),
                      date: formatDate(point.created_at),
                    }))}
                  >
                    <CartesianGrid stroke="#e3dbcd" vertical={false} />
                    <XAxis dataKey="name" tick={{ fill: "#5f584e", fontSize: 12 }} minTickGap={16} />
                    <YAxis domain={[0, 100]} tick={{ fill: "#5f584e", fontSize: 12 }} width={32} />
                    <Tooltip formatter={(value) => [`${value}%`, "Readiness"]} />
                    <Line type="monotone" dataKey="readiness" stroke={pine} strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </section>
          ) : null}
        </>
      ) : null}
    </div>
  )
}

function ScoreTile({ item }: { item: ScoreCard }) {
  const tone =
    item.score === null ? "text-muted" : item.score >= 75 ? "text-pine" : item.score < 60 ? "text-clay" : "text-ink"
  const note =
    item.score === null ? "No score yet" : item.score >= 75 ? "Strong" : item.score < 60 ? "Needs work" : "On track"
  return (
    <article className="rounded-lg border border-line bg-foam p-4">
      <p className="text-sm text-muted">{item.label}</p>
      <p className={`mt-2 font-serif text-3xl ${tone}`}>{item.score === null ? "—" : Math.round(item.score)}</p>
      <p className="mt-1 text-xs text-muted">{note}</p>
    </article>
  )
}

function AreaList({ title, empty, items }: { title: string; empty: string; items: ScoreCard[] }) {
  return (
    <article className="rounded-lg border border-line bg-foam p-4">
      <h2 className="font-serif text-2xl">{title}</h2>
      {items.length === 0 ? <p className="mt-3 text-sm text-muted">{empty}</p> : null}
      <ul className="mt-3 space-y-2">
        {items.map((item) => (
          <li key={item.category} className="flex justify-between text-sm">
            <span>{item.label}</span>
            <span className="font-medium">{item.score === null ? "—" : Math.round(item.score)}</span>
          </li>
        ))}
      </ul>
    </article>
  )
}

function DashboardSkeleton() {
  return (
    <div className="mt-8 grid gap-3 sm:grid-cols-3" role="status" aria-label="Loading your dashboard">
      {Array.from({ length: 6 }, (_, index) => (
        <Skeleton key={index} className="h-28" />
      ))}
    </div>
  )
}
