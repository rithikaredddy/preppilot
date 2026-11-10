import { lazy, Suspense, type ReactNode } from "react"
import { BrowserRouter, Link, Route, Routes } from "react-router"
import { GuestOnly, RequireAuth, StatusScreen } from "./components/guards"
import { Spinner } from "./components/ui"
import { AuthProvider } from "./context/AuthContext"
import { StudentLayout, TpoLayout } from "./layouts/AppShell"
import { LandingPage } from "./pages/LandingPage"
import { LoginPage } from "./pages/LoginPage"
import { RegisterPage } from "./pages/RegisterPage"

// Pages are loaded on demand so charts and the code editor are not in the first download.
const ForgotPasswordPage = lazy(() => import("./pages/PasswordPages").then((m) => ({ default: m.ForgotPasswordPage })))
const ResetPasswordPage = lazy(() => import("./pages/PasswordPages").then((m) => ({ default: m.ResetPasswordPage })))
const StudentDashboard = lazy(() => import("./pages/student/StudentDashboard").then((m) => ({ default: m.StudentDashboard })))
const StudentProfile = lazy(() => import("./pages/student/StudentProfile").then((m) => ({ default: m.StudentProfile })))
const InterviewHistoryPage = lazy(() =>
  import("./pages/student/InterviewHistoryPage").then((m) => ({ default: m.InterviewHistoryPage })),
)
const HrInterviewPage = lazy(() => import("./pages/student/InterviewSetupPage").then((m) => ({ default: m.HrInterviewPage })))
const TechnicalInterviewPage = lazy(() =>
  import("./pages/student/InterviewSetupPage").then((m) => ({ default: m.TechnicalInterviewPage })),
)
const InterviewSessionPage = lazy(() =>
  import("./pages/student/InterviewSessionPage").then((m) => ({ default: m.InterviewSessionPage })),
)
const ResumePage = lazy(() => import("./pages/student/ResumePage").then((m) => ({ default: m.ResumePage })))
const CodingPage = lazy(() => import("./pages/student/CodingPage").then((m) => ({ default: m.CodingPage })))
const RoadmapPage = lazy(() => import("./pages/student/RoadmapPage").then((m) => ({ default: m.RoadmapPage })))
const CompaniesPage = lazy(() => import("./pages/student/CompaniesPage").then((m) => ({ default: m.CompaniesPage })))
const CompanyDetailPage = lazy(() =>
  import("./pages/student/CompanyDetailPage").then((m) => ({ default: m.CompanyDetailPage })),
)
const TpoDashboard = lazy(() => import("./pages/tpo/TpoDashboard").then((m) => ({ default: m.TpoDashboard })))
const TpoProfile = lazy(() => import("./pages/tpo/TpoProfile").then((m) => ({ default: m.TpoProfile })))
const TpoStudentPage = lazy(() => import("./pages/tpo/TpoStudentPage").then((m) => ({ default: m.TpoStudentPage })))

function Page({ children }: { children: ReactNode }) {
  return (
    <Suspense
      fallback={
        <p className="flex items-center gap-2 text-sm text-muted" role="status">
          <Spinner />
          Loading…
        </p>
      }
    >
      {children}
    </Suspense>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<GuestOnly><LoginPage /></GuestOnly>} />
          <Route path="/register" element={<GuestOnly><RegisterPage /></GuestOnly>} />
          <Route
            path="/forgot-password"
            element={
              <GuestOnly>
                <Suspense fallback={<StatusScreen label="Loading…" />}>
                  <ForgotPasswordPage />
                </Suspense>
              </GuestOnly>
            }
          />
          <Route
            path="/reset-password"
            element={
              <Suspense fallback={<StatusScreen label="Loading…" />}>
                <ResetPasswordPage />
              </Suspense>
            }
          />
          <Route
            path="/app"
            element={
              <RequireAuth role="student">
                <StudentLayout />
              </RequireAuth>
            }
          >
            <Route index element={<Page><StudentDashboard /></Page>} />
            <Route path="resume" element={<Page><ResumePage /></Page>} />
            <Route path="interview/hr" element={<Page><HrInterviewPage /></Page>} />
            <Route path="interview/technical" element={<Page><TechnicalInterviewPage /></Page>} />
            <Route path="interview/history" element={<Page><InterviewHistoryPage /></Page>} />
            <Route path="interview/:sessionId" element={<Page><InterviewSessionPage /></Page>} />
            <Route path="coding" element={<Page><CodingPage /></Page>} />
            <Route path="companies" element={<Page><CompaniesPage /></Page>} />
            <Route path="companies/:slug" element={<Page><CompanyDetailPage /></Page>} />
            <Route path="roadmap" element={<Page><RoadmapPage /></Page>} />
            <Route path="profile" element={<Page><StudentProfile /></Page>} />
          </Route>
          <Route
            path="/tpo"
            element={
              <RequireAuth role="tpo">
                <TpoLayout />
              </RequireAuth>
            }
          >
            <Route index element={<Page><TpoDashboard /></Page>} />
            <Route path="students/:studentId" element={<Page><TpoStudentPage /></Page>} />
            <Route path="profile" element={<Page><TpoProfile /></Page>} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

function NotFound() {
  return (
    <div className="grid min-h-screen place-items-center bg-paper px-6 text-center">
      <div>
        <p className="text-xs font-semibold tracking-wider text-muted uppercase">404</p>
        <h1 className="mt-1 font-serif text-4xl">Page not found</h1>
        <p className="mt-2 text-sm text-muted">The link may be old, or the page has moved.</p>
        <Link to="/" className="mt-5 inline-block rounded-md bg-navy px-4 py-2.5 text-sm font-semibold text-foam">
          Back home
        </Link>
      </div>
    </div>
  )
}
