import { useEffect, useMemo, useState, type JSX } from "react"
import { Link } from "react-router"
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { icons } from "../../components/icons"
import { Alert, ProgressRing, Skeleton, StatTile } from "../../components/ui"
import { useChartColors } from "../../lib/theme"
import { useAuth } from "../../context/auth"
import { formatDate, formatShortDate } from "../../lib/format"
import { ApiError, api, downloadAuthenticated } from "../../services/api"
import type { Analytics, ReadinessView, ScoreCard } from "../../types"

const quickStart = [
  {
    to: "/app/resume",
    title: "Analyze your resume",
    body: "Get an ATS-style score, matched skills, and suggestions for a role.",
    icon: icons.resume,
    tint: "from-indigo-500/15 to-violet-500/10 text-brand",
  },
  {
    to: "/app/interview/hr",
    title: "Practice an HR round",
    body: "Answer a few questions by typing or speaking and get feedback on each one.",
    icon: icons.chat,
    tint: "from-violet-500/15 to-fuchsia-500/10 text-violet-500",
  },
  {
    to: "/app/coding",
    title: "Solve a coding problem",
    body: "Runs on the server right away. A submission adds your first coding score.",
    icon: icons.code,
    tint: "from-cyan-500/15 to-sky-500/10 text-cyan-600 dark:text-cyan-400",
  },
  {
    to: "/app/companies",
    title: "Browse company questions",
    body: "See what recruiters commonly ask, grouped by HR, technical, and coding.",
    icon: icons.building,
    tint: "from-emerald-500/15 to-teal-500/10 text-pine",
  },
]

const categoryIcons: Record<string, JSX.Element> = {
  resume: icons.resume,
  hr: icons.chat,
  hr_interview: icons.chat,
  technical: icons.chip,
  technical_interview: icons.chip,
  coding: icons.code,
  communication: icons.mic,
}

