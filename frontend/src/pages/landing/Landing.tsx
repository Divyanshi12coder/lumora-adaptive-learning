import { useEffect } from "react";
import { PublicNav } from "@/components/layout/PublicNav";
import { Footer } from "@/components/layout/Footer";
import { Hero } from "./Hero";
import { HowItWorks, Problem } from "./Story";
import { AdaptSlider, TutorDemo } from "./Demos";
import { AccessibilitySection, AnalyticsSection, CTA, Features, Journey, MLSection, RagSection, Responsible, Technology } from "./Sections";

export default function Landing() {
  useEffect(() => {
    document.title = "Lumora - Adaptive intelligence for every learner";
  }, []);
  return (
    <div className="min-h-screen bg-cream-50">
      <a href="#content" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-full focus:bg-maroon-600 focus:px-4 focus:py-2 focus:text-cream-50">
        Skip to content
      </a>
      <PublicNav />
      <main id="content">
        <Hero />
        <Problem />
        <HowItWorks />
        <AdaptSlider />
        <TutorDemo />
        <Journey />
        <Features />
        <RagSection />
        <MLSection />
        <AnalyticsSection />
        <AccessibilitySection />
        <Responsible />
        <Technology />
        <CTA />
      </main>
      <Footer />
    </div>
  );
}
