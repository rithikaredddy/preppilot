import { ApiError } from "../services/api"
import type { Role } from "../types"

export function homeFor(role: Role) {
  return role === "tpo" ? "/tpo" : "/app"
}

export const BRANCHES = [
  "CSE",
  "CSE - Data Science",
  "CSE - AI & ML",
  "IT",
  "ECE",
  "EEE",
  "MECH",
  "CIVIL",
  "Other",
] as const

/** The fixed branch list, plus a legacy free-text value so existing profiles still display. */
export function branchOptions(current: string | null | undefined): string[] {
  const list: string[] = [...BRANCHES]
  if (current && !list.includes(current)) list.unshift(current)
  return list
}

const dateFormat = new Intl.DateTimeFormat("en-IN", { day: "numeric", month: "short", year: "numeric" })
const dateTimeFormat = new Intl.DateTimeFormat("en-IN", {
  day: "numeric",
  month: "short",
  hour: "numeric",
  minute: "2-digit",
})
const shortDate = new Intl.DateTimeFormat("en-IN", { day: "numeric", month: "short" })

function parse(value: string | null | undefined) {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

export function formatDate(value: string | null | undefined) {
  const date = parse(value)
  return date ? dateFormat.format(date) : "—"
}

export function formatDateTime(value: string | null | undefined) {
  const date = parse(value)
  return date ? dateTimeFormat.format(date) : "—"
}

export function formatShortDate(value: string | null | undefined) {
  const date = parse(value)
  return date ? shortDate.format(date) : ""
}

export const STATUS_LABELS: Record<string, string> = {
  accepted: "Accepted",
  wrong_answer: "Wrong answer",
  time_limit: "Time limit exceeded",
  time_limit_exceeded: "Time limit exceeded",
  memory_limit: "Memory limit exceeded",
  compilation_error: "Compilation error",
  runtime_error: "Runtime error",
  partial: "Partially correct",
  error: "Could not run",
  internal_error: "Could not run",
  unavailable: "Runner unavailable",
}

export function statusLabel(status: string | null | undefined) {
  if (!status) return "—"
  return STATUS_LABELS[status] ?? status.replace(/_/g, " ").replace(/^\w/, (letter) => letter.toUpperCase())
}

export function statusTone(status: string | null | undefined) {
  if (status === "accepted") return "bg-pine/10 text-pine border-pine/20"
  if (status === "partial") return "border-gold/30 bg-gold/10 text-gold"
  return "bg-clay/10 text-clay border-clay/20"
}

/** A readable message for an API error, with a friendlier line for AI configuration problems. */
export function errorMessage(error: unknown, fallback: string) {
  if (!(error instanceof ApiError)) return fallback
  if (error.code === "llm_not_configured") {
    return "AI features are not set up on the server yet. Add a Gemini, OpenAI, or Anthropic key to the backend .env file and restart the API."
  }
  if (error.code === "llm_quota_exhausted") {
    return "The AI provider account has run out of free quota. Wait a minute and try again, or switch to another key."
  }
  const details = Object.values(error.details ?? {}).flat().filter(Boolean)
  return details.length > 0 ? details.join(" ") : error.message
}

export function readStorage(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

export function writeStorage(key: string, value: string | null) {
  try {
    if (value === null) localStorage.removeItem(key)
    else localStorage.setItem(key, value)
  } catch {
    // Storage can be unavailable in private windows; drafts are a convenience only.
  }
}
