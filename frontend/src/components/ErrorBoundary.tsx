import { Component, type ErrorInfo, type ReactNode } from "react"

type Props = { children: ReactNode; resetKey?: string }
type State = { error: Error | null; resetKey?: string }

/** Shows a recoverable message instead of a blank screen when a page crashes. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null, resetKey: this.props.resetKey }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { error }
  }

  static getDerivedStateFromProps(props: Props, state: State): Partial<State> | null {
    // Navigating to another page clears the error.
    if (props.resetKey !== state.resetKey) return { error: null, resetKey: props.resetKey }
    return null
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Page crashed:", error, info.componentStack)
  }

  render() {
    if (!this.state.error) return this.props.children
    return (
      <div role="alert" className="mx-auto max-w-xl rounded-2xl border border-clay/30 bg-foam p-6 shadow-card">
        <h2 className="font-serif text-2xl font-bold">Something went wrong on this page</h2>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          Your saved work is safe. Try again, or reload the page if it keeps happening.
        </p>
        <p className="mt-3 rounded-lg bg-paper px-3 py-2 font-mono text-xs break-words text-clay">
          {this.state.error.message}
        </p>
        <div className="mt-5 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => this.setState({ error: null })}
            className="rounded-xl bg-navy px-4 py-2.5 text-sm font-semibold text-onbrand hover:bg-navy-soft"
          >
            Try again
          </button>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="rounded-xl border border-line bg-foam px-4 py-2.5 text-sm font-semibold hover:text-brand"
          >
            Reload page
          </button>
        </div>
      </div>
    )
  }
}
