import { useEffect, useRef, useState, type FormEvent } from "react"
import { Link, useParams } from "react-router"
import { Alert, Badge, Button, LoadingLine, Notice, PageHeader, ScoreBar, TextArea } from "../../components/ui"
import { errorMessage, formatDateTime, readStorage, writeStorage } from "../../lib/format"
import { api, ApiError } from "../../services/api"
import type { InterviewSession } from "../../types"

const dimensionLabels: Record<string, string> = {
  language_specificity: "Confidence-related language",
  communication: "Communication",
  relevance: "Relevance",
  professionalism: "Professionalism",
  correctness: "Correctness",
  depth: "Depth",
  clarity: "Clarity",
}

export function InterviewSessionPage() {
  const { sessionId } = useParams()
  const [session, setSession] = useState<InterviewSession | null>(null)
  const [loadError, setLoadError] = useState("")
  const [answer, setAnswer] = useState(() => (sessionId ? (readStorage(`interview-draft:${sessionId}`) ?? "") : ""))
  const [pending, setPending] = useState<"answer" | "finish" | null>(null)
  const [speaking, setSpeaking] = useState(false)
  const [error, setError] = useState("")
  const [notice, setNotice] = useState("")
  const [listening, setListening] = useState(false)
  const [speechNote, setSpeechNote] = useState("")
  const recognitionRef = useRef<BrowserSpeechRecognition | null>(null)
  const answerRef = useRef("")
  const openTurnRef = useRef<HTMLLIElement>(null)

  useEffect(() => {
    if (!sessionId) return
    api<InterviewSession>(`/api/v1/interviews/${sessionId}`)
      .then(setSession)
      .catch((caught) =>
        setLoadError(caught instanceof ApiError ? caught.message : "This interview could not be loaded."),
      )
  }, [sessionId])

  useEffect(() => {
    answerRef.current = answer
  }, [answer])

  // Stop any speech or listening when leaving the page.
  useEffect(
    () => () => {
      window.speechSynthesis?.cancel()
      recognitionRef.current?.stop()
    },
    [],
  )

  const openTurn = session?.turns?.find((turn) => turn.answer_text === null)

  function updateAnswer(value: string) {
    setAnswer(value)
    if (sessionId) writeStorage(`interview-draft:${sessionId}`, value || null)
  }

  function hearQuestion() {
    if (!openTurn) return
    if (speaking) {
      window.speechSynthesis?.cancel()
      setSpeaking(false)
      return
    }
    speakText(openTurn.question_text, () => setSpeaking(false))
    setSpeaking(true)
  }

  function toggleListening() {
    if (listening) {
      recognitionRef.current?.stop()
      setListening(false)
      return
    }
    const recognition = createRecognition()
    if (!recognition) {
      setSpeechNote("This browser cannot use the microphone. Type the answer instead.")
      return
    }
    window.speechSynthesis?.cancel()
    setSpeaking(false)
    const typedSoFar = answerRef.current.trim()
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0]?.transcript ?? "")
        .join(" ")
        .trim()
      if (!transcript) return
      updateAnswer(typedSoFar ? `${typedSoFar} ${transcript}` : transcript)
    }
    recognition.onerror = () => {
      setListening(false)
      setSpeechNote("The microphone could not be used. Check the browser permission, or type the answer.")
    }
    recognition.onend = () => setListening(false)
    recognitionRef.current = recognition
    setSpeechNote("")
    setListening(true)
    recognition.start()
  }

  async function submitAnswer(event: FormEvent) {
    event.preventDefault()
    if (!session || !answer.trim()) {
      setError("Write an answer before submitting.")
      return
    }
    recognitionRef.current?.stop()
    setListening(false)
    window.speechSynthesis?.cancel()
    setSpeaking(false)
    setPending("answer")
    setError("")
    setNotice("")
    try {
      const updated = await api<InterviewSession>(`/api/v1/interviews/${session.id}/answers`, {
        method: "POST",
        body: JSON.stringify({ answer: answer.trim() }),
      })
      setSession(updated)
      updateAnswer("")
      setNotice("Your answer and its evaluation were saved.")
      window.requestAnimationFrame(() => openTurnRef.current?.scrollIntoView({ behavior: "smooth", block: "center" }))
    } catch (caught) {
      setError(errorMessage(caught, "The answer could not be saved."))
    } finally {
      setPending(null)
    }
  }

  async function finish() {
    if (!session) return
    setPending("finish")
    setError("")
    try {
      const updated = await api<InterviewSession>(`/api/v1/interviews/${session.id}/complete`, { method: "POST" })
      setSession(updated)
      setNotice("The interview result was saved.")
      window.scrollTo({ top: 0, behavior: "smooth" })
    } catch (caught) {
      setError(errorMessage(caught, "The interview could not be finished."))
    } finally {
      setPending(null)
    }
  }

  const title = session?.kind === "technical" ? `${session.topic} interview` : "HR interview"
  const answered = session?.turns?.filter((turn) => turn.answer_text !== null).length ?? 0

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        kicker={session?.status === "completed" ? "Result" : "Live interview"}
        title={session ? title : "Interview"}
        body={
          session?.kind === "hr"
            ? "Confidence-related language describes the specificity of the written answer. It is not a voice or emotion score."
            : "Topic scores come from the stored answer evaluations. Weak areas are the dimensions below 60, plus the topic when the overall result is below 60."
        }
      />
      {loadError ? (
        <div className="mt-6">
          <Alert>{loadError}</Alert>
        </div>
      ) : null}
      {session === null && !loadError ? <p className="mt-6 text-sm text-muted">Loading the interview…</p> : null}
      {error ? (
        <div className="mt-6">
          <Alert>{error}</Alert>
        </div>
      ) : null}
      {notice ? (
        <div className="mt-6">
          <Notice>{notice}</Notice>
        </div>
      ) : null}

      {session ? (
        <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
          <Badge className={session.status === "completed" ? "border-pine/20 bg-pine/10 text-pine" : "border-navy/20 bg-navy/5 text-navy"}>
            {session.status === "completed" ? "Completed" : "In progress"}
          </Badge>
          {session.difficulty ? <Badge className="border-line bg-foam capitalize text-ink">{session.difficulty}</Badge> : null}
          <span className="text-muted">
            {answered} answered · started {formatDateTime(session.started_at)}
          </span>
        </div>
      ) : null}

      {session?.status === "completed" ? (
        <section className="mt-8 rounded-lg border border-line bg-foam p-5">
          <p className="text-xs font-semibold tracking-wider text-muted uppercase">Overall result</p>
          <p className="mt-1 font-serif text-5xl text-navy">
            {session.overall_score === null ? "—" : Math.round(session.overall_score)}
            <span className="text-2xl text-muted">/100</span>
          </p>
          <div className="mt-4">
            <ScoreBar label="Overall score" value={session.overall_score} />
          </div>
          <div className="mt-4 grid gap-3">
            {Object.entries(session.dimension_scores ?? {}).map(([key, value]) => (
              <ScoreBar key={key} label={dimensionLabels[key] ?? key} value={value} />
            ))}
          </div>
          <StringList title="Strengths" items={session.strengths ?? []} />
          <StringList title="Improvements" items={session.improvements ?? []} />
          <StringList title="Weak areas" items={session.weak_areas ?? []} />
        </section>
      ) : null}

      <ol className="mt-8 space-y-4">
        {session?.turns?.map((turn) => (
          <li
            key={turn.id}
            ref={turn.id === openTurn?.id ? openTurnRef : undefined}
            className={`scroll-mt-6 rounded-lg border bg-foam p-4 ${turn.id === openTurn?.id ? "border-navy/40 ring-2 ring-navy/10" : "border-line"}`}
          >
            <p className="text-xs tracking-wide text-muted uppercase">
              Question {turn.turn_index}
              {turn.is_follow_up ? " · Follow-up" : ""}
              {turn.id === openTurn?.id ? " · Your turn" : ""}
            </p>
            <p className="mt-2 leading-relaxed">{turn.question_text}</p>
            {turn.answer_text ? (
              <p className="mt-3 border-l-2 border-line pl-3 text-sm leading-relaxed text-muted">{turn.answer_text}</p>
            ) : null}
            {turn.evaluation ? (
              <div className="mt-3 border-t border-line pt-3 text-sm">
                <p>{turn.evaluation.feedback}</p>
                <p className="mt-2 text-muted">
                  {Object.entries(turn.evaluation.scores)
                    .map(([key, value]) => `${dimensionLabels[key] ?? key} ${value}`)
                    .join(" · ")}
                </p>
              </div>
            ) : null}
          </li>
        ))}
      </ol>

      {session?.status === "in_progress" && openTurn ? (
        <form onSubmit={submitAnswer} className="mt-6 grid gap-4" aria-busy={pending !== null}>
          <TextArea
            id="answer"
            label="Your answer"
            value={answer}
            disabled={pending !== null}
            onChange={(event) => updateAnswer(event.target.value)}
            placeholder="Type here, or use Speak answer and then edit the text."
            hint="Your draft is kept in this browser until you submit."
          />
          {speechNote ? <p className="text-sm text-muted">{speechNote}</p> : null}
          {listening ? (
            <p className="flex items-center gap-2 text-sm text-clay" role="status">
              <span className="h-2 w-2 animate-pulse rounded-full bg-clay" aria-hidden="true" />
              Listening… speak your answer, then press Stop speaking.
            </p>
          ) : null}
          {pending === "answer" ? (
            <LoadingLine label="Evaluating your answer…" detail="The interviewer is scoring it and choosing the next question." />
          ) : null}
          {pending === "finish" ? <LoadingLine label="Scoring the whole interview…" /> : null}
          <div className="flex flex-wrap gap-3">
            <Button type="submit" pending={pending === "answer"} pendingLabel="Evaluating…" disabled={pending !== null}>
              Submit answer
            </Button>
            <Button variant="secondary" onClick={hearQuestion} aria-pressed={speaking} disabled={pending !== null}>
              {speaking ? "Stop reading" : "Read question aloud"}
            </Button>
            <Button variant="secondary" onClick={toggleListening} aria-pressed={listening} disabled={pending !== null}>
              {listening ? "Stop speaking" : "Speak answer"}
            </Button>
            <Button
              variant="secondary"
              disabled={!session.can_finish || pending !== null}
              pending={pending === "finish"}
              pendingLabel="Scoring…"
              onClick={finish}
              title={session.can_finish ? undefined : "Answer at least one question first"}
            >
              Finish and score
            </Button>
          </div>
        </form>
      ) : null}
      {session?.status === "in_progress" && !openTurn ? (
        <div className="mt-6 grid gap-3">
          {pending === "finish" ? <LoadingLine label="Scoring the whole interview…" /> : null}
          <div>
            <Button pending={pending === "finish"} pendingLabel="Scoring…" disabled={!session.can_finish} onClick={finish}>
              Finish and score
            </Button>
          </div>
        </div>
      ) : null}
      <p className="mt-8 text-sm">
        <Link to="/app/interview/history" className="font-medium text-navy">
          Back to history
        </Link>
      </p>
    </div>
  )
}

