import { useEffect, useState } from "react"
import { Link } from "react-router"
import { Alert, Button, EmptyState, PageHeader, SelectField, Skeleton } from "../../components/ui"
import { api } from "../../services/api"
import type { BatchInsights, StudentList, StudentListItem } from "../../types"

const PAGE_SIZE = 8

function readinessTone(value: number | null) {
  if (value === null) return "text-muted"
  // Compare the rounded value so the colour matches the number on screen.
  const shown = Math.round(value)
  if (shown < 60) return "text-clay"
  if (shown >= 75) return "text-pine"
  return "text-ink"
}

function csvCell(value: string | number | null) {
  const text = value === null ? "" : String(value)
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text
}

function downloadCsv(rows: StudentListItem[]) {
  const header = ["Name", "Email", "Roll number", "Branch", "Graduation year", "Readiness %", "Weakest factor"]
  const lines = rows.map((row) =>
    [
      row.full_name,
      row.email,
      row.roll_number,
      row.branch,
      row.graduation_year,
      row.readiness_percentage === null ? null : Math.round(row.readiness_percentage),
      row.top_factor,
    ]
      .map(csvCell)
      .join(","),
  )
  const blob = new Blob([[header.join(","), ...lines].join("\n")], { type: "text/csv" })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = "batch-readiness.csv"
  link.click()
  URL.revokeObjectURL(url)
}

