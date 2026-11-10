import { useTheme } from "../lib/theme"
import { icons } from "./icons"

export function ThemeToggle({ className = "" }: { className?: string }) {
  const [theme, setTheme] = useTheme()
  const dark = theme === "dark"
  return (
    <button
      type="button"
      onClick={() => setTheme(dark ? "light" : "dark")}
      className={`grid h-9 w-9 place-items-center rounded-xl border border-line bg-foam text-muted shadow-card transition hover:border-brand/30 hover:text-brand ${className}`}
      aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
      title={dark ? "Light theme" : "Dark theme"}
    >
      <span key={theme} className="animate-fade">
        {dark ? icons.sun : icons.moon}
      </span>
    </button>
  )
}