export function StudentDashboard() {
  const { user } = useAuth()
  const colors = useChartColors()
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
        { name: "Strong", value: analytics.strong_areas.length, fill: colors.success },
        { name: "Weak", value: analytics.weak_areas.length, fill: colors.danger },
      ].filter((item) => item.value > 0)
    : []
  const firstName = user?.full_name?.split(/\s+/)[0] ?? "there"
  const profileLine = [user?.roll_number, user?.branch, user?.graduation_year ? `Class of ${user.graduation_year}` : null]
    .filter(Boolean)
    .join(" · ")

  const readinessValue = readiness?.current ? readiness.current.readiness_percentage : null
  const average = measured.length
    ? Math.round(measured.reduce((sum, item) => sum + (item.score ?? 0), 0) / measured.length)
    : null
  const tooltipStyle = {
    background: colors.surface,
    border: `1px solid ${colors.grid}`,
    borderRadius: 12,
    color: colors.ink,
    boxShadow: "0 12px 30px -12px rgba(15,23,42,0.25)",
    fontSize: 12,
  }

  return (
    <div className="mx-auto max-w-6xl">
      <section className="relative overflow-hidden rounded-3xl bg-sidebar p-6 text-white shadow-lift ring-1 ring-white/5 sm:p-8">
        <div className="pointer-events-none absolute -top-24 -right-20 h-72 w-72 rounded-full bg-brand-gradient opacity-40 blur-3xl" aria-hidden="true" />
        <div className="pointer-events-none absolute -bottom-28 left-10 h-56 w-56 rounded-full bg-cyan-500/20 blur-3xl" aria-hidden="true" />
        <div className="pointer-events-none absolute inset-0 bg-grid opacity-[0.07]" aria-hidden="true" />
        <div className="relative flex flex-wrap items-center justify-between gap-8">
          <div className="max-w-xl">
            <p className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-[11px] font-semibold tracking-wider text-white/80 uppercase ring-1 ring-white/15">
              {icons.spark}
              Student overview
            </p>
            <h1 className="mt-4 font-serif text-4xl leading-tight font-bold sm:text-5xl">
              Hello, <span className="text-brand-gradient">{firstName}</span>
            </h1>
            <p className="mt-2 text-sm text-white/65">
              {profileLine || "Complete your profile so the placement office sees the right details."}
            </p>
            <p className="mt-5 max-w-md text-[0.95rem] leading-relaxed text-white/80">
              {readiness?.current?.headline ??
                (measured.length
                  ? "Finish one more activity to estimate your placement readiness."
                  : "Start with any activity below. Your scores, charts and readiness estimate fill in as you practice.")}
            </p>
            <div className="mt-6 flex flex-wrap gap-2">
              <Link
                to={measured.length ? "/app/roadmap" : "/app/resume"}
                className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-[#1e1b4b] shadow-glow transition hover:-translate-y-px"
              >
                {measured.length ? "Open my roadmap" : "Start with my resume"}
                {icons.arrow}
              </Link>
              {measured.length > 0 ? (
                <button
                  type="button"
                  onClick={downloadReport}
                  disabled={downloading}
                  className="inline-flex items-center gap-2 rounded-xl bg-white/10 px-4 py-2.5 text-sm font-semibold text-white ring-1 ring-white/20 transition hover:bg-white/15 disabled:opacity-60"
                >
                  {icons.download}
                  {downloading ? "Preparing PDF…" : "Download report"}
                </button>
              ) : null}
            </div>
          </div>
          <div className="flex flex-col items-center gap-2">
            <ProgressRing value={readinessValue} size={168} stroke={14} label="Placement readiness" sublabel="Readiness" tone="light" />
            <p className="text-xs text-white/60">Random Forest estimate · proof of concept</p>
          </div>
        </div>
      </section>

      {error ? (
        <div className="mt-6">
          <Alert>{error}</Alert>
        </div>
      ) : null}
      {reportError ? (
        <div className="mt-4">
          <Alert>{reportError}</Alert>
        </div>
      ) : null}
      {loading ? <DashboardSkeleton /> : null}

      {!loading && analytics && measured.length === 0 ? (
        <section className="mt-8">
          <div className="flex items-end justify-between gap-3">
            <div>
              <h2 className="font-serif text-2xl font-bold">Let's get your first score</h2>
              <p className="mt-1 text-sm text-muted">Every chart here uses your own saved results, never sample data.</p>
            </div>
          </div>
          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            {quickStart.map((item, index) => (
              <Link
                key={item.to}
                to={item.to}
                style={{ animationDelay: `${index * 60}ms` }}
                className="group relative flex animate-rise gap-4 overflow-hidden rounded-2xl border border-line bg-foam p-5 shadow-card transition duration-300 hover:-translate-y-1 hover:border-brand/30 hover:shadow-lift"
              >
                <span className={`grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-gradient-to-br ${item.tint}`}>
                  {item.icon}
                </span>
                <span>
                  <span className="flex items-center gap-1.5 font-semibold group-hover:text-brand">
                    {item.title}
                    <span className="transition-transform duration-300 group-hover:translate-x-1">{icons.arrow}</span>
                  </span>
                  <span className="mt-1 block text-sm leading-relaxed text-muted">{item.body}</span>
                </span>
              </Link>
            ))}
          </div>
        </section>
      ) : null}

      {!loading && analytics && measured.length > 0 ? (
        <>
          <section className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatTile
              icon={icons.target}
              label="Average score"
              value={average === null ? "—" : String(average)}
              note={`${measured.length} of ${analytics.scores.length} areas measured`}
              tone="brand"
              progress={average}
            />
            {analytics.scores.slice(0, 3).map((item) => (
              <ScoreTile key={item.category} item={item} />
            ))}
          </section>
          {analytics.scores.length > 3 ? (
            <section className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {analytics.scores.slice(3).map((item) => (
                <ScoreTile key={item.category} item={item} />
              ))}
            </section>
          ) : null}

          <section className="mt-6 grid gap-4 lg:grid-cols-[1.5fr_0.8fr]">
            <article className="rounded-2xl border border-line bg-foam p-5 shadow-card">
              <ChartHeading title="Scores over time" detail="Every saved activity, newest on the right" />
              {lineData.length === 0 ? (
                <p className="mt-4 text-sm text-muted">Scores will plot here after your first saved activity.</p>
              ) : (
                <div className="mt-4 h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={lineData}>
                      <defs>
                        <linearGradient id="scoreFill" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor={colors.brand} stopOpacity={0.35} />
                          <stop offset="100%" stopColor={colors.brand} stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid stroke={colors.grid} vertical={false} strokeDasharray="4 4" />
                      <XAxis dataKey="name" tick={{ fill: colors.text, fontSize: 12 }} axisLine={false} tickLine={false} minTickGap={16} />
                      <YAxis domain={[0, 100]} tick={{ fill: colors.text, fontSize: 12 }} axisLine={false} tickLine={false} width={32} />
                      <Tooltip
                        contentStyle={tooltipStyle}
                        formatter={(value) => [value, "Score"]}
                        labelFormatter={(label, payload) => {
                          const item = payload?.[0]?.payload as { label?: string } | undefined
                          return item?.label ? `${label} · ${item.label}` : String(label)
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="score"
                        stroke={colors.brand}
                        strokeWidth={2.5}
                        fill="url(#scoreFill)"
                        dot={{ r: 3, fill: colors.surface, stroke: colors.brand, strokeWidth: 2 }}
                        activeDot={{ r: 5 }}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              )}
            </article>
            <article className="rounded-2xl border border-line bg-foam p-5 shadow-card">
              <ChartHeading title="Strong vs weak" detail="Strong ≥ 75 · weak < 60" />
              {strongWeak.length === 0 ? (
                <p className="mt-4 text-sm text-muted">Areas appear once a score is 75 or above, or below 60.</p>
              ) : (
                <>
                  <div className="mt-2 h-52">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={strongWeak}
                          dataKey="value"
                          nameKey="name"
                          innerRadius={55}
                          outerRadius={82}
                          paddingAngle={4}
                          cornerRadius={6}
                          stroke="none"
                        >
                          {strongWeak.map((item) => (
                            <Cell key={item.name} fill={item.fill} />
                          ))}
                        </Pie>
                        <Tooltip contentStyle={tooltipStyle} />
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

          <section className="mt-4 rounded-2xl border border-line bg-foam p-5 shadow-card">
            <ChartHeading title="Category breakdown" detail="Green is strong, amber needs work" />
            <div className="mt-4 h-64 overflow-x-auto">
              <div className="h-full min-w-[28rem]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analytics.scores.map((item) => ({ name: item.label, score: Math.round(item.score ?? 0) }))}>
                    <CartesianGrid stroke={colors.grid} vertical={false} strokeDasharray="4 4" />
                    <XAxis dataKey="name" tick={{ fill: colors.text, fontSize: 12 }} axisLine={false} tickLine={false} interval={0} />
                    <YAxis domain={[0, 100]} tick={{ fill: colors.text, fontSize: 12 }} axisLine={false} tickLine={false} width={32} />
                    <Tooltip contentStyle={tooltipStyle} cursor={{ fill: colors.grid, opacity: 0.4 }} formatter={(value) => [value, "Score"]} />
                    <Bar dataKey="score" radius={[8, 8, 0, 0]} maxBarSize={56}>
                      {analytics.scores.map((item) => (
                        <Cell
                          key={item.category}
                          fill={
                            item.score === null
                              ? colors.grid
                              : item.score >= 75
                                ? colors.success
                                : item.score < 60
                                  ? colors.warning
                                  : colors.brand
                          }
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>

          <section className="mt-4 grid gap-4 md:grid-cols-2">
            <AreaList title="Weak areas" tone="danger" empty="Nothing is below 60 yet." items={analytics.weak_areas} />
            <AreaList title="Strong areas" tone="success" empty="Nothing is at 75 or above yet." items={analytics.strong_areas} />
          </section>

          <section className="mt-4 overflow-hidden rounded-2xl border border-line bg-foam shadow-card">
            <div className="grid gap-0 md:grid-cols-[1fr_15rem]">
              <div className="p-5">
                <ChartHeading
                  title="What if you improve?"
                  detail="Drag a score. The estimate on the right updates live and is not saved to your trend."
                />
                <div className="mt-5 grid gap-5 sm:grid-cols-2">
                  {(
                    [
                      ["resume_ats", "Resume"],
                      ["interview_score", "Interview"],
                      ["coding_score", "Coding"],
                      ["communication_score", "Communication"],
                    ] as const
                  ).map(([key, label]) => (
                    <label key={key} className="text-sm">
                      <span className="mb-2 flex justify-between font-medium">
                        {label}
                        <span className="rounded-md bg-brand/10 px-1.5 text-brand tabular-nums">{Math.round(sliders[key])}</span>
                      </span>
                      <input
                        type="range"
                        min={0}
                        max={100}
                        value={sliders[key]}
                        onChange={(event) => setSliders((current) => ({ ...current, [key]: Number(event.target.value) }))}
                        className="w-full accent-[var(--color-navy)]"
                      />
                    </label>
                  ))}
                </div>
              </div>
              <div className="grid place-items-center border-t border-line bg-paper/60 p-5 md:border-t-0 md:border-l">
                <ProgressRing value={hypothetical} size={140} stroke={12} label="Estimated readiness" sublabel="Estimate" />
              </div>
            </div>
          </section>

          <section className="mt-4 grid gap-4 md:grid-cols-[1fr_auto] md:items-center rounded-2xl border border-line bg-foam p-5 shadow-card">
            <div className="flex items-center gap-4">
              <span className="grid h-12 w-12 place-items-center rounded-2xl bg-gold/10 text-gold">{icons.map}</span>
              <div>
                <h2 className="font-serif text-xl font-bold">
                  Preparation gap <span className="text-brand-gradient">{Math.round(analytics.gap.remaining_gap)}</span>
                </h2>
                <p className="mt-0.5 text-sm text-muted">
                  {analytics.gap.total_items === 0
                    ? "Generate a roadmap from your weak areas. Checking items off lowers this gap."
                    : `${analytics.gap.completed_items} of ${analytics.gap.total_items} roadmap items done.`}
                </p>
              </div>
            </div>
            <Link
              to="/app/roadmap"
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-navy px-4 py-2.5 text-sm font-semibold text-onbrand transition hover:-translate-y-px hover:bg-navy-soft"
            >
              Open roadmap {icons.arrow}
            </Link>
          </section>

          {readiness && readiness.history.length > 1 ? (
            <section className="mt-4 rounded-2xl border border-line bg-foam p-5 shadow-card">
              <ChartHeading title="Readiness trend" detail="Each estimate after a saved activity" />
              <div className="mt-4 h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart
                    data={readiness.history.map((point, index) => ({
                      name: formatShortDate(point.created_at) || `${index + 1}`,
                      readiness: Math.round(point.readiness_percentage),
                      date: formatDate(point.created_at),
                    }))}
                  >
                    <defs>
                      <linearGradient id="readyFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={colors.success} stopOpacity={0.3} />
                        <stop offset="100%" stopColor={colors.success} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke={colors.grid} vertical={false} strokeDasharray="4 4" />
                    <XAxis dataKey="name" tick={{ fill: colors.text, fontSize: 12 }} axisLine={false} tickLine={false} minTickGap={16} />
                    <YAxis domain={[0, 100]} tick={{ fill: colors.text, fontSize: 12 }} axisLine={false} tickLine={false} width={32} />
                    <Tooltip contentStyle={tooltipStyle} formatter={(value) => [`${value}%`, "Readiness"]} />
                    <Area type="monotone" dataKey="readiness" stroke={colors.success} strokeWidth={2.5} fill="url(#readyFill)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </section>
          ) : null}
        </>
      ) : null}
    </div>
  )
}

function ChartHeading({ title, detail }: { title: string; detail?: string }) {
  return (
    <div>
      <h2 className="font-serif text-xl font-bold">{title}</h2>
      {detail ? <p className="mt-0.5 text-xs text-muted">{detail}</p> : null}
    </div>
  )
}

function ScoreTile({ item }: { item: ScoreCard }) {
  const tone =
    item.score === null ? "muted" : item.score >= 75 ? "success" : item.score < 60 ? "danger" : "brand"
  const note =
    item.score === null ? "No score yet" : item.score >= 75 ? "Strong" : item.score < 60 ? "Needs work" : "On track"
  return (
    <StatTile
      icon={categoryIcons[item.category] ?? icons.chart}
      label={item.label}
      value={item.score === null ? "—" : String(Math.round(item.score))}
      note={note}
      tone={tone}
      progress={item.score}
    />
  )
}

function AreaList({
  title,
  empty,
  items,
  tone,
}: {
  title: string
  empty: string
  items: ScoreCard[]
  tone: "success" | "danger"
}) {
  const dot = tone === "success" ? "bg-pine" : "bg-clay"
  const chip = tone === "success" ? "bg-pine/10 text-pine" : "bg-clay/10 text-clay"
  return (
    <article className="rounded-2xl border border-line bg-foam p-5 shadow-card">
      <h2 className="flex items-center gap-2 font-serif text-xl font-bold">
        <span className={`h-2.5 w-2.5 rounded-full ${dot}`} aria-hidden="true" />
        {title}
      </h2>
      {items.length === 0 ? <p className="mt-3 text-sm text-muted">{empty}</p> : null}
      <ul className="mt-3 divide-y divide-line">
        {items.map((item) => (
          <li key={item.category} className="flex items-center justify-between py-2.5 text-sm">
            <span className="flex items-center gap-2.5">
              <span className="text-muted">{categoryIcons[item.category] ?? icons.chart}</span>
              {item.label}
            </span>
            <span className={`rounded-lg px-2 py-0.5 font-semibold tabular-nums ${chip}`}>
              {item.score === null ? "—" : Math.round(item.score)}
            </span>
          </li>
        ))}
      </ul>
    </article>
  )
}

function DashboardSkeleton() {
  return (
    <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4" role="status" aria-label="Loading your dashboard">
      {Array.from({ length: 8 }, (_, index) => (
        <Skeleton key={index} className={index > 3 ? "h-56 sm:col-span-2" : "h-32"} />
      ))}
    </div>
  )
}
