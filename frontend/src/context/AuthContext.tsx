import { useEffect, useMemo, useState, type ReactNode } from "react"
import { api, clearTokens, storeTokens } from "../services/api"
import type { AuthResponse, User } from "../types"
import { AuthContext, type AuthContextValue } from "./auth"

function persist(response: AuthResponse) {
  storeTokens(response.access_token, response.refresh_token)
  return response.user
}

function hasStoredToken() {
  try {
    return Boolean(localStorage.getItem("access_token"))
  } catch {
    return false
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  // With no stored token there is nothing to check, so the app is ready immediately.
  const [ready, setReady] = useState(() => !hasStoredToken())

  useEffect(() => {
    if (!hasStoredToken()) return
    api<User>("/api/v1/auth/me")
      .then(setUser)
      .catch(() => {
        clearTokens()
        setUser(null)
      })
      .finally(() => setReady(true))
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      ready,
      async login(email, password) {
        const response = await api<AuthResponse>("/api/v1/auth/login", {
          method: "POST",
          body: JSON.stringify({ email, password }),
        })
        const nextUser = persist(response)
        setUser(nextUser)
        return nextUser
      },
      async register(payload) {
        const response = await api<AuthResponse>("/api/v1/auth/register", {
          method: "POST",
          body: JSON.stringify(payload),
        })
        const nextUser = persist(response)
        setUser(nextUser)
        return nextUser
      },
      async logout() {
        const refreshToken = localStorage.getItem("refresh_token")
        try {
          if (refreshToken) {
            await api("/api/v1/auth/logout", {
              method: "POST",
              body: JSON.stringify({ refresh_token: refreshToken }),
            })
          }
        } finally {
          clearTokens()
          setUser(null)
        }
      },
      async refreshUser() {
        const nextUser = await api<User>("/api/v1/auth/me")
        setUser(nextUser)
      },
    }),
    [ready, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
