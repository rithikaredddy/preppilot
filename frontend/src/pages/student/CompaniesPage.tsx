import { useEffect, useState } from "react"
import { Link } from "react-router"
import { Alert, EmptyState, PageHeader, Skeleton } from "../../components/ui"
import { api } from "../../services/api"
import type { Company } from "../../types"

export function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[] | null>(null)
  const [error, setError] = useState("")

  useEffect(() => {
    api<{ items: Company[] }>("/api/v1/companies")
      .then((result) => setCompanies(result.items))
      .catch(() => setError("The company list could not be loaded."))
  }, [])

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader
        kicker="Companies"
        title="Previously asked questions"
        body="Choose a company. Each card opens the HR, technical, and coding questions students are commonly asked in that company's campus process."
      />
      {error ? (
        <div className="mt-6">
          <Alert>{error}</Alert>
        </div>
      ) : null}
      {companies === null && !error ? (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-3" role="status" aria-label="Loading companies">
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
        </div>
      ) : null}
      {companies && companies.length === 0 ? (
        <div className="mt-6">
          <EmptyState title="No companies yet" body="The question bank has not been loaded." />
        </div>
      ) : null}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {(companies ?? []).map((company) => (
          <Link
            key={company.slug}
            to={`/app/companies/${company.slug}`}
            className="group rounded-2xl border border-line bg-foam p-5 transition hover:-translate-y-0.5 hover:border-navy/30"
          >
            <div className="flex items-center gap-3">
              <span aria-hidden="true" className="grid h-12 w-12 place-items-center rounded-2xl bg-navy font-serif text-lg text-foam">
                {company.name.slice(0, 1)}
              </span>
              <div>
                <h2 className="font-serif text-2xl group-hover:text-navy">{company.name}</h2>
                <p className="text-xs text-muted">{company.question_count} questions</p>
              </div>
            </div>
            <p className="mt-4 text-sm leading-relaxed text-muted">{company.overview}</p>
            <p className="mt-4 text-sm font-semibold text-navy">View questions →</p>
          </Link>
        ))}
      </div>
    </div>
  )
}
