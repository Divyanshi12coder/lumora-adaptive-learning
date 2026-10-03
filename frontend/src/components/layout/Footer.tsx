import { Link } from "react-router-dom";
import { Github, ShieldCheck } from "lucide-react";
import { Logo } from "../brand/Logo";
import { apiBase } from "@/lib/api";

export function Footer() {
  const docs = `${apiBase || ""}/docs`;
  return (
    <footer className="border-t border-cream-200 bg-cream-100/70">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 py-12 sm:px-6 md:grid-cols-[1.4fr_1fr_1fr]">
        <div>
          <Logo size={40} tagline />
          <p className="mt-4 max-w-sm text-sm text-cocoa-soft">
            Adaptive intelligence for every learner. Lumora changes <em>how</em> it teaches based on how each child learns.
          </p>
          <p className="mt-4 flex max-w-sm items-start gap-2 text-xs text-sand-500">
            <ShieldCheck size={16} className="mt-0.5 shrink-0 text-maroon-500" aria-hidden />
            Lumora supports learning preferences and accessibility needs. It is not a medical tool and does not diagnose or treat ADHD,
            dyslexia, autism or any other condition.
          </p>
        </div>
        <div>
          <h2 className="text-sm font-semibold text-maroon-700">Product</h2>
          <ul className="mt-3 space-y-2 text-sm">
            <li><a className="hover:text-maroon-700" href="/#how">How it works</a></li>
            <li><a className="hover:text-maroon-700" href="/#features">Features</a></li>
            <li><Link className="hover:text-maroon-700" to="/signup">Create an account</Link></li>
          </ul>
        </div>
        <div>
          <h2 className="text-sm font-semibold text-maroon-700">For developers</h2>
          <ul className="mt-3 space-y-2 text-sm">
            <li><a className="hover:text-maroon-700" href={docs} target="_blank" rel="noreferrer">API documentation</a></li>
            <li>
              <a className="inline-flex items-center gap-1.5 hover:text-maroon-700" href="https://github.com/Divyanshi12coder/lumora" target="_blank" rel="noreferrer">
                <Github size={15} aria-hidden /> Source on GitHub
              </a>
            </li>
          </ul>
        </div>
      </div>
      <div className="border-t border-cream-200 py-5 text-center text-xs text-sand-500">
        © {new Date().getFullYear()} Lumora · Designed &amp; built by Divyanshi
      </div>
    </footer>
  );
}
