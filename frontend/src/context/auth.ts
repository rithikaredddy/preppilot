import { createContext, useContext } from "react"
import type { User } from "../types"

export type AuthContextValue = {
  user: User | null
  ready: boolean
  login: (email: string, password: string) => Promise<User>
  register: (payload: Record<string, unknown>) => Promise<User>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) {
    throw new Error("useAuth must be used inside AuthProvider")
  }
  return value
}
