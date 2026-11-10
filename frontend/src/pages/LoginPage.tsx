import { useState, type FormEvent, type ReactNode } from "react"
import { Link, useNavigate } from "react-router"
import { Alert, Button, Field, PasswordField } from "../components/ui"
import { useAuth } from "../context/auth"
import { ApiError, fieldError } from "../services/api"
import { homeFor } from "../lib/format"

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<unknown>(null)
  const [pending, setPending] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setPending(true)
    try {
      const user = await login(email, password)
      navigate(homeFor(user.role))
    } catch (caught) {
      setError(caught)
    } finally {
      setPending(false)
    }
  }

  return (
    <AuthScreen
      title="Sign in"
      lede="Use the email and password from your student or TPO account."
    >
      <form className="space-y-4" onSubmit={onSubmit} noValidate>
        {error instanceof ApiError ? <Alert>{error.message}</Alert> : null}
        <Field
          id="email"
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          error={fieldError(error, "email")}
          onChange={(event) => setEmail(event.target.value)}
        />
        <PasswordField
          id="password"
          label="Password"
          autoComplete="current-password"
          required
          value={password}
          error={fieldError(error, "password")}
          onChange={(event) => setPassword(event.target.value)}
        />
        <Button type="submit" pending={pending} pendingLabel="Signing in…" className="w-full">
          Sign in
        </Button>
      </form>
      <p className="mt-4 text-sm text-muted">
        <Link to="/forgot-password" className="font-medium text-navy">
          Forgot password
        </Link>
      </p>
      <p className="mt-2 text-sm text-muted">
        New here?{" "}
        <Link to="/register" className="font-medium text-navy">
          Create an account
        </Link>
      </p>
    </AuthScreen>
  )
}

export function AuthScreen({
  title,
  lede,
  children,
}: {
  title: string
  lede: string
  children: ReactNode
}) {
  return (
    <div className="grid min-h-screen md:grid-cols-[minmax(0,0.9fr)_minmax(22rem,1fr)]">
      <section className="hidden bg-navy px-10 py-12 text-foam md:flex md:flex-col md:justify-between">
        <p className="font-serif text-3xl">Interview Prep</p>
        <div>
          <h1 className="font-serif text-5xl leading-tight">Campus placements, with a shared record.</h1>
          <p className="mt-4 max-w-md text-foam/75">
            Students and the placement office sign in to the same system. Each role sees only its own screens.
          </p>
        </div>
        <p className="text-sm text-foam/60">AI Interview Preparation Platform</p>
      </section>
      <section className="flex items-center bg-paper px-5 py-10">
        <div className="mx-auto w-full max-w-md">
          <p className="font-serif text-2xl text-navy md:hidden">Interview Prep</p>
          <h2 className="mt-6 font-serif text-4xl">{title}</h2>
          <p className="mt-2 mb-6 text-sm leading-relaxed text-muted">{lede}</p>
          {children}
        </div>
      </section>
    </div>
  )
}