type SpeechResult = { results: ArrayLike<ArrayLike<{ transcript: string }>> }

interface BrowserSpeechRecognition {
  lang: string
  continuous: boolean
  interimResults: boolean
  onresult: ((event: SpeechResult) => void) | null
  onerror: (() => void) | null
  onend: (() => void) | null
  start: () => void
  stop: () => void
}

function createRecognition(): BrowserSpeechRecognition | null {
  const browser = window as Window & {
    SpeechRecognition?: new () => BrowserSpeechRecognition
    webkitSpeechRecognition?: new () => BrowserSpeechRecognition
  }
  const Recognition = browser.SpeechRecognition ?? browser.webkitSpeechRecognition
  if (!Recognition) return null
  const recognition = new Recognition()
  recognition.lang = "en-IN"
  recognition.continuous = true
  recognition.interimResults = true
  return recognition
}

function speakText(text: string, onDone: () => void) {
  if (!window.speechSynthesis) {
    onDone()
    return
  }
  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = "en-IN"
  utterance.rate = 1
  utterance.onend = onDone
  utterance.onerror = onDone
  window.speechSynthesis.speak(utterance)
}

function StringList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="mt-6">
      <h2 className="font-medium">{title}</h2>
      {items.length === 0 ? <p className="mt-1 text-sm text-muted">None saved.</p> : null}
      {items.length > 0 ? (
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-relaxed">
          {items.map((item, index) => (
            <li key={`${index}-${item}`}>{item}</li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}
