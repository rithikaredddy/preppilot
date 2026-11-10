import { useEffect, useMemo, useRef, useState, type ReactNode } from "react"
import { useNavigate } from "react-router"
import { setTheme, currentTheme } from "../lib/theme"
import { icons } from "./icons"

export type Command = { label: string; hint?: string; icon: ReactNode; to?: string; run?: () => void }

/** Ctrl/⌘+K launcher for jumping between pages and quick actions. */
export function CommandPalette({
  open,
  onClose,
  commands,
}: {
  open: boolean
  onClose: () => void
  commands: Command[]
}) {
  const navigate = useNavigate()
  const [query, setQuery] = useState("")
  const [active, setActive] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  const all = useMemo<Command[]>(
    () => [
      ...commands,
      {
        label: "Toggle dark mode",
        hint: "Appearance",
        icon: icons.moon,
        run: () => setTheme(currentTheme() === "dark" ? "light" : "dark"),
      },
    ],
    [commands],
  )
  const results = useMemo(() => {
    const term = query.trim().toLowerCase()
    if (!term) return all
    return all.filter((item) => `${item.label} ${item.hint ?? ""}`.toLowerCase().includes(term))
  }, [all, query])

  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  if (!open) return null

  function choose(item: Command | undefined) {
    if (!item) return
    onClose()
    setQuery("")
    setActive(0)
    if (item.to) navigate(item.to)
    item.run?.()
  }

  function close() {
    onClose()
    setQuery("")
    setActive(0)
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-start bg-ink/40 px-4 pt-[12vh] backdrop-blur-sm animate-fade" onMouseDown={close}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Command palette"
        className="mx-auto w-full max-w-lg overflow-hidden rounded-2xl border border-line bg-foam shadow-lift animate-rise"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="flex items-center gap-3 border-b border-line px-4">
          <span className="text-muted">{icons.search}</span>
          <input
            ref={inputRef}
            value={query}
            onChange={(event) => {
              setQuery(event.target.value)
              setActive(0)
            }}
            onKeyDown={(event) => {
              if (event.key === "Escape") close()
              if (event.key === "ArrowDown") {
                event.preventDefault()
                setActive((current) => Math.min(current + 1, results.length - 1))
              }
              if (event.key === "ArrowUp") {
                event.preventDefault()
                setActive((current) => Math.max(current - 1, 0))
              }
              if (event.key === "Enter") choose(results[active])
            }}
            placeholder="Jump to a page or action…"
            aria-label="Search pages and actions"
            className="h-14 w-full bg-transparent text-sm text-ink outline-none placeholder:text-muted"
          />
          <kbd className="rounded-md border border-line px-1.5 py-0.5 text-[10px] font-semibold text-muted">ESC</kbd>
        </div>
        <ul className="max-h-80 overflow-y-auto p-2" role="listbox" aria-label="Results">
          {results.length === 0 ? <li className="px-3 py-6 text-center text-sm text-muted">No matches.</li> : null}
          {results.map((item, index) => (
            <li key={item.label} role="option" aria-selected={index === active}>
              <button
                type="button"
                onMouseEnter={() => setActive(index)}
                onClick={() => choose(item)}
                className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm transition ${
                  index === active ? "bg-brand/10 text-brand" : "text-ink"
                }`}
              >
                <span className={index === active ? "text-brand" : "text-muted"}>{item.icon}</span>
                <span className="flex-1 font-medium">{item.label}</span>
                {item.hint ? <span className="text-xs text-muted">{item.hint}</span> : null}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
