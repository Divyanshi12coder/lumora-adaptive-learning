import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { AlertCircle, Eye, EyeOff, Loader2, Sparkles } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { ApiError } from "@/lib/api";
import { Logo } from "@/components/brand/Logo";
import { DiviAvatar } from "@/components/brand/DiviAvatar";
import { Blob, FloatingShapes } from "@/components/illustrations/Decor";

const DEMO = { email: "demo@lumora.app", password: "LumoraDemo2026!" };

function AuthLayout({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <div className="grid min-h-screen bg-cream-50 lg:grid-cols-2">
      <div className="relative hidden overflow-hidden bg-cream-100 lg:flex lg:flex-col lg:items-center lg:justify-center">
        <FloatingShapes />
        <Blob className="absolute h-[80%] w-[80%]" color="#FFF2CC" />
        <div className="relative z-10 flex max-w-sm flex-col items-center text-center">
          <DiviAvatar size={150} mood="happy" />
          <p className="mt-6 font-display text-3xl font-semibold text-maroon-800">“I'll learn how you learn.”</p>
          <p className="mt-3 text-cocoa-soft">Divi adapts every explanation, hint and quiz to you - at your pace, in your way.</p>
        </div>
      </div>
      <div className="flex flex-col px-5 py-8 sm:px-10">
        <Link to="/" aria-label="Back to Lumora home" className="self-start">
          <Logo size={40} />
        </Link>
        <motion.div className="mx-auto my-auto w-full max-w-md py-10" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="h-display text-3xl sm:text-4xl">{title}</h1>
          <p className="mt-2 text-cocoa-soft">{subtitle}</p>
          <div className="mt-8">{children}</div>
        </motion.div>
      </div>
    </div>
  );
}

function FormError({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <div role="alert" className="flex items-start gap-2 rounded-2xl border border-maroon-200 bg-maroon-50 px-4 py-3 text-sm text-maroon-800">
      <AlertCircle size={18} className="mt-0.5 shrink-0" aria-hidden /> {message}
    </div>
  );
}

function PasswordField({ id, value, onChange, autoComplete, describedBy }: { id: string; value: string; onChange: (v: string) => void; autoComplete: string; describedBy?: string }) {
  const [show, setShow] = useState(false);
  return (
    <div className="relative">
      <input
        id={id}
        type={show ? "text" : "password"}
        className="input pr-14"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        autoComplete={autoComplete}
        required
        minLength={8}
        maxLength={72}
        aria-describedby={describedBy}
      />
      <button type="button" className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full p-2 text-sand-500 hover:text-maroon-700" onClick={() => setShow((s) => !s)} aria-label={show ? "Hide password" : "Show password"}>
        {show ? <EyeOff size={20} aria-hidden /> : <Eye size={20} aria-hidden />}
      </button>
    </div>
  );
}

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => { document.title = "Sign in · Lumora"; }, []);

  const submit = async (e: FormEvent, creds = { email, password }) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(creds.email, creds.password);
      navigate((location.state as { from?: string } | null)?.from ?? "/app", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthLayout title="Welcome back!" subtitle="Sign in to keep learning with Divi.">
      <form onSubmit={submit} className="space-y-5" noValidate={false}>
        <FormError message={error} />
        <div>
          <label htmlFor="email" className="mb-1.5 block font-medium">Email</label>
          <input id="email" type="email" className="input" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required />
        </div>
        <div>
          <label htmlFor="password" className="mb-1.5 block font-medium">Password</label>
          <PasswordField id="password" value={password} onChange={setPassword} autoComplete="current-password" />
        </div>
        <button type="submit" className="btn-primary w-full py-3 text-base" disabled={busy}>
          {busy && <Loader2 className="animate-spin" size={18} aria-hidden />} Sign in
        </button>
      </form>
      <div className="mt-6 rounded-2xl border border-cream-300 bg-cream-100 p-4 text-sm">
        <p className="flex items-center gap-2 font-medium text-maroon-800"><Sparkles size={16} aria-hidden /> Just looking around?</p>
        <p className="mt-1 text-cocoa-soft">Try the demo learner account (simulated practice history, available when the server was seeded with it).</p>
        <button className="btn-secondary mt-3 w-full" disabled={busy} onClick={(e) => { setEmail(DEMO.email); setPassword(DEMO.password); void submit(e, DEMO); }}>
          Explore the demo account
        </button>
      </div>
      <p className="mt-6 text-center text-sm text-cocoa-soft">
        New to Lumora? <Link to="/signup" className="font-semibold text-maroon-700 underline-offset-4 hover:underline">Create an account</Link>
      </p>
    </AuthLayout>
  );
}

export function SignupPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => { document.title = "Create account · Lumora"; }, []);

  const weak = password.length > 0 && (password.length < 8 || /^[A-Za-z]+$/.test(password) || /^\d+$/.test(password));

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    if (weak) {
      setError("Your password needs at least 8 characters with a mix of letters and numbers.");
      return;
    }
    setBusy(true);
    try {
      await register(email, password, name);
      navigate("/app", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthLayout title="Let's get started" subtitle="Create your free Lumora account. We only ask for what we need.">
      <form onSubmit={submit} className="space-y-5">
        <FormError message={error} />
        <div>
          <label htmlFor="name" className="mb-1.5 block font-medium">What should Divi call you?</label>
          <input id="name" className="input" value={name} onChange={(e) => setName(e.target.value)} maxLength={40} required autoComplete="nickname" aria-describedby="name-help" />
          <p id="name-help" className="mt-1 text-xs text-sand-500">A first name or nickname is perfect.</p>
        </div>
        <div>
          <label htmlFor="email" className="mb-1.5 block font-medium">Email <span className="font-normal text-sand-500">(a grown-up's is fine)</span></label>
          <input id="email" type="email" className="input" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required />
        </div>
        <div>
          <label htmlFor="password" className="mb-1.5 block font-medium">Password</label>
          <PasswordField id="password" value={password} onChange={setPassword} autoComplete="new-password" describedBy="pw-help" />
          <p id="pw-help" className={weak ? "mt-1 text-xs text-maroon-700" : "mt-1 text-xs text-sand-500"}>
            At least 8 characters, with letters and numbers.
          </p>
        </div>
        <button type="submit" className="btn-primary w-full py-3 text-base" disabled={busy}>
          {busy && <Loader2 className="animate-spin" size={18} aria-hidden />} Create my account
        </button>
        <p className="text-xs text-sand-500">
          Lumora adapts to learning preferences. It is not a medical tool and never diagnoses conditions. We don't collect birthdays, schools or locations.
        </p>
      </form>
      <p className="mt-6 text-center text-sm text-cocoa-soft">
        Already have an account? <Link to="/login" className="font-semibold text-maroon-700 underline-offset-4 hover:underline">Sign in</Link>
      </p>
    </AuthLayout>
  );
}
