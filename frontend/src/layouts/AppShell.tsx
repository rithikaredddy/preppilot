import { NavLink, Outlet, useNavigate } from "react-router"
import { useEffect, useState, type ReactNode } from "react"
import { useAuth } from "../context/auth"

type Item = { to: string; label: string; icon: ReactNode; end?: boolean }

const iconProps = {
  width: 18,
  height: 18,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
}

const icons = {
  home: (
    <svg {...iconProps}>
      <path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z" />
    </svg>
  ),
  resume: (
    <svg {...iconProps}>
      <path d="M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8z" />
      <path d="M14 3v5h5M8 13h8M8 17h5" />
    </svg>
  ),
  chat: (
    <svg {...iconProps}>
      <path d="M4 5h16v11H8l-4 4z" />
    </svg>
  ),
  chip: (
    <svg {...iconProps}>
      <rect x="6" y="6" width="12" height="12" rx="2" />
      <path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4" />
    </svg>
  ),
  code: (
    <svg {...iconProps}>
      <path d="M8 8l-4 4 4 4M16 8l4 4-4 4M14 5l-4 14" />
    </svg>
  ),
  building: (
    <svg {...iconProps}>
      <path d="M4 21V5a1 1 0 0 1 1-1h9a1 1 0 0 1 1 1v16M15 10h4a1 1 0 0 1 1 1v10M3 21h18M8 8h3M8 12h3M8 16h3" />
    </svg>
  ),
  map: (
    <svg {...iconProps}>
      <path d="M9 4L3 6v14l6-2 6 2 6-2V4l-6 2z" />
      <path d="M9 4v14M15 6v14" />
    </svg>
  ),
  clock: (
    <svg {...iconProps}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </svg>
  ),
  user: (
    <svg {...iconProps}>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21a8 8 0 0 1 16 0" />
    </svg>
  ),
  users: (
    <svg {...iconProps}>
      <circle cx="9" cy="8" r="3.5" />
      <path d="M2 20a7 7 0 0 1 14 0M16 4.5a3.5 3.5 0 0 1 0 7M18 13.5a6 6 0 0 1 4 6.5" />
    </svg>
  ),
}

export function AppShell({ items, kicker }: { items: Item[]; kicker: string }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (!open) return
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false)
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [open])

  async function signOut() {
    await logout()
    navigate("/")
  }

  const initials = (user?.full_name ?? "?")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("")

  return (
    <div className="min-h-screen bg-paper text-ink md:grid md:grid-cols-[16.5rem_1fr]">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:rounded-md focus:bg-foam focus:px-3 focus:py-2 focus:text-sm"
      >
        Skip to content
      </a>
      <aside className="sticky top-0 z-30 border-b border-white/10 bg-navy text-foam md:h-screen md:overflow-y-auto md:border-b-0">
        <div className="flex items-center justify-between gap-4 px-5 py-4 md:py-6">
          <div>
            <p className="font-serif text-2xl">Interview Prep</p>
            <p className="mt-0.5 text-xs tracking-wide text-foam/70 uppercase">{kicker}</p>
          </div>
          <button
            type="button"
            className="rounded-md border border-white/20 px-3 py-1.5 text-sm text-foam md:hidden"
            aria-expanded={open}
            aria-controls="workspace-nav"
            onClick={() => setOpen((current) => !current)}
          >
            {open ? "Close" : "Menu"}
          </button>
        </div>
        <nav
          id="workspace-nav"
          className={`${open ? "block" : "hidden"} space-y-0.5 px-3 pb-4 md:block`}
          aria-label="Workspace"
        >
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-md px-3 py-2 text-sm transition ${
                  isActive ? "bg-white/15 font-semibold text-foam" : "text-foam/80 hover:bg-white/10 hover:text-foam"
                }`
              }
            >
              {item.icon}
              {item.label}
            </NavLink>
          ))}
          <button
            type="button"
            onClick={signOut}
            className="mt-2 w-full rounded-md px-3 py-2 text-left text-sm text-foam/80 hover:bg-white/10 md:hidden"
          >
            Sign out
          </button>
        </nav>
      </aside>
      <div className="min-w-0">
        <header className="hidden items-center justify-between border-b border-line bg-foam px-8 py-3 md:flex">
          <div className="flex items-center gap-3">
            <span className="grid h-9 w-9 place-items-center rounded-full bg-navy text-xs font-semibold text-foam">
              {initials}
            </span>
            <div>
              <p className="text-sm font-medium">{user?.full_name}</p>
              <p className="text-xs text-muted">{user?.email}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={signOut}
            className="rounded-md border border-line px-3 py-1.5 text-sm font-medium text-navy hover:bg-paper"
          >
            Sign out
          </button>
        </header>
        <main id="main" className="px-4 py-6 sm:px-5 md:px-8 md:py-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export function StudentLayout() {
  return (
    <AppShell
      kicker="Student"
      items={[
        { to: "/app", label: "Overview", icon: icons.home, end: true },
        { to: "/app/resume", label: "Resume", icon: icons.resume },
        { to: "/app/interview/hr", label: "HR interview", icon: icons.chat },
        { to: "/app/interview/technical", label: "Technical interview", icon: icons.chip },
        { to: "/app/coding", label: "Coding", icon: icons.code },
        { to: "/app/companies", label: "Companies", icon: icons.building },
        { to: "/app/roadmap", label: "Roadmap", icon: icons.map },
        { to: "/app/interview/history", label: "History", icon: icons.clock },
        { to: "/app/profile", label: "Profile", icon: icons.user },
      ]}
    />
  )
}

export function TpoLayout() {
  return (
    <AppShell
      kicker="Placement office"
      items={[
        { to: "/tpo", label: "Students", icon: icons.users, end: true },
        { to: "/tpo/profile", label: "Profile", icon: icons.user },
      ]}
    />
  )
}
