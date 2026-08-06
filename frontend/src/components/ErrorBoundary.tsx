import { Component, type ErrorInfo, type ReactNode } from "react"

interface Props { children: ReactNode }
interface State { error: Error | null }

/** Prevents an unexpected rendering error from leaving members on a blank page. */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("SSGA interface error", error, info.componentStack)
  }

  render() {
    if (!this.state.error) return this.props.children
    return (
      <main className="error-boundary" role="alert">
        <article>
          <img src="/icon.svg" width="48" height="48" alt="SSGA HOLDINGS" />
          <h1>We could not display this page</h1>
          <p>The application encountered an unexpected interface error. Your account and transaction data are safe.</p>
          <code>{this.state.error.message}</code>
          <button className="btn primary" onClick={() => window.location.assign("/dashboard")}>Return to overview</button>
        </article>
      </main>
    )
  }
}
