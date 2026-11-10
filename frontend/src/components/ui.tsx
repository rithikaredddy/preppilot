import {
  useId,
  useState,
  type ButtonHTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from "react"

const controlClass =
  "w-full rounded-md border border-line bg-foam px-3 py-2.5 text-sm text-ink placeholder:text-muted/70 transition focus:border-navy/50 aria-[invalid=true]:border-clay/60"

export function Spinner({ className = "" }: { className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={`inline-block h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-current border-t-transparent ${className}`}
    />
  )
}

export function Button({
  children,
  pending = false,
  pendingLabel,
  variant = "primary",
  type = "button",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  pending?: boolean
  pendingLabel?: string
  variant?: "primary" | "secondary" | "ghost" | "danger"
}) {
  const styles = {
    primary: "bg-navy text-foam hover:bg-navy-soft",
    secondary: "border border-line bg-foam text-ink hover:bg-paper",
    ghost: "text-foam/90 hover:bg-white/10 hover:text-foam",
    danger: "border border-clay/30 bg-foam text-clay hover:bg-clay/10",
  }[variant]
  return (
    <button
      {...props}
      type={type}
      aria-busy={pending || undefined}
      disabled={pending || props.disabled}
      className={`inline-flex items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${styles} ${props.className ?? ""}`}
    >
      {pending ? (
        <>
          <Spinner />
          {pendingLabel ?? "Please wait…"}
        </>
      ) : (
        children
      )}
    </button>
  )
}

function FieldError({ id, error }: { id: string; error?: string }) {
  if (!error) return null
  return (
    <span id={id} className="mt-1 block text-sm text-clay" role="alert">
      {error}
    </span>
  )
}

function FieldHint({ id, hint }: { id: string; hint?: string }) {
  if (!hint) return null
  return (
    <span id={id} className="mt-1 block text-xs text-muted">
      {hint}
    </span>
  )
}

function describedBy(errorId: string, hintId: string, error?: string, hint?: string) {
  return [error ? errorId : null, hint ? hintId : null].filter(Boolean).join(" ") || undefined
}

export function Field({
  label,
  error,
  hint,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label: string; error?: string; hint?: string }) {
  const fallbackId = useId()
  const id = props.id ?? fallbackId
  const errorId = `${id}-error`
  const hintId = `${id}-hint`
  return (
    <label className="block text-sm" htmlFor={id}>
      <span className="mb-1.5 block font-medium text-ink">{label}</span>
      <input
        {...props}
        id={id}
        aria-invalid={Boolean(error)}
        aria-describedby={describedBy(errorId, hintId, error, hint)}
        className={controlClass}
      />
      <FieldHint id={hintId} hint={hint} />
      <FieldError id={errorId} error={error} />
    </label>
  )
}

export function PasswordField({
  label,
  error,
  hint,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label: string; error?: string; hint?: string }) {
  const [visible, setVisible] = useState(false)
  const fallbackId = useId()
  const id = props.id ?? fallbackId
  const errorId = `${id}-error`
  const hintId = `${id}-hint`
  return (
    <div className="text-sm">
      <label className="mb-1.5 block font-medium text-ink" htmlFor={id}>
        {label}
      </label>
      <div className="relative">
        <input
          {...props}
          id={id}
          type={visible ? "text" : "password"}
          aria-invalid={Boolean(error)}
          aria-describedby={describedBy(errorId, hintId, error, hint)}
          className={`${controlClass} pr-16`}
        />
        <button
          type="button"
          onClick={() => setVisible((current) => !current)}
          className="absolute inset-y-0 right-0 rounded-r-md px-3 text-xs font-semibold text-navy hover:bg-paper"
          aria-label={visible ? "Hide password" : "Show password"}
          aria-pressed={visible}
        >
          {visible ? "Hide" : "Show"}
        </button>
      </div>
      <FieldHint id={hintId} hint={hint} />
      <FieldError id={errorId} error={error} />
    </div>
  )
}

export function SelectField({
  label,
  error,
  hint,
  children,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & { label: string; error?: string; hint?: string; children: ReactNode }) {
  const fallbackId = useId()
  const id = props.id ?? fallbackId
  const errorId = `${id}-error`
  const hintId = `${id}-hint`
  return (
    <label className="block text-sm" htmlFor={id}>
      <span className="mb-1.5 block font-medium text-ink">{label}</span>
      <select
        {...props}
        id={id}
        aria-invalid={Boolean(error)}
        aria-describedby={describedBy(errorId, hintId, error, hint)}
        className={controlClass}
      >
        {children}
      </select>
      <FieldHint id={hintId} hint={hint} />
      <FieldError id={errorId} error={error} />
    </label>
  )
}

export function TextArea({
  label,
  error,
  hint,
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement> & { label: string; error?: string; hint?: string }) {
  const fallbackId = useId()
  const id = props.id ?? fallbackId
  const errorId = `${id}-error`
  const hintId = `${id}-hint`
  return (
    <label className="block text-sm" htmlFor={id}>
      <span className="mb-1.5 block font-medium text-ink">{label}</span>
      <textarea
        {...props}
        id={id}
        aria-invalid={Boolean(error)}
        aria-describedby={describedBy(errorId, hintId, error, hint)}
        className={`${controlClass} min-h-32`}
      />
      <FieldHint id={hintId} hint={hint} />
      <FieldError id={errorId} error={error} />
    </label>
  )
}

export function PageHeader({
  kicker,
  title,
  body,
  actions,
}: {
  kicker: string
  title: string
  body?: ReactNode
  actions?: ReactNode
}) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-4">
      <div className="max-w-3xl">
        <p className="text-xs font-semibold tracking-wider text-muted uppercase">{kicker}</p>
        <h1 className="mt-1 font-serif text-3xl leading-tight sm:text-4xl">{title}</h1>
        {body ? <p className="mt-3 text-sm leading-relaxed text-muted">{body}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </header>
  )
}

export function EmptyState({ title, body, children }: { title: string; body: string; children?: ReactNode }) {
  return (
    <div className="rounded-lg border border-dashed border-line bg-foam px-5 py-8">
      <h2 className="font-serif text-2xl">{title}</h2>
      <p className="mt-2 max-w-xl text-sm leading-relaxed text-muted">{body}</p>
      {children ? <div className="mt-5 flex flex-wrap gap-2">{children}</div> : null}
    </div>
  )
}

/** A polite live region shown while a slow request (usually an AI call) runs. */
export function LoadingLine({ label, detail }: { label: string; detail?: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex items-start gap-3 rounded-lg border border-navy/15 bg-navy/5 px-4 py-3 text-sm text-navy"
    >
      <Spinner className="mt-0.5" />
      <div>
        <p className="font-medium">{label}</p>
        {detail ? <p className="mt-0.5 text-muted">{detail}</p> : null}
      </div>
    </div>
  )
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div aria-hidden="true" className={`animate-pulse rounded-lg bg-line/70 ${className}`} />
}

export function ScoreBar({ label, value }: { label: string; value: number | null }) {
  const width = value === null ? 0 : Math.max(0, Math.min(100, value))
  const tone = value === null ? "bg-line" : value >= 75 ? "bg-pine" : value < 60 ? "bg-clay" : "bg-navy"
  return (
    <div>
      <div className="mb-1 flex justify-between gap-3 text-sm">
        <span>{label}</span>
        <span className="font-medium">{value === null ? "—" : Math.round(value)}</span>
      </div>
      <div
        className="h-2 rounded-full bg-line"
        role="meter"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={value === null ? undefined : Math.round(width)}
      >
        <div className={`h-2 rounded-full ${tone}`} style={{ width: `${width}%` }} />
      </div>
    </div>
  )
}

export function Alert({ children }: { children: ReactNode }) {
  return (
    <p className="rounded-md border border-clay/30 bg-clay/10 px-3 py-2 text-sm text-clay" role="alert">
      {children}
    </p>
  )
}

export function Notice({ children }: { children: ReactNode }) {
  return (
    <p className="rounded-md border border-pine/20 bg-pine/10 px-3 py-2 text-sm text-pine" role="status">
      {children}
    </p>
  )
}

export function Badge({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${className}`}>
      {children}
    </span>
  )
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`rounded-lg border border-line bg-foam p-5 ${className}`}>{children}</section>
}
