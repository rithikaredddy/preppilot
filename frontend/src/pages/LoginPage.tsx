import { useState, type FormEvent, type ReactNode } from "react"
import { Link, useNavigate } from "react-router"
import { Alert, Button, Field, Logo, PasswordField } from "../components/ui"
import { useAuth } from "../context/auth"
import { ApiError, fieldError } from "../services/api"
import { homeFor } from "../lib/format"
import { ThemeToggle } from "../components/ThemeToggle"
import { icons } from "../components/icons"
import { BRAND, BRAND_TAGLINE } from "../lib/theme"

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
      <div className="mt-5 flex flex-wrap items-center justify-between gap-2 text-sm text-muted">
        <Link to="/forgot-password" className="font-medium text-brand hover:underline">
          Forgot password?
        </Link>
        <span>
          New here?{" "}
          <Link to="/register" className="font-semibold text-brand hover:underline">
            Create an account
          </Link>
        </span>
      </div>
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
    <div className="grid min-h-screen bg-paper lg:grid-cols-[minmax(0,1fr)_minmax(26rem,0.9fr)]">
      <section className="relative hidden overflow-hidden bg-sidebar px-12 py-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="pointer-events-none absolute -top-32 -left-24 h-96 w-96 rounded-full bg-brand-gradient opacity-40 blur-3xl" aria-hidden="true" />
        <div className="pointer-events-none absolute -right-24 -bottom-32 h-96 w-96 rounded-full bg-cyan-500/25 blur-3xl" aria-hidden="true" />
        <div className="pointer-events-none absolute inset-0 bg-grid opacity-[0.06]" aria-hidden="true" />
        <Link to="/" className="relative w-fit" aria-label={`${BRAND} home`}>
          <Logo name={BRAND} size={36} />
        </Link>
        <div className="relative max-w-lg">
          <h1 className="font-serif text-5xl leading-[1.08] font-extrabold">
            Practice today. <span className="text-brand-gradient">Get placed</span> tomorrow.
          </h1>
          <p className="mt-5 text-white/70">
            Students and the placement office sign in to the same system. Each role sees only its own screens.
          </p>
          <ul className="mt-8 space-y-3 text-sm text-white/85">
            {[
              [icons.resume, "ATS-style resume score against any role"],
              [icons.chat, "AI mock interviews that follow up on your answers"],
              [icons.code, "Coding practice with hidden tests and AI review"],
              [icons.target, "Readiness estimate and a personal roadmap"],
            ].map(([icon, text], index) => (
              <li key={index} className="flex items-center gap-3">
                <span className="grid h-9 w-9 place-items-center rounded-xl bg-white/10 text-[#a5b4fc] ring-1 ring-white/10">{icon}</span>
                {text}
              </li>
            ))}
          </ul>
        </div>
        <p className="relative text-sm text-white/50">{BRAND_TAGLINE}</p>
      </section>
      <section className="relative flex items-center px-5 py-10">
        <div className="absolute top-5 right-5">
          <ThemeToggle />
        </div>
        <div className="mx-auto w-full max-w-md animate-rise">
          <Link to="/" className="lg:hidden" aria-label={`${BRAND} home`}>
            <Logo name={BRAND} />
          </Link>
          <div className="mt-8 rounded-3xl border border-line bg-foam p-6 shadow-lift sm:p-8 lg:mt-0">
            <h2 className="font-serif text-3xl font-bold">{title}</h2>
            <p className="mt-2 mb-6 text-sm leading-relaxed text-muted">{lede}</p>
            {children}
          </div>
        </div>
      </section>
    </div>
  )
}
