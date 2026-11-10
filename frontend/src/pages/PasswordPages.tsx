import { useState, type FormEvent } from "react"
import { Link, useSearchParams } from "react-router"
import { Alert, Button, Field, Notice } from "../components/ui"
import { ApiError, api, fieldError } from "../services/api"
import { AuthScreen } from "./LoginPage"

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("")
  const [message, setMessage] = useState("")
  const [resetToken, setResetToken] = useState("")
  const [error, setError] = useState<unknown>(null)
  const [pending, setPending] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setPending(true)
    setError(null)
    setResetToken("")
    try {
      const response = await api<{ message: string; reset_token?: string }>("/api/v1/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ email }),
      })
      setMessage(response.message)
      setResetToken(response.reset_token ?? "")
    } catch (caught) {
      setError(caught)
    } finally {
      setPending(false)
    }
  }

  return (
    <AuthScreen title="Reset password" lede="We will send a reset link if this email belongs to an account.">
      <form className="space-y-4" onSubmit={onSubmit}>
        {error instanceof ApiError ? <Alert>{error.message}</Alert> : null}
        {message ? <Notice>{message}</Notice> : null}
        {resetToken ? (
          <Notice>
            Email delivery is not configured, so the development server returned a token.{" "}
            <Link className="font-medium underline" to={`/reset-password?token=${encodeURIComponent(resetToken)}`}>
              Continue to choose a new password
            </Link>
            .
          </Notice>
        ) : null}
        <Field id="email" label="Email" type="email" required value={email} error={fieldError(error, "email")} onChange={(event) => setEmail(event.target.value)} />
        <Button type="submit" pending={pending} className="w-full">
          Send reset link
        </Button>
      </form>
      <p className="mt-4 text-sm">
        <Link to="/login" className="font-medium text-navy">
          Back to sign in
        </Link>
      </p>
    </AuthScreen>
  )
}

export function ResetPasswordPage() {
  const [params] = useSearchParams()
  const [password, setPassword] = useState("")
  const [message, setMessage] = useState("")
  const [error, setError] = useState<unknown>(null)
  const [pending, setPending] = useState(false)
  const token = params.get("token") ?? ""

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setPending(true)
    setError(null)
    try {
      const response = await api<{ message: string }>("/api/v1/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({ token, password }),
      })
      setMessage(response.message)
    } catch (caught) {
      setError(caught)
    } finally {
      setPending(false)
    }
  }

  return (
    <AuthScreen title="Choose a new password" lede="Use at least 8 characters, with one letter and one number.">
      <form className="space-y-4" onSubmit={onSubmit}>
        {error instanceof ApiError ? <Alert>{error.message}</Alert> : null}
        {message ? <Notice>{message}</Notice> : null}
        {!token ? <Alert>This reset link is missing a token.</Alert> : null}
        <Field id="password" label="New password" type="password" autoComplete="new-password" required value={password} error={fieldError(error, "password")} onChange={(event) => setPassword(event.target.value)} />
        <Button type="submit" pending={pending} disabled={!token} className="w-full">
          Update password
        </Button>
      </form>
      <p className="mt-4 text-sm">
        <Link to="/login" className="font-medium text-navy">
          Sign in
        </Link>
      </p>
    </AuthScreen>
  )
}
