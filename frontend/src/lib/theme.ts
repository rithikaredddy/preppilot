import { useEffect, useMemo, useState } from "react"

/** Product name shown across the app. Change it here to rebrand. */
export const BRAND = "PrepPilot"
export const BRAND_TAGLINE = "AI Interview Preparation Platform"

export type Theme = "light" | "dark"

const STORAGE_KEY = "theme"
const EVENT = "themechange"

export function currentTheme(): Theme {
  return document.documentElement.classList.contains("dark") ? "dark" : "light"
}

export function setTheme(theme: Theme) {
  document.documentElement.classList.toggle("dark", theme === "dark")
  try {
    localStorage.setItem(STORAGE_KEY, theme)
  } catch {
    // Private windows can block storage; the theme still applies for this visit.
  }
  window.dispatchEvent(new Event(EVENT))
}

export function useTheme(): [Theme, (theme: Theme) => void] {
  const [theme, setLocal] = useState<Theme>(() => currentTheme())
  useEffect(() => {
    const sync = () => setLocal(currentTheme())
    window.addEventListener(EVENT, sync)
    return () => window.removeEventListener(EVENT, sync)
  }, [])
  return [theme, setTheme]
}

/** Resolved token colours for charts, which need real colour values rather than CSS variables. */
export function useChartColors() {
  const [theme] = useTheme()
  return useMemo(() => {
    const style = getComputedStyle(document.documentElement)
    const value = (name: string) => style.getPropertyValue(name).trim()
    return {
      theme,
      brand: value("--color-navy"),
      success: value("--color-pine"),
      danger: value("--color-clay"),
      warning: value("--color-gold"),
      grid: value("--color-line"),
      text: value("--color-muted"),
      surface: value("--color-foam"),
      ink: value("--color-ink"),
      violet: "#8b5cf6",
      cyan: "#06b6d4",
    }
  }, [theme])
}
