import { lazy, Suspense } from "react";
import { Link, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { GuestOnly, RequireAuth } from "./components/layout/Guards";
import { DiviAvatar } from "./components/brand/DiviAvatar";
import { PageSkeleton } from "./components/ui";
import Landing from "./pages/landing/Landing";
import { LoginPage, SignupPage } from "./pages/auth/AuthPages";

const Dashboard = lazy(() => import("./pages/app/Dashboard"));
const Explore = lazy(() => import("./pages/app/Explore"));
const Lesson = lazy(() => import("./pages/app/Lesson"));
const Quiz = lazy(() => import("./pages/app/Quiz"));
const Tutor = lazy(() => import("./pages/app/Tutor"));
const Insights = lazy(() => import("./pages/app/Insights"));
const Library = lazy(() => import("./pages/app/Library"));
const Settings = lazy(() => import("./pages/app/Settings"));

function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-cream-50 px-6 text-center">
      <DiviAvatar size={110} mood="thinking" />
      <h1 className="h-display text-3xl">Hmm, this page wandered off.</h1>
      <p className="text-cocoa-soft">Let's head back somewhere familiar.</p>
      <Link to="/" className="btn-primary">Go home</Link>
    </div>
  );
}

const page = (el: JSX.Element) => <Suspense fallback={<PageSkeleton />}>{el}</Suspense>;

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<GuestOnly><LoginPage /></GuestOnly>} />
      <Route path="/signup" element={<GuestOnly><SignupPage /></GuestOnly>} />
      <Route path="/app" element={<RequireAuth><AppShell /></RequireAuth>}>
        <Route index element={page(<Dashboard />)} />
        <Route path="explore" element={page(<Explore />)} />
        <Route path="lesson/:id" element={page(<Lesson />)} />
        <Route path="quiz/:topicId" element={page(<Quiz />)} />
        <Route path="tutor" element={page(<Tutor />)} />
        <Route path="insights" element={page(<Insights />)} />
        <Route path="library" element={page(<Library />)} />
        <Route path="settings" element={page(<Settings />)} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
