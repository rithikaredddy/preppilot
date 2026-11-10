import { Link } from "react-router"

export function LandingPage() {
  return (
    <div className="min-h-screen bg-paper">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5">
        <p className="font-serif text-2xl text-navy">Interview Prep</p>
        <nav className="flex items-center gap-3 text-sm">
          <Link to="/login" className="px-3 py-2 font-medium text-navy">
            Sign in
          </Link>
          <Link to="/register" className="rounded-md bg-navy px-3 py-2 font-semibold text-foam">
            Create account
          </Link>
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-5 pt-10 pb-20">
        <p className="text-sm font-medium tracking-wide text-muted uppercase">Campus placement platform</p>
        <h1 className="mt-3 max-w-3xl font-serif text-5xl leading-tight text-ink md:text-6xl">
          One workspace for students and the placement office.
        </h1>
        <p className="mt-5 max-w-2xl text-lg leading-relaxed text-muted">
          Students register with a college email, branch, and roll number. Resume review, mock interviews,
          coding practice, a readiness estimate, and a study plan all live in one workspace. The placement
          office sees batch readiness without interview transcripts.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link to="/register" className="rounded-md bg-navy px-4 py-2.5 text-sm font-semibold text-foam">
            Create a student account
          </Link>
          <Link to="/login" className="rounded-md border border-line bg-foam px-4 py-2.5 text-sm font-semibold">
            Sign in
          </Link>
        </div>
        <section className="mt-14 grid gap-4 md:grid-cols-2">
          <article className="rounded-lg border border-line bg-foam p-6">
            <p className="text-sm font-medium text-muted">For students</p>
            <h2 className="mt-2 font-serif text-3xl">Keep your placement profile</h2>
            <p className="mt-3 leading-relaxed text-muted">
              Sign up with your name, email, branch, and roll number. Upload a resume, practice interviews,
              solve coding problems, and download one report before the real interview.
            </p>
          </article>
          <article className="rounded-lg border border-line bg-navy p-6 text-foam">
            <p className="text-sm font-medium text-foam/70">For the TPO</p>
            <h2 className="mt-2 font-serif text-3xl">See who needs help</h2>
            <p className="mt-3 leading-relaxed text-foam/80">
              Filter the batch by branch or by readiness below 60%. Open one student for scores and weak areas.
              Transcripts stay private.
            </p>
          </article>
        </section>
        <ol className="mt-8 grid gap-4 md:grid-cols-3">
          {[
            ["01", "Create an account", "Choose student, or TPO and confirm the code sent to that email."],
            ["02", "Practice in one place", "Resume, HR, technical, and coding scores land on the same dashboard."],
            ["03", "See the lever", "Readiness, a what-if slider, a roadmap, and a PDF report show what to improve."],
          ].map(([step, title, copy]) => (
            <li key={step} className="rounded-lg border border-line bg-foam p-5">
              <p className="font-serif text-2xl text-navy">{step}</p>
              <h3 className="mt-3 font-semibold">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{copy}</p>
            </li>
          ))}
        </ol>
      </main>
    </div>
  )
}
