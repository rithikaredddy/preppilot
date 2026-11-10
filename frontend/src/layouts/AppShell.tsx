import { NavLink, Outlet, useLocation, useNavigate } from "react-router"
import { useEffect, useState, type ReactNode } from "react"
import { CommandPalette, type Command } from "../components/CommandPalette"
import { ErrorBoundary } from "../components/ErrorBoundary"
import { ThemeToggle } from "../components/ThemeToggle"
import { icons } from "../components/icons"
import { Logo } from "../components/ui"
import { useAuth } from "../context/auth"
import { BRAND } from "../lib/theme"

type Item = { to: string; label: string; icon: ReactNode; end?: boolean; section?: string }

export function AppShell({ items, kicker }: { items: Item[]; kicker: string }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [open, setOpen] = useState(false)
  const [paletteOpen, setPaletteOpen] = useState(false)

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault()
        setPaletteOpen((current) => !current)
      }
      if (event.key === "Escape") setOpen(false)
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [])

  async function signOut() {
    await logout()
    navigate("/")
  }

  const commands: Command[] = [
    ...items.map((item) => ({ label: item.label, hint: item.section ?? "Go to", icon: item.icon, to: item.to })),
    { label: "Sign out", hint: "Account", icon: icons.logout, run: () => void signOut() },
  ]

  const initials = (user?.full_name ?? "?")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("")
  const current = items.find((item) =>
    item.end ? location.pathname === item.to : location.pathname.startsWith(item.to),
  )

  return (
    <div className="min-h-screen bg-paper text-ink md:grid md:grid-cols-[17rem_1fr]">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:rounded-xl focus:bg-foam focus:px-3 focus:py-2 focus:text-sm"
      >
        Skip to content
      </a>
      <aside className="sticky top-0 z-30 flex flex-col bg-sidebar text-sidebar-ink md:h-screen">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-48 bg-[radial-gradient(60%_80%_at_20%_0%,rgb(99_102_241/0.35),transparent)]" aria-hidden="true" />
        <div className="relative flex items-center justify-between gap-4 px-5 py-4 md:pt-6 md:pb-5">
          <div>
            <Logo name={BRAND} size={34} />
            <p className="mt-1.5 pl-[2.75rem] text-[11px] font-semibold tracking-[0.14em] text-sidebar-ink/50 uppercase">{kicker}</p>
          </div>
          <button
            type="button"
            className="grid h-9 w-9 place-items-center rounded-xl border border-white/15 text-sidebar-ink md:hidden"
            aria-expanded={open}
            aria-controls="workspace-nav"
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen((value) => !value)}
          >
            {open ? icons.close : icons.menu}
          </button>
        </div>
        <nav
          id="workspace-nav"
          className={`${open ? "block" : "hidden"} relative flex-1 overflow-y-auto px-3 pb-4 md:block`}
          aria-label="Workspace"
        >
          {items.map((item, index) => {
            const heading = item.section && item.section !== items[index - 1]?.section ? item.section : null
            return (
              <div key={item.to}>
                {heading ? (
                  <p className="mt-5 mb-1.5 px-3 text-[10px] font-semibold tracking-[0.16em] text-sidebar-ink/40 uppercase first:mt-1">
                    {heading}
                  </p>
                ) : null}
                <NavLink
                  to={item.to}
                  end={item.end}
                  onClick={() => setOpen(false)}
                  className={({ isActive }) =>
                    `group relative mb-0.5 flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition duration-200 ${
                      isActive
                        ? "bg-white/[0.09] font-semibold text-white shadow-[inset_0_0_0_1px_rgb(255_255_255/0.06)]"
                        : "text-sidebar-ink/65 hover:bg-white/[0.05] hover:text-white"
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      <span
                        className={`absolute top-2 bottom-2 left-0 w-[3px] rounded-full bg-brand-gradient transition-opacity ${isActive ? "opacity-100" : "opacity-0"}`}
                        aria-hidden="true"
                      />
                      <span className={isActive ? "text-[#a5b4fc]" : "transition group-hover:text-[#a5b4fc]"}>{item.icon}</span>
                      {item.label}
                    </>
                  )}
                </NavLink>
              </div>
            )
          })}
        </nav>
        <div className={`${open ? "block" : "hidden"} relative border-t border-white/10 p-3 md:block`}>
          <div className="flex items-center gap-3 rounded-xl px-2 py-2">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-brand-gradient text-xs font-bold text-white">
              {initials}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-white">{user?.full_name}</p>
              <p className="truncate text-xs text-sidebar-ink/55">{user?.email}</p>
            </div>
            <button
              type="button"
              onClick={signOut}
              className="grid h-8 w-8 place-items-center rounded-lg text-sidebar-ink/60 transition hover:bg-white/10 hover:text-white"
              aria-label="Sign out"
              title="Sign out"
            >
              {icons.logout}
            </button>
          </div>
        </div>
      </aside>
      <div className="min-w-0">
        <header className="sticky top-0 z-20 flex items-center justify-between gap-3 border-b border-line bg-paper/80 px-4 py-3 backdrop-blur-xl sm:px-5 md:px-8">
          <div className="flex min-w-0 items-center gap-2 text-sm">
            <span className="hidden text-muted sm:inline">{kicker}</span>
            <span className="hidden text-muted/60 sm:inline">/</span>
            <span className="truncate font-semibold">{current?.label ?? detailLabel(location.pathname)}</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setPaletteOpen(true)}
              className="flex h-9 items-center gap-2 rounded-xl border border-line bg-foam px-3 text-sm text-muted shadow-card transition hover:border-brand/30 hover:text-brand"
              aria-label="Open command palette"
            >
              {icons.search}
              <span className="hidden sm:inline">Quick jump</span>
              <kbd className="hidden rounded-md border border-line px-1.5 py-0.5 text-[10px] font-semibold sm:inline">⌘K</kbd>
            </button>
            <ThemeToggle />
          </div>
        </header>
        <main id="main" className="px-4 py-6 sm:px-5 md:px-8 md:py-9">
          <div key={location.pathname} className="animate-rise">
            <ErrorBoundary resetKey={location.pathname}>
              <Outlet />
            </ErrorBoundary>
          </div>
        </main>
      </div>
      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} commands={commands} />
    </div>
  )
}

function detailLabel(path: string) {
  if (path.includes("/interview/")) return "Interview session"
  if (path.includes("/companies/")) return "Company"
  if (path.includes("/students/")) return "Student detail"
  return "Workspace"
}

export function StudentLayout() {
  return (
    <AppShell
      kicker="Student"
      items={[
        { to: "/app", label: "Overview", icon: icons.home, end: true, section: "Home" },
        { to: "/app/resume", label: "Resume analyzer", icon: icons.resume, section: "Practice" },
        { to: "/app/interview/hr", label: "HR interview", icon: icons.chat, section: "Practice" },
        { to: "/app/interview/technical", label: "Technical interview", icon: icons.chip, section: "Practice" },
        { to: "/app/coding", label: "Coding practice", icon: icons.code, section: "Practice" },
        { to: "/app/companies", label: "Companies", icon: icons.building, section: "Prepare" },
        { to: "/app/roadmap", label: "Roadmap", icon: icons.map, section: "Prepare" },
        { to: "/app/interview/history", label: "History", icon: icons.clock, section: "Prepare" },
        { to: "/app/profile", label: "Profile", icon: icons.user, section: "Account" },
      ]}
    />
  )
}

export function TpoLayout() {
  return (
    <AppShell
      kicker="Placement office"
      items={[
        { to: "/tpo", label: "Students", icon: icons.users, end: true, section: "Batch" },
        { to: "/tpo/profile", label: "Profile", icon: icons.user, section: "Account" },
      ]}
    />
  )
}
