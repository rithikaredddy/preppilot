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
  "w-full rounded-xl border border-line bg-foam px-3 py-2.5 text-sm text-ink placeholder:text-muted/70 transition focus:border-brand/50 aria-[invalid=true]:border-clay/60"

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
    primary:
      "bg-navy text-onbrand shadow-[0_1px_0_rgb(255_255_255/0.15)_inset,0_8px_20px_-8px_rgb(79_70_229/0.6)] hover:bg-navy-soft hover:-translate-y-px active:translate-y-0",
    secondary: "border border-line bg-foam text-ink shadow-card hover:border-brand/30 hover:text-brand",
    ghost: "text-onbrand/90 hover:bg-white/10 hover:text-onbrand",
    danger: "border border-clay/30 bg-foam text-clay hover:bg-clay/10",
  }[variant]
  return (
    <button
      {...props}
      type={type}
      aria-busy={pending || undefined}
      disabled={pending || props.disabled}
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition duration-200 disabled:pointer-events-none disabled:opacity-60 ${styles} ${props.className ?? ""}`}
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
          className="absolute inset-y-0 right-0 rounded-r-md px-3 text-xs font-semibold text-brand hover:bg-paper"
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
        <p className="inline-flex items-center gap-2 rounded-full border border-brand/20 bg-brand/10 px-3 py-1 text-[11px] font-semibold tracking-wider text-brand uppercase">
          <span className="h-1.5 w-1.5 rounded-full bg-brand-gradient" aria-hidden="true" />
          {kicker}
        </p>
        <h1 className="mt-3 font-serif text-3xl leading-tight font-bold sm:text-[2.6rem]">{title}</h1>
        {body ? <p className="mt-3 text-[0.95rem] leading-relaxed text-muted">{body}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </header>
  )
}

export function EmptyState({ title, body, children }: { title: string; body: string; children?: ReactNode }) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-dashed border-line bg-foam px-6 py-9">
      <div className="pointer-events-none absolute -top-16 -right-16 h-48 w-48 rounded-full bg-brand-gradient opacity-10 blur-2xl" aria-hidden="true" />
      <h2 className="font-serif text-2xl font-bold">{title}</h2>
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
      className="flex items-start gap-3 rounded-lg border border-brand/15 bg-brand/5 px-4 py-3 text-sm text-brand"
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
  return (
    <div
      aria-hidden="true"
      className={`animate-shimmer rounded-2xl bg-[linear-gradient(90deg,var(--color-line)_0%,var(--color-foam)_50%,var(--color-line)_100%)] bg-[length:200%_100%] ${className}`}
    />
  )
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
        <div className={`h-2 rounded-full ${tone} transition-[width] duration-700`} style={{ width: `${width}%` }} />
      </div>
    </div>
  )
}

export function Alert({ children }: { children: ReactNode }) {
  return (
    <p className="rounded-xl border border-clay/30 bg-clay/10 px-3 py-2 text-sm text-clay" role="alert">
      {children}
    </p>
  )
}

export function Notice({ children }: { children: ReactNode }) {
  return (
    <p className="rounded-xl border border-pine/20 bg-pine/10 px-3 py-2 text-sm text-pine" role="status">
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
  return <section className={`rounded-2xl border border-line bg-foam shadow-card p-5 ${className}`}>{children}</section>
}


/** Brand mark: gradient tile with the "P" monogram. */
export function Logo({ size = 32, withName = true, name, className = "" }: { size?: number; withName?: boolean; name?: string; className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <span
        className="grid shrink-0 place-items-center rounded-[28%] bg-brand-gradient shadow-glow"
        style={{ width: size, height: size }}
        aria-hidden="true"
      >
        <svg viewBox="0 0 32 32" width={size * 0.72} height={size * 0.72}>
          <path d="M10 22.5V9.5h6.2a4.6 4.6 0 0 1 0 9.2H13.4" fill="none" stroke="#fff" strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M18.5 22.5l4-4" stroke="#fff" strokeWidth="2.8" strokeLinecap="round" />
        </svg>
      </span>
      {withName ? <span className="font-serif text-xl font-bold tracking-tight">{name}</span> : null}
    </span>
  )
}

/** Circular progress meter used for readiness and scores. */
export function ProgressRing({
  value,
  size = 132,
  stroke = 12,
  label,
  sublabel,
  tone = "gradient",
}: {
  value: number | null
  size?: number
  stroke?: number
  label?: string
  sublabel?: string
  tone?: "gradient" | "light"
}) {
  const id = useId()
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const clamped = value === null ? 0 : Math.max(0, Math.min(100, value))
  const offset = circumference * (1 - clamped / 100)
  return (
    <div
      className="relative inline-grid place-items-center"
      style={{ width: size, height: size }}
      role="meter"
      aria-label={label ?? "Progress"}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={value === null ? undefined : Math.round(clamped)}
    >
      <svg width={size} height={size} className="-rotate-90">
        <defs>
          <linearGradient id={`ring-${id}`} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={tone === "light" ? "#ffffff" : "#6366f1"} />
            <stop offset="55%" stopColor={tone === "light" ? "#e0e7ff" : "#8b5cf6"} />
            <stop offset="100%" stopColor={tone === "light" ? "#a5f3fc" : "#06b6d4"} />
          </linearGradient>
        </defs>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={stroke}
          className={tone === "light" ? "stroke-white/20" : "stroke-line"}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={`url(#ring-${id})`}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 1s cubic-bezier(0.2,0.7,0.2,1)" }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center text-center">
        <div>
          <p className="font-serif text-3xl leading-none font-bold">{value === null ? "—" : `${Math.round(clamped)}%`}</p>
          {sublabel ? <p className="mt-1 text-[11px] font-medium tracking-wide uppercase opacity-70">{sublabel}</p> : null}
        </div>
      </div>
    </div>
  )
}

/** Compact metric card with an icon, a value and a short status line. */
export function StatTile({
  icon,
  label,
  value,
  note,
  tone = "brand",
  progress,
}: {
  icon: ReactNode
  label: string
  value: string
  note?: string
  tone?: "brand" | "success" | "danger" | "warning" | "muted"
  progress?: number | null
}) {
  const tones = {
    brand: "bg-brand/10 text-brand",
    success: "bg-pine/10 text-pine",
    danger: "bg-clay/10 text-clay",
    warning: "bg-gold/10 text-gold",
    muted: "bg-line/60 text-muted",
  }[tone]
  const bar = {
    brand: "bg-navy",
    success: "bg-pine",
    danger: "bg-clay",
    warning: "bg-gold",
    muted: "bg-line",
  }[tone]
  return (
    <article className="group rounded-2xl border border-line bg-foam p-4 shadow-card transition duration-300 hover:-translate-y-0.5 hover:shadow-lift">
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-medium text-muted">{label}</p>
        <span className={`grid h-9 w-9 place-items-center rounded-xl ${tones}`}>{icon}</span>
      </div>
      <p className="mt-2 font-serif text-3xl font-bold">{value}</p>
      {note ? <p className="mt-1 text-xs font-medium text-muted">{note}</p> : null}
      {progress !== undefined ? (
        <div className="mt-3 h-1.5 rounded-full bg-line" aria-hidden="true">
          <div
            className={`h-1.5 rounded-full ${bar} transition-[width] duration-700`}
            style={{ width: `${Math.max(0, Math.min(100, progress ?? 0))}%` }}
          />
        </div>
      ) : null}
    </article>
  )
}
