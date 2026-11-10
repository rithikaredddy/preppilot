import type { AuthResponse } from "../types"

const API_BASE = import.meta.env.VITE_API_URL ?? ""

export class ApiError extends Error {
  status: number
  code: string
  details: Record<string, string[]>

  constructor(status: number, code: string, message: string, details: Record<string, string[]> = {}) {
    super(message)
    this.status = status
    this.code = code
    this.details = details
  }
}

export function fieldError(error: unknown, name: string): string | undefined {
  if (!(error instanceof ApiError)) return undefined
  return error.details[name]?.[0]
}

export function storeTokens(accessToken: string, refreshToken: string) {
  localStorage.setItem("access_token", accessToken)
  localStorage.setItem("refresh_token", refreshToken)
}

export function clearTokens() {
  localStorage.removeItem("access_token")
  localStorage.removeItem("refresh_token")
}

let refreshRequest: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem("refresh_token")
  if (!refreshToken) return null
  if (!refreshRequest) {
    refreshRequest = fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { Authorization: `Bearer ${refreshToken}` },
    })
      .then(async (response) => {
        if (!response.ok) {
          clearTokens()
          return null
        }
        const body = (await response.json()) as Pick<AuthResponse, "access_token" | "refresh_token">
        storeTokens(body.access_token, body.refresh_token)
        return body.access_token
      })
      .finally(() => {
        refreshRequest = null
      })
  }
  return refreshRequest
}

async function authorizedFetch(path: string, options: RequestInit = {}, retry = true): Promise<Response> {
  const headers = new Headers(options.headers)
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json")
  }
  const accessToken = localStorage.getItem("access_token")
  if (accessToken && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${accessToken}`)
  }

  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  } catch {
    throw new ApiError(0, "network", "The server is not reachable. Check your connection and try again.")
  }

  if (response.status === 401 && retry && accessToken && !path.startsWith("/api/v1/auth/refresh")) {
    const nextAccess = await refreshAccessToken()
    if (nextAccess) {
      return authorizedFetch(path, options, false)
    }
  }
  return response
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await authorizedFetch(path, options)

  if (response.status === 204) {
    return undefined as T
  }

  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const error = payload?.error
    throw new ApiError(
      response.status,
      error?.code ?? "request_failed",
      error?.message ?? "The request could not be completed.",
      error?.details ?? {},
    )
  }
  return payload as T
}

export async function downloadAuthenticated(path: string, filename: string) {
  const response = await authorizedFetch(path)
  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    const error = payload?.error
    throw new ApiError(
      response.status,
      error?.code ?? "request_failed",
      error?.message ?? "The file could not be downloaded.",
      error?.details ?? {},
    )
  }
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
