import { useEffect, useState } from "react"
import { Link, useParams } from "react-router"
import { Alert, Badge, PageHeader, Skeleton } from "../../components/ui"
import { ApiError, api } from "../../services/api"
import type { CompanyQuestion } from "../../types"

const groups = [
  ["hr", "HR"],
  ["technical", "Technical"],
  ["coding", "Coding"],
] as const

export function CompanyDetailPage() {
  const { slug } = useParams()
  const [companyName, setCompanyName] = useState("")
  const [overview, setOverview] = useState("")
  const [items, setItems] = useState<CompanyQuestion[] | null>(null)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!slug) return
    api<{ company: { name: string; overview: string }; items: CompanyQuestion[] }>(
      `/api/v1/companies/${slug}/questions`,
    )
      .then((result) => {
        setCompanyName(result.company.name)
        setOverview(result.company.overview)
        setItems(result.items)
      })
      .catch((caught) => setError(caught instanceof ApiError ? caught.message : "Those questions could not be loaded."))
  }, [slug])

  const back = (
    <Link to="/app/companies" className="text-sm font-medium text-navy hover:underline">
      ← All companies
    </Link>
  )
  if (error) {
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        {back}
        <Alert>{error}</Alert>
      </div>
    )
  }
  if (!items) {
    return (
      <div className="mx-auto max-w-3xl space-y-4" role="status" aria-label="Loading questions">
        {back}
        <Skeleton className="h-28" />
        <Skeleton className="h-40" />
      </div>
    )
  }

  const counts = groups.map(([key, label]) => [label, items.filter((item) => item.category === key).length] as const)

  return (
    <div className="mx-auto max-w-3xl">
      {back}
      <div className="mt-4">
        <PageHeader kicker="Previously asked" title={companyName} body={overview} />
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-2">
        {counts
          .filter(([, count]) => count > 0)
          .map(([label, count]) => (
            <Badge key={label} className="border-line bg-foam text-ink">
              {label} · {count}
            </Badge>
          ))}
      </div>
      <div className="mt-5 flex flex-wrap gap-2">
        <Link
          to={`/app/coding?company=${slug}`}
          className="rounded-md bg-navy px-4 py-2.5 text-sm font-semibold text-foam hover:bg-navy-soft"
        >
          Practice coding tasks
        </Link>
        <Link
          to="/app/interview/hr"
          className="rounded-md border border-line bg-foam px-4 py-2.5 text-sm font-semibold hover:bg-paper"
        >
          Mock HR interview
        </Link>
      </div>
      <div className="mt-8 space-y-8">
        {groups.map(([key, label]) => {
          const questions = items.filter((item) => item.category === key)
          if (!questions.length) return null
          return (
            <section key={key}>
              <h2 className="font-serif text-2xl">{label}</h2>
              <ol className="mt-3 space-y-3">
                {questions.map((question, index) => (
                  <li key={question.id} className="rounded-xl border border-line bg-foam p-4">
                    <p className="text-xs font-medium tracking-wide text-muted uppercase">
                      {index + 1} · {question.topic} · {question.difficulty}
                    </p>
                    <p className="mt-2 leading-relaxed">{question.prompt}</p>
                    {question.preparation_tip ? (
                      <p className="mt-3 rounded-md bg-paper px-3 py-2 text-sm text-muted">
                        <span className="font-semibold text-ink">Tip: </span>
                        {question.preparation_tip}
                      </p>
                    ) : null}
                  </li>
                ))}
              </ol>
            </section>
          )
        })}
      </div>
    </div>
  )
}
