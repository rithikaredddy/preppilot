import { useState, type FormEvent, type ReactNode } from "react"
import { Alert, Button, Field, Notice, PageHeader, SelectField } from "../../components/ui"
import { useAuth } from "../../context/auth"
import { branchOptions } from "../../lib/format"
import { ApiError, api, fieldError } from "../../services/api"
import type { User } from "../../types"

function formFrom(user: User | null) {
  const text = (value: number | null | undefined) => (value === null || value === undefined ? "" : String(value))
  return {
    full_name: user?.full_name ?? "",
    roll_number: user?.roll_number ?? "",
    branch: user?.branch ?? "",
    graduation_year: text(user?.graduation_year),
    cgpa: text(user?.cgpa),
    backlogs: text(user?.backlogs),
    internship_count: text(user?.internship_count),
    certification_count: text(user?.certification_count),
    project_count: text(user?.project_count),
    phone: user?.phone ?? "",
    target_companies: user?.target_companies ?? "",
  }
}

export function StudentProfile() {
  const { user, refreshUser } = useAuth()
  // RequireAuth renders this page only after the user has loaded, so the form starts filled in.
  const [form, setForm] = useState(() => formFrom(user))
  const [error, setError] = useState<unknown>(null)
  const [saved, setSaved] = useState(false)
  const [pending, setPending] = useState(false)

  function update(name: keyof typeof form, value: string) {
    setSaved(false)
    setForm((current) => ({ ...current, [name]: value }))
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setPending(true)
    setSaved(false)
    setError(null)
    const optional = (value: string) => (value === "" ? null : Number(value))
    try {
      await api<User>("/api/v1/profile", {
        method: "PATCH",
        body: JSON.stringify({
          full_name: form.full_name,
          roll_number: form.roll_number,
          branch: form.branch,
          graduation_year: Number(form.graduation_year),
          cgpa: optional(form.cgpa),
          backlogs: optional(form.backlogs),
          internship_count: optional(form.internship_count),
          certification_count: optional(form.certification_count),
          project_count: optional(form.project_count),
          phone: form.phone || null,
          target_companies: form.target_companies,
        }),
      })
      await refreshUser()
      setSaved(true)
    } catch (caught) {
      setError(caught)
    } finally {
      setPending(false)
    }
  }

  const err = (name: string) => fieldError(error, name)

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        kicker="Profile"
        title="Your placement profile"
        body={`Signed in as ${user?.email ?? ""}. The placement office sees these details next to your scores, and the readiness model uses the academic numbers.`}
      />
      <form className="mt-8 space-y-6" onSubmit={onSubmit} noValidate>
        {error instanceof ApiError ? <Alert>{error.message}</Alert> : null}
        <Section title="Personal">
          <Field id="full_name" label="Full name" autoComplete="name" value={form.full_name} error={err("full_name")} onChange={(event) => update("full_name", event.target.value)} />
          <Field id="phone" label="Phone" type="tel" autoComplete="tel" value={form.phone} error={err("phone")} onChange={(event) => update("phone", event.target.value)} />
        </Section>
        <Section title="Academic">
          <Field id="roll_number" label="Roll number" value={form.roll_number} error={err("roll_number")} onChange={(event) => update("roll_number", event.target.value)} />
          <SelectField id="branch" label="Branch" value={form.branch} error={err("branch")} onChange={(event) => update("branch", event.target.value)}>
            <option value="" disabled>
              Choose your branch
            </option>
            {branchOptions(form.branch).map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </SelectField>
          <Field id="graduation_year" label="Graduation year" type="number" inputMode="numeric" value={form.graduation_year} error={err("graduation_year")} onChange={(event) => update("graduation_year", event.target.value)} />
          <Field id="cgpa" label="CGPA" type="number" step="0.01" min="0" max="10" inputMode="decimal" hint="Out of 10" value={form.cgpa} error={err("cgpa")} onChange={(event) => update("cgpa", event.target.value)} />
          <Field id="backlogs" label="Active backlogs" type="number" min="0" inputMode="numeric" value={form.backlogs} error={err("backlogs")} onChange={(event) => update("backlogs", event.target.value)} />
        </Section>
        <Section title="Experience">
          <Field id="internship_count" label="Internships" type="number" min="0" inputMode="numeric" value={form.internship_count} error={err("internship_count")} onChange={(event) => update("internship_count", event.target.value)} />
          <Field id="project_count" label="Projects" type="number" min="0" inputMode="numeric" value={form.project_count} error={err("project_count")} onChange={(event) => update("project_count", event.target.value)} />
          <Field id="certification_count" label="Certifications" type="number" min="0" inputMode="numeric" value={form.certification_count} error={err("certification_count")} onChange={(event) => update("certification_count", event.target.value)} />
          <div className="sm:col-span-2">
            <Field id="target_companies" label="Target companies" hint="Separate names with commas, for example TCS, Infosys, Accenture." value={form.target_companies} error={err("target_companies")} onChange={(event) => update("target_companies", event.target.value)} />
          </div>
        </Section>
        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" pending={pending} pendingLabel="Saving…">
            Save profile
          </Button>
          {saved ? <Notice>Profile saved.</Notice> : null}
        </div>
      </form>
    </div>
  )
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <fieldset className="rounded-lg border border-line bg-foam p-5">
      <legend className="px-1 font-serif text-xl">{title}</legend>
      <div className="mt-2 grid gap-4 sm:grid-cols-2">{children}</div>
    </fieldset>
  )
}