export function TpoDashboard() {
  const [branch, setBranch] = useState("")
  const [threshold, setThreshold] = useState("")
  const [sort, setSort] = useState("readiness")
  const [page, setPage] = useState(1)
  const [result, setResult] = useState<{ key: string; students: StudentList; insights: BatchInsights } | null>(null)
  const [allBranches, setAllBranches] = useState<string[]>([])
  const [error, setError] = useState("")
  const [exporting, setExporting] = useState(false)

  const key = JSON.stringify({ branch, threshold, sort, page })
  const loading = result?.key !== key

  useEffect(() => {
    let cancelled = false
    const params = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE), sort, branch })
    if (threshold) params.set("readiness_below", threshold)
    Promise.all([
      api<StudentList>(`/api/v1/tpo/students?${params.toString()}`),
      api<BatchInsights>(`/api/v1/tpo/insights?${new URLSearchParams({ branch }).toString()}`),
    ])
      .then(([students, insights]) => {
        if (cancelled) return
        setResult({ key: JSON.stringify({ branch, threshold, sort, page }), students, insights })
        if (!branch) setAllBranches(insights.branch_averages.map((row) => row.branch))
        setError("")
      })
      .catch(() => {
        if (!cancelled) setError("The placement view could not be loaded.")
      })
    return () => {
      cancelled = true
    }
  }, [branch, page, sort, threshold])

  const data = result?.students ?? null
  const insights = result?.insights ?? null
  const pageCount = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1

  async function exportAll() {
    setExporting(true)
    try {
      const params = new URLSearchParams({ page: "1", page_size: "50", sort, branch })
      if (threshold) params.set("readiness_below", threshold)
      const first = await api<StudentList>(`/api/v1/tpo/students?${params.toString()}`)
      const rows = [...first.items]
      const pages = Math.ceil(first.total / first.page_size)
      for (let next = 2; next <= pages; next += 1) {
        params.set("page", String(next))
        const more = await api<StudentList>(`/api/v1/tpo/students?${params.toString()}`)
        rows.push(...more.items)
      }
      downloadCsv(rows)
    } catch {
      setError("The CSV export could not be prepared.")
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader
        kicker="Placement office"
        title="Batch readiness"
        body="Read-only scores for every registered student. Interview transcripts stay on the student account."
        actions={
          <Button variant="secondary" pending={exporting} pendingLabel="Exporting…" disabled={!data?.total} onClick={exportAll}>
            Export CSV
          </Button>
        }
      />
      {insights ? (
        <section className="mt-6 grid gap-3 md:grid-cols-3">
          <article className="rounded-lg border border-line bg-foam p-4">
            <p className="text-sm text-muted">Students{branch ? ` in ${branch}` : ""}</p>
            <p className="mt-1 font-serif text-3xl">{insights.student_count}</p>
          </article>
          <article className="rounded-lg border border-line bg-foam p-4">
            <p className="text-sm text-muted">Readiness below {insights.threshold}%</p>
            <p className={`mt-1 font-serif text-3xl ${insights.below_threshold_count > 0 ? "text-clay" : ""}`}>
              {insights.below_threshold_count}
            </p>
          </article>
          <article className="rounded-lg border border-line bg-foam p-4">
            <p className="text-sm text-muted">Common weak areas</p>
            {insights.common_weak_areas.length ? (
              <ul className="mt-2 flex flex-wrap gap-1.5">
                {insights.common_weak_areas.map((item) => (
                  <li key={item.area} className="rounded-full bg-clay/10 px-2.5 py-0.5 text-xs font-medium text-clay">
                    {item.area} · {item.student_count}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-2 text-sm">None recorded yet</p>
            )}
          </article>
        </section>
      ) : (
        <div className="mt-6 grid gap-3 md:grid-cols-3">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
      )}
      {insights && insights.branch_averages.length > 0 && !branch ? (
        <div className="mt-3 overflow-x-auto rounded-lg border border-line bg-foam">
          <table className="w-full min-w-[28rem] text-left text-sm">
            <caption className="sr-only">Average readiness by branch</caption>
            <thead className="border-b border-line text-muted">
              <tr>
                <th scope="col" className="px-4 py-3 font-medium">Branch</th>
                <th scope="col" className="px-4 py-3 font-medium">Students</th>
                <th scope="col" className="px-4 py-3 font-medium">Average readiness</th>
              </tr>
            </thead>
            <tbody>
              {insights.branch_averages.map((row) => (
                <tr key={row.branch} className="border-b border-line last:border-0">
                  <td className="px-4 py-3">
                    <button
                      type="button"
                      className="font-medium text-navy hover:underline"
                      onClick={() => {
                        setBranch(row.branch)
                        setPage(1)
                      }}
                    >
                      {row.branch}
                    </button>
                  </td>
                  <td className="px-4 py-3">{row.student_count}</td>
                  <td className={`px-4 py-3 font-medium ${readinessTone(row.average_readiness)}`}>
                    {row.average_readiness === null ? "—" : `${Math.round(row.average_readiness)}%`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      <div className="mt-6 grid gap-3 rounded-lg border border-line bg-foam p-4 sm:grid-cols-3">
        <SelectField
          id="branch"
          label="Branch"
          value={branch}
          onChange={(event) => {
            setBranch(event.target.value)
            setPage(1)
          }}
        >
          <option value="">All branches</option>
          {allBranches.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </SelectField>
        <SelectField
          id="threshold"
          label="Readiness below"
          value={threshold}
          onChange={(event) => {
            setThreshold(event.target.value)
            setPage(1)
          }}
        >
          <option value="">Any readiness</option>
          <option value="60">60%</option>
          <option value="70">70%</option>
          <option value="80">80%</option>
        </SelectField>
        <SelectField
          id="sort"
          label="Sort by"
          value={sort}
          onChange={(event) => {
            setSort(event.target.value)
            setPage(1)
          }}
        >
          <option value="readiness">Readiness</option>
          <option value="name">Name</option>
          <option value="branch">Branch</option>
          <option value="roll_number">Roll number</option>
        </SelectField>
      </div>

      {error ? (
        <div className="mt-6">
          <Alert>{error}</Alert>
        </div>
      ) : null}
      {loading && !data ? (
        <div className="mt-6 space-y-2" role="status" aria-label="Loading students">
          <Skeleton className="h-12" />
          <Skeleton className="h-12" />
          <Skeleton className="h-12" />
        </div>
      ) : null}
      {data && data.items.length === 0 ? (
        <div className="mt-6">
          <EmptyState title="No students match" body="Try another branch or clear the readiness filter." />
        </div>
      ) : null}
      {data && data.items.length > 0 ? (
        <div
          className={`mt-6 overflow-x-auto rounded-lg border border-line bg-foam transition-opacity ${loading ? "opacity-60" : ""}`}
          aria-busy={loading}
        >
          <table className="w-full min-w-[48rem] text-left text-sm">
            <caption className="sr-only">Students</caption>
            <thead className="border-b border-line text-muted">
              <tr>
                <th scope="col" className="px-4 py-3 font-medium">Name</th>
                <th scope="col" className="px-4 py-3 font-medium">Roll number</th>
                <th scope="col" className="px-4 py-3 font-medium">Branch</th>
                <th scope="col" className="px-4 py-3 font-medium">Readiness</th>
                <th scope="col" className="px-4 py-3 font-medium">Weakest factor</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((student) => (
                <tr key={student.id} className="border-b border-line last:border-0 hover:bg-paper/60">
                  <td className="px-4 py-3 font-medium">
                    <Link to={`/tpo/students/${student.id}`} className="text-navy hover:underline">
                      {student.full_name}
                    </Link>
                  </td>
                  <td className="px-4 py-3">{student.roll_number}</td>
                  <td className="px-4 py-3">{student.branch}</td>
                  <td className={`px-4 py-3 font-semibold ${readinessTone(student.readiness_percentage)}`}>
                    {student.readiness_percentage === null ? "—" : `${Math.round(student.readiness_percentage)}%`}
                  </td>
                  <td className="px-4 py-3">{student.top_factor ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
      {data ? (
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-sm">
          <p className="text-muted">
            {data.total} student{data.total === 1 ? "" : "s"}
          </p>
          <div className="flex items-center gap-2">
            <Button variant="secondary" className="px-3 py-1.5" disabled={page <= 1 || loading} onClick={() => setPage((current) => current - 1)}>
              Previous
            </Button>
            <span className="px-2 py-1.5 text-muted" aria-live="polite">
              Page {page} of {pageCount}
            </span>
            <Button
              variant="secondary"
              className="px-3 py-1.5"
              disabled={page >= pageCount || loading}
              onClick={() => setPage((current) => current + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  )
}
