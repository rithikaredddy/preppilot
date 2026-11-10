import { useState, type FormEvent } from "react"
import { Link, useNavigate } from "react-router"
import { BRANCHES, homeFor } from "../lib/format"
import { Alert, Button, Field, Notice, PasswordField, SelectField } from "../components/ui"
import { useAuth } from "../context/auth"
import { ApiError, api, fieldError } from "../services/api"
import type { Role } from "../types"
import { AuthScreen } from "./LoginPage"

const DEFAULT_GRADUATION_YEAR = String(new Date().getFullYear() + 1)

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [role, setRole] = useState<Role>("student")
  const [error, setError] = useState<unknown>(null)
  const [pending, setPending] = useState(false)
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    roll_number: "",
    branch: "",
    graduation_year: DEFAULT_GRADUATION_YEAR,
    department: "",
    designation: "",
    otp: "",
  })
  const [otpMessage, setOtpMessage] = useState("")
  const [devOtp, setDevOtp] = useState("")
  const [sendingOtp, setSendingOtp] = useState(false)

  function update(name: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [name]: value }))
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setPending(true)
    const payload =
      role === "student"
        ? {
            role,
            full_name: form.full_name,
            email: form.email,
            password: form.password,
            roll_number: form.roll_number,
            branch: form.branch,
            graduation_year: Number(form.graduation_year),
          }
        : {
            role,
            full_name: form.full_name,
            email: form.email,
            password: form.password,
            department: form.department,
            designation: form.designation,
            otp: form.otp,
          }
    try {
      const user = await register(payload)
      navigate(homeFor(user.role))
    } catch (caught) {
      setError(caught)
    } finally {
      setPending(false)
    }
  }

  async function sendOtp() {
    setError(null)
    setOtpMessage("")
    setDevOtp("")
    setSendingOtp(true)
    try {
      const response = await api<{ message: string; otp?: string }>("/api/v1/auth/tpo-otp", {
        method: "POST",
        body: JSON.stringify({ email: form.email }),
      })
      setOtpMessage(response.message)
      setDevOtp(response.otp ?? "")
      if (response.otp) update("otp", response.otp)
    } catch (caught) {
      setError(caught)
    } finally {
      setSendingOtp(false)
    }
  }

  return (
    <AuthScreen title="Create an account" lede="Students can register directly. A TPO verifies the email address with a 6-digit code.">
      <form className="space-y-4" onSubmit={onSubmit} noValidate>
        {error instanceof ApiError ? <Alert>{error.message}</Alert> : null}
        <fieldset>
          <legend className="mb-2 text-sm font-medium">I am registering as</legend>
          <div className="grid grid-cols-2 gap-2">
            {(
              [
                ["student", "Student"],
                ["tpo", "TPO"],
              ] as const
            ).map(([value, label]) => (
              <label
                key={value}
                className={`cursor-pointer rounded-md border px-3 py-2 text-center text-sm font-medium transition focus-within:ring-2 focus-within:ring-navy focus-within:ring-offset-2 ${role === value ? "border-navy bg-navy text-foam" : "border-line bg-foam hover:bg-paper"}`}
              >
                <input
                  className="sr-only"
                  type="radio"
                  name="role"
                  value={value}
                  checked={role === value}
                  onChange={() => setRole(value)}
                />
                {label}
              </label>
            ))}
          </div>
        </fieldset>
        <Field id="full_name" label="Full name" required value={form.full_name} error={fieldError(error, "full_name")} onChange={(event) => update("full_name", event.target.value)} />
        <Field id="email" label="Email" type="email" autoComplete="email" required value={form.email} error={fieldError(error, "email")} onChange={(event) => update("email", event.target.value)} />
        <PasswordField id="password" label="Password" autoComplete="new-password" required hint="At least 8 characters, with one letter and one number." value={form.password} error={fieldError(error, "password")} onChange={(event) => update("password", event.target.value)} />
        {role === "student" ? (
          <>
            <Field id="roll_number" label="Roll number" required value={form.roll_number} error={fieldError(error, "roll_number")} onChange={(event) => update("roll_number", event.target.value)} />
            <SelectField id="branch" label="Branch" required value={form.branch} error={fieldError(error, "branch")} onChange={(event) => update("branch", event.target.value)}>
              <option value="" disabled>
                Choose your branch
              </option>
              {BRANCHES.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </SelectField>
            <Field id="graduation_year" label="Graduation year" type="number" required value={form.graduation_year} error={fieldError(error, "graduation_year")} onChange={(event) => update("graduation_year", event.target.value)} />
          </>
        ) : (
          <>
            <Field id="department" label="Department" required value={form.department} error={fieldError(error, "department")} onChange={(event) => update("department", event.target.value)} />
            <Field id="designation" label="Designation" required value={form.designation} error={fieldError(error, "designation")} onChange={(event) => update("designation", event.target.value)} />
            <div className="flex items-end gap-2">
              <div className="flex-1">
                <Field id="otp" label="Email code" inputMode="numeric" autoComplete="one-time-code" maxLength={6} required value={form.otp} error={fieldError(error, "otp")} onChange={(event) => update("otp", event.target.value)} />
              </div>
              <Button type="button" variant="secondary" pending={sendingOtp} onClick={sendOtp}>
                Send code
              </Button>
            </div>
            {otpMessage ? <Notice>{otpMessage}</Notice> : null}
            {devOtp ? (
              <div className="rounded-md border border-navy bg-foam px-4 py-3">
                <p className="text-sm text-muted">No email was sent. Use this code</p>
                <p className="mt-1 font-serif text-4xl tracking-[0.25em] text-navy">{devOtp}</p>
              </div>
            ) : null}
          </>
        )}
        <Button type="submit" pending={pending} pendingLabel="Creating account…" className="w-full">
          Create account
        </Button>
      </form>
      <p className="mt-4 text-sm text-muted">
        Already registered?{" "}
        <Link to="/login" className="font-medium text-navy">
          Sign in
        </Link>
      </p>
    </AuthScreen>
  )
}
