import { useState, type ReactNode } from "react"
import { Link } from "react-router"
import { ThemeToggle } from "../components/ThemeToggle"
import { icons } from "../components/icons"
import { Logo, ProgressRing } from "../components/ui"
import { BRAND, BRAND_TAGLINE } from "../lib/theme"

const features: { icon: ReactNode; title: string; body: string; tint: string }[] = [
  {
    icon: icons.resume,
    title: "Resume analyzer",
    body: "Upload a PDF or DOCX and check it against any role. ATS-style score, skill match, missing keywords and formatting fixes.",
    tint: "from-indigo-500/20 to-violet-500/5 text-brand",
  },
  {
    icon: icons.chat,
    title: "AI mock interviews",
    body: "Multi-turn HR and technical rounds that follow up on your answers, scored on clarity, depth and confidence-related language.",
    tint: "from-violet-500/20 to-fuchsia-500/5 text-violet-500",
  },
  {
    icon: icons.code,
    title: "Coding practice",
    body: "36 problems in Python, Java and C++ with hidden tests, a real code runner and an AI review of complexity and style.",
    tint: "from-cyan-500/20 to-sky-500/5 text-cyan-600 dark:text-cyan-400",
  },
  {
    icon: icons.building,
    title: "Company prep",
    body: "Curated and AI-generated questions for Accenture, Amazon, Infosys, TCS and more, grouped by round.",
    tint: "from-emerald-500/20 to-teal-500/5 text-pine",
  },
  {
    icon: icons.target,
    title: "Readiness estimate",
    body: "A machine-learning model turns your scores into a placement readiness estimate, with a what-if simulator.",
    tint: "from-amber-500/20 to-orange-500/5 text-gold",
  },
  {
    icon: icons.map,
    title: "Personal roadmap",
    body: "A 7-day plan built from your weak areas. Tick items off and watch your preparation gap shrink.",
    tint: "from-rose-500/20 to-pink-500/5 text-clay",
  },
]

const steps = [
  ["Create your profile", "Sign up with your college email, branch and roll number. TPO accounts verify with an emailed code."],
  ["Practice with AI feedback", "Resume, HR, technical and coding scores all land on one dashboard, with specific suggestions."],
  ["Close the gap", "Readiness, a roadmap and a one-click PDF report show exactly what to improve before the drive."],
]

const faqs = [
  [
    "Is the AI feedback made up when the model is unavailable?",
    "No. If the AI service is not configured or fails, the app says so clearly. It never shows a placeholder score.",
  ],
  [
    "Can the placement office read my interview answers?",
    "No. The TPO sees scores, readiness and weak areas for the batch, but interview transcripts stay private to you.",
  ],
  [
    "Which languages can I code in?",
    "Python, Java and C++. Code runs against visible and hidden test cases, then gets an AI review.",
  ],
  [
    "How accurate is the readiness estimate?",
    "It is a proof of concept trained on synthetic data, because real placement outcomes were not available. Treat it as a guide, not a verdict.",
  ],
]

