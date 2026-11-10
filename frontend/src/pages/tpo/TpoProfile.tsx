import { useState, type FormEvent } from "react"
import { Alert, Button, Field, Notice, PageHeader } from "../../components/ui"
import { useAuth } from "../../context/auth"
import { ApiError, api, fieldError } from "../../services/api"
import type { User } from "../../types"

export function TpoProfile() {
  const { user, refreshUser } = useAuth()
  const [form, setForm] = useState(() => ({
    full_name: user?.full_name ?? "",
    department: user?.department ?? "",
    designation: user?.designation ?? "",
  }))
  const [error, setError] = useState<unknown>(null)
  const [saved, setSaved] = useState(false)
  const [pending, setPending] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setPending(true)
    setSaved(false)
    setError(null)
    try {
      await api<User>("/api/v1/profile", {
        method: "PATCH",
        body: JSON.stringify(form),
      })
      await refreshUser()
      setSaved(true)
    } catch (caught) {
      setError(caught)
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="mx-auto max-w-xl">
      <PageHeader kicker="Profile" title="Office profile" body={`Signed in as ${user?.email ?? ""}.`} />
      <form className="mt-8 space-y-4 rounded-2xl border border-line bg-foam shadow-card p-5" onSubmit={onSubmit} noValidate>
        {error instanceof ApiError ? <Alert>{error.message}</Alert> : null}
        <Field id="full_name" label="Full name" value={form.full_name} error={fieldError(error, "full_name")} onChange={(event) => setForm({ ...form, full_name: event.target.value })} />
        <Field id="department" label="Department" value={form.department} error={fieldError(error, "department")} onChange={(event) => setForm({ ...form, department: event.target.value })} />
        <Field id="designation" label="Designation" value={form.designation} error={fieldError(error, "designation")} onChange={(event) => setForm({ ...form, designation: event.target.value })} />
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
