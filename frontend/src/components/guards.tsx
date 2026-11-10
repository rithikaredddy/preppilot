import type { ReactNode } from "react"
import { Navigate } from "react-router"
import { useAuth } from "../context/auth"
import { homeFor } from "../lib/format"
import type { Role } from "../types"
import { Spinner } from "./ui"

export function RequireAuth({ role, children }: { role: Role; children: ReactNode }) {
  const { user, ready } = useAuth()
  if (!ready) return <StatusScreen label="Checking your session" />
  if (!user) return <Navigate to="/login" replace />
  if (user.role !== role) return <Navigate to={homeFor(user.role)} replace />
  return children
}

export function GuestOnly({ children }: { children: ReactNode }) {
  const { user, ready } = useAuth()
  if (!ready) return <StatusScreen label="Checking your session" />
  if (user) return <Navigate to={homeFor(user.role)} replace />
  return children
}

export function StatusScreen({ label }: { label: string }) {
  return (
    <div className="grid min-h-screen place-items-center bg-paper px-6">
      <p className="flex items-center gap-2 text-sm text-muted" role="status">
        <Spinner />
        {label}
      </p>
    </div>
  )
}