export function LandingPage() {
  return (
    <div className="min-h-screen overflow-x-hidden bg-paper text-ink">
      <SiteHeader />
      <main>
        <Hero />
        <StatsStrip />
        <section id="features" className="mx-auto max-w-6xl scroll-mt-24 px-5 py-20">
          <SectionHeading kicker="Everything in one place" title="Built for the whole placement season" />
          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <article
                key={feature.title}
                className="group relative overflow-hidden rounded-3xl border border-line bg-foam p-6 shadow-card transition duration-300 hover:-translate-y-1 hover:shadow-lift"
              >
                <div
                  className="pointer-events-none absolute -top-20 -right-20 h-40 w-40 rounded-full bg-brand-gradient opacity-0 blur-3xl transition duration-500 group-hover:opacity-20"
                  aria-hidden="true"
                />
                <span className={`grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br ${feature.tint}`}>
                  {feature.icon}
                </span>
                <h3 className="mt-5 font-serif text-xl font-bold">{feature.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">{feature.body}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="how" className="scroll-mt-24 border-y border-line bg-foam/60">
          <div className="mx-auto max-w-6xl px-5 py-20">
            <SectionHeading kicker="How it works" title="From sign-up to offer-ready in three steps" />
            <ol className="relative mt-12 grid gap-6 md:grid-cols-3">
              <div className="absolute top-7 right-[16%] left-[16%] hidden h-px bg-gradient-to-r from-transparent via-brand/40 to-transparent md:block" aria-hidden="true" />
              {steps.map(([title, body], index) => (
                <li key={title} className="relative text-center">
                  <span className="relative mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-brand-gradient font-serif text-xl font-bold text-white shadow-glow">
                    {index + 1}
                  </span>
                  <h3 className="mt-5 font-serif text-xl font-bold">{title}</h3>
                  <p className="mx-auto mt-2 max-w-xs text-sm leading-relaxed text-muted">{body}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section id="tpo" className="mx-auto max-w-6xl scroll-mt-24 px-5 py-20">
          <div className="relative overflow-hidden rounded-[2rem] bg-sidebar p-8 text-white shadow-lift ring-1 ring-white/5 sm:p-12">
            <div className="pointer-events-none absolute -top-24 -right-16 h-80 w-80 rounded-full bg-brand-gradient opacity-40 blur-3xl" aria-hidden="true" />
            <div className="pointer-events-none absolute inset-0 bg-grid opacity-[0.06]" aria-hidden="true" />
            <div className="relative grid items-center gap-10 lg:grid-cols-2">
              <div>
                <p className="text-xs font-semibold tracking-[0.16em] text-white/60 uppercase">For the placement office</p>
                <h2 className="mt-3 font-serif text-3xl leading-tight font-bold sm:text-4xl">
                  See who needs help, <span className="text-brand-gradient">before the drive</span>
                </h2>
                <ul className="mt-6 space-y-3 text-sm text-white/80">
                  {[
                    "Filter the batch by branch or readiness below 60%",
                    "Open any student for scores and weak areas",
                    "Export the batch to CSV for the department",
                    "Transcripts stay private to the student",
                  ].map((item) => (
                    <li key={item} className="flex items-start gap-3">
                      <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-white/15 text-[#a5f3fc]">
                        {icons.check}
                      </span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
              <BatchPreview />
            </div>
          </div>
        </section>

        <section id="faq" className="mx-auto max-w-3xl scroll-mt-24 px-5 pb-20">
          <SectionHeading kicker="Questions" title="Good to know" />
          <div className="mt-10 space-y-3">
            {faqs.map(([question, answer]) => (
              <Faq key={question} question={question} answer={answer} />
            ))}
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-5 pb-20">
          <div className="relative overflow-hidden rounded-[2rem] border border-line bg-foam p-10 text-center shadow-card sm:p-14">
            <div className="pointer-events-none absolute inset-0 bg-grid opacity-60 [mask-image:radial-gradient(60%_60%_at_50%_50%,black,transparent)]" aria-hidden="true" />
            <div className="relative">
              <h2 className="font-serif text-3xl font-bold sm:text-4xl">
                Your next interview starts <span className="text-brand-gradient">here</span>
              </h2>
              <p className="mx-auto mt-3 max-w-lg text-muted">
                Free for students. Create an account with your college email and get your first score in five minutes.
              </p>
              <div className="mt-8 flex flex-wrap justify-center gap-3">
                <PrimaryLink to="/register">Create a free account</PrimaryLink>
                <Link
                  to="/login"
                  className="inline-flex items-center rounded-xl border border-line bg-foam px-5 py-3 text-sm font-semibold shadow-card transition hover:border-brand/30 hover:text-brand"
                >
                  I already have one
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>
      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-5 py-8 text-sm text-muted">
          <Logo name={BRAND} size={28} className="text-ink" />
          <p>{BRAND_TAGLINE} · B.Tech CSE (Data Science) capstone</p>
        </div>
      </footer>
    </div>
  )
}

function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-line/60 bg-paper/75 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-3.5">
        <Link to="/" aria-label={`${BRAND} home`}>
          <Logo name={BRAND} />
        </Link>
        <nav className="hidden items-center gap-7 text-sm font-medium text-muted md:flex" aria-label="Sections">
          <a href="#features" className="transition hover:text-ink">Features</a>
          <a href="#how" className="transition hover:text-ink">How it works</a>
          <a href="#tpo" className="transition hover:text-ink">For TPOs</a>
          <a href="#faq" className="transition hover:text-ink">FAQ</a>
        </nav>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Link to="/login" className="hidden px-3 py-2 text-sm font-semibold transition hover:text-brand sm:inline">
            Sign in
          </Link>
          <Link
            to="/register"
            className="rounded-xl bg-navy px-4 py-2 text-sm font-semibold text-onbrand shadow-glow transition hover:-translate-y-px hover:bg-navy-soft"
          >
            Get started
          </Link>
        </div>
      </div>
    </header>
  )
}

function Hero() {
  return (
    <section className="relative">
      <div className="pointer-events-none absolute inset-0 bg-grid [mask-image:radial-gradient(70%_60%_at_50%_0%,black,transparent)]" aria-hidden="true" />
      <div className="pointer-events-none absolute -top-40 left-1/2 h-[32rem] w-[60rem] -translate-x-1/2 rounded-full bg-brand-gradient opacity-20 blur-[120px]" aria-hidden="true" />
      <div className="relative mx-auto grid max-w-6xl items-center gap-14 px-5 pt-16 pb-20 lg:grid-cols-[1.05fr_0.95fr] lg:pt-24">
        <div className="animate-rise">
          <p className="inline-flex items-center gap-2 rounded-full border border-brand/20 bg-foam/80 px-3 py-1.5 text-xs font-semibold text-brand shadow-card backdrop-blur">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand opacity-60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-brand" />
            </span>
            AI-powered campus placement prep
          </p>
          <h1 className="mt-6 font-serif text-5xl leading-[1.05] font-extrabold tracking-tight sm:text-6xl lg:text-[4.2rem]">
            Walk into every interview <span className="text-brand-gradient">ready.</span>
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-relaxed text-muted">
            Resume scoring, AI mock interviews, coding practice and a readiness estimate in one workspace. The placement
            office sees who needs help, without reading your transcripts.
          </p>
          <div className="mt-9 flex flex-wrap items-center gap-3">
            <PrimaryLink to="/register">Start practicing free</PrimaryLink>
            <a
              href="#features"
              className="inline-flex items-center gap-2 rounded-xl border border-line bg-foam px-5 py-3 text-sm font-semibold shadow-card transition hover:border-brand/30 hover:text-brand"
            >
              See what's inside
            </a>
          </div>
          <div className="mt-9 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-muted">
            {["Free for students", "Python · Java · C++", "Private transcripts"].map((item) => (
              <span key={item} className="flex items-center gap-1.5">
                <span className="text-pine">{icons.check}</span>
                {item}
              </span>
            ))}
          </div>
        </div>
        <ProductPreview />
      </div>
    </section>
  )
}

/** Illustrative dashboard mock-up built from real UI pieces (not a screenshot). */
function ProductPreview() {
  return (
    <div className="relative mx-auto w-full max-w-md animate-rise [animation-delay:120ms] lg:max-w-none" aria-hidden="true">
      <div className="absolute -inset-4 rounded-[2.2rem] bg-brand-gradient opacity-25 blur-2xl" />
      <div className="relative rounded-[1.75rem] border border-line bg-foam/90 p-5 shadow-lift backdrop-blur-xl">
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-clay/60" />
          <span className="h-2.5 w-2.5 rounded-full bg-gold/60" />
          <span className="h-2.5 w-2.5 rounded-full bg-pine/60" />
          <span className="ml-3 h-5 flex-1 rounded-md bg-paper" />
        </div>
        <div className="mt-5 flex items-center gap-5 rounded-2xl bg-sidebar p-5 text-white">
          <ProgressRing value={78} size={104} stroke={10} sublabel="Ready" tone="light" />
          <div>
            <p className="text-xs text-white/60">Placement readiness</p>
            <p className="mt-1 font-serif text-lg leading-snug font-bold">Strong in coding. Polish HR answers next.</p>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-3 gap-3">
          {[
            ["Resume", 84, "bg-pine"],
            ["HR", 62, "bg-gold"],
            ["Coding", 91, "bg-navy"],
          ].map(([label, value, bar]) => (
            <div key={label as string} className="rounded-xl border border-line bg-paper/60 p-3">
              <p className="text-[11px] text-muted">{label}</p>
              <p className="font-serif text-xl font-bold">{value}</p>
              <div className="mt-2 h-1.5 rounded-full bg-line">
                <div className={`h-1.5 rounded-full ${bar}`} style={{ width: `${value}%` }} />
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 flex h-24 items-end gap-2 rounded-xl border border-line bg-paper/60 p-3">
          {[38, 52, 47, 63, 58, 72, 69, 81, 78, 88].map((height, index) => (
            <div
              key={index}
              className="flex-1 rounded-t-md bg-gradient-to-t from-indigo-500 to-cyan-400 opacity-80"
              style={{ height: `${height}%` }}
            />
          ))}
        </div>
      </div>
      <div className="absolute -bottom-6 -left-4 hidden animate-float rounded-2xl border border-line bg-foam p-3.5 shadow-lift sm:block">
        <p className="flex items-center gap-2 text-xs font-semibold text-pine">
          <span className="grid h-6 w-6 place-items-center rounded-full bg-pine/10">{icons.check}</span>
          All 12 tests passed
        </p>
      </div>
      <div className="absolute -top-5 -right-3 hidden animate-float rounded-2xl border border-line bg-foam p-3.5 shadow-lift [animation-delay:1.5s] sm:block">
        <p className="flex items-center gap-2 text-xs font-semibold text-brand">
          <span className="grid h-6 w-6 place-items-center rounded-full bg-brand/10">{icons.spark}</span>
          ATS score +18
        </p>
      </div>
    </div>
  )
}

function StatsStrip() {
  const stats = [
    ["36", "coding problems"],
    ["9", "company tracks"],
    ["3", "languages"],
    ["4", "AI-scored skills"],
  ]
  return (
    <section className="mx-auto max-w-6xl px-5">
      <div className="grid grid-cols-2 gap-px overflow-hidden rounded-3xl border border-line bg-line shadow-card md:grid-cols-4">
        {stats.map(([value, label]) => (
          <div key={label} className="bg-foam px-6 py-7 text-center">
            <p className="font-serif text-4xl font-extrabold text-brand-gradient">{value}</p>
            <p className="mt-1 text-sm text-muted">{label}</p>
          </div>
        ))}
      </div>
    </section>
  )
}

function BatchPreview() {
  const rows = [
    ["Aarav S.", "CSE", 82],
    ["Diya R.", "CSE - DS", 67],
    ["Kiran M.", "ECE", 54],
    ["Meera P.", "IT", 76],
  ] as const
  return (
    <div className="rounded-2xl bg-white/[0.06] p-4 ring-1 ring-white/10 backdrop-blur" aria-hidden="true">
      <div className="mb-3 flex items-center justify-between text-xs text-white/60">
        <span>Batch 2027 · 4 students</span>
        <span className="rounded-full bg-white/10 px-2 py-0.5">Readiness &lt; 60%</span>
      </div>
      <div className="space-y-2">
        {rows.map(([name, branch, value]) => (
          <div key={name} className="flex items-center gap-3 rounded-xl bg-white/[0.04] px-3 py-2.5">
            <span className="grid h-8 w-8 place-items-center rounded-full bg-brand-gradient text-[11px] font-bold">
              {name.slice(0, 1)}
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold">{name}</p>
              <p className="text-[11px] text-white/50">{branch}</p>
            </div>
            <div className="w-24">
              <div className="h-1.5 rounded-full bg-white/10">
                <div
                  className={`h-1.5 rounded-full ${value < 60 ? "bg-rose-400" : value < 75 ? "bg-amber-300" : "bg-emerald-400"}`}
                  style={{ width: `${value}%` }}
                />
              </div>
            </div>
            <span className="w-9 text-right text-sm font-semibold tabular-nums">{value}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function Faq({ question, answer }: { question: string; answer: string }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="rounded-2xl border border-line bg-foam shadow-card">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left font-semibold"
      >
        {question}
        <span className={`grid h-7 w-7 shrink-0 place-items-center rounded-full bg-brand/10 text-brand transition-transform duration-300 ${open ? "rotate-45" : ""}`}>
          +
        </span>
      </button>
      <div className={`grid transition-all duration-300 ${open ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"}`}>
        <p className="overflow-hidden px-5 text-sm leading-relaxed text-muted">
          <span className="block pb-4">{answer}</span>
        </p>
      </div>
    </div>
  )
}

function SectionHeading({ kicker, title }: { kicker: string; title: string }) {
  return (
    <div className="text-center">
      <p className="text-xs font-semibold tracking-[0.16em] text-brand uppercase">{kicker}</p>
      <h2 className="mx-auto mt-3 max-w-2xl font-serif text-3xl leading-tight font-bold sm:text-[2.6rem]">{title}</h2>
    </div>
  )
}

function PrimaryLink({ to, children }: { to: string; children: ReactNode }) {
  return (
    <Link
      to={to}
      className="group inline-flex items-center gap-2 rounded-xl bg-brand-gradient px-5 py-3 text-sm font-semibold text-white shadow-glow transition hover:-translate-y-0.5 hover:shadow-lift"
    >
      {children}
      <span className="transition-transform group-hover:translate-x-1">{icons.arrow}</span>
    </Link>
  )
}
