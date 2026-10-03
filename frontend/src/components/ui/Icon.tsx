import {
  BookOpen,
  Building2,
  Calculator,
  CalendarHeart,
  Cog,
  Droplets,
  FlaskConical,
  Footprints,
  Landmark,
  Lightbulb,
  MessageCircleQuestion,
  Orbit,
  PieChart,
  Puzzle,
  Scroll,
  Search,
  Shapes,
  Sparkles,
  Sprout,
  Trophy,
  Triangle,
  X,
  type LucideIcon,
} from "lucide-react";

const MAP: Record<string, LucideIcon> = {
  calculator: Calculator,
  flask: FlaskConical,
  "book-open": BookOpen,
  landmark: Landmark,
  "pie-chart": PieChart,
  x: X,
  shapes: Shapes,
  sprout: Sprout,
  droplets: Droplets,
  orbit: Orbit,
  lightbulb: Lightbulb,
  search: Search,
  scroll: Scroll,
  pyramid: Triangle,
  building: Building2,
  cog: Cog,
  footprints: Footprints,
  "message-circle-question": MessageCircleQuestion,
  puzzle: Puzzle,
  "calendar-heart": CalendarHeart,
  trophy: Trophy,
};

export function Icon({ name, size = 20, className }: { name: string; size?: number; className?: string }) {
  const C = MAP[name] ?? Sparkles;
  return <C size={size} className={className} aria-hidden="true" />;
}
